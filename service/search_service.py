import os
import glob
import logging
from typing import Union
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_classic.retrievers.ensemble import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from core.utils import get_tenant_path

# OCR opcional
try:
    import ocrmypdf
except ImportError:
    ocrmypdf = None
    logging.info("ocrmypdf não instalado. PDFs escaneados não serão processados automaticamente.")

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Dicionário de retrievers por inquilino: {tenant_id: ensemble_retriever}
_tenant_retrievers = {}
# Retriever global para documentos compartilhados
_global_retriever = None


def garantir_pdf_textual(caminho_pdf: str) -> str:
    """
    Se o PDF não tiver texto selecionável, tenta aplicar OCR (se disponível).
    Retorna o caminho para o PDF textual.
    """
    from pypdf import PdfReader

    try:
        reader = PdfReader(caminho_pdf)
        tem_texto = any(p.extract_text() and p.extract_text().strip() for p in reader.pages)
    except Exception as e:
        logging.warning(f"Não foi possível ler {caminho_pdf}: {e}")
        return caminho_pdf

    if tem_texto or ocrmypdf is None:
        return caminho_pdf

    pdf_ocr = caminho_pdf.replace(".pdf", "_ocr.pdf")
    try:
        logging.info(f"Aplicando OCR em {caminho_pdf}")
        ocrmypdf.ocr(caminho_pdf, pdf_ocr, language="por", force_ocr=True)
        return pdf_ocr
    except Exception as e:
        logging.warning(f"OCR falhou em {caminho_pdf}: {e}")
        return caminho_pdf


def init_search(tenant_id: Union[str, int] = None, username: str = None, force_reload=False):
    """
    Inicializa ou recarrega o Sistema Híbrido (BM25 + FAISS) para um usuário.
    """
    global _tenant_retrievers, _global_retriever
    
    # 1. Normalização de Entradas
    t_id = str(tenant_id) if tenant_id is not None else None
    u_name = str(username) if username is not None else None
    
    # 2. Resolução de Caminhos e Chaves
    base_dir = os.path.abspath(os.getcwd())
    data_dir = os.path.join(base_dir, "data")
    
    if t_id and u_name:
        store_key = f"{t_id}_{u_name}"
        tenant_base = get_tenant_path(t_id)
        docs_paths = [os.path.join(tenant_base, u_name)]
    elif t_id:
        store_key = t_id
        tenant_base = get_tenant_path(t_id)
        docs_paths = [tenant_base]
    else:
        store_key = "global"
        docs_paths = [os.path.join(data_dir, "docs")]

    # 3. Cache Check
    if t_id:
        if store_key in _tenant_retrievers and not force_reload:
            return
    else:
        if _global_retriever is not None and not force_reload:
            return

    # 4. Carregamento de Documentos
    documents = []
    for path in docs_paths:
        if not os.path.exists(path):
            logging.info(f"Diretório não existe: {path}")
            continue
            
        for file in os.listdir(path):
            if file.lower().endswith(".pdf") and not file.lower().endswith("_ocr.pdf"):
                caminho_pdf = os.path.join(path, file)
                # Tenta garantir que o PDF seja textual
                caminho_final = garantir_pdf_textual(caminho_pdf)
                
                try:
                    loader = PyPDFLoader(caminho_final)
                    docs = loader.load()
                    if docs:
                        documents.extend(docs)
                        logging.info(f"Carregado: {file} ({len(docs)} pgs)")
                except Exception as e:
                    logging.warning(f"Erro ao ler {file}: {e}")

    # 5. Fallback se não houver documentos
    if not documents:
        logging.info(f"Nenhum PDF válido encontrado para {store_key}")
        if t_id:
            _tenant_retrievers[store_key] = None
        else:
            _global_retriever = None
        return

    # 6. Processamento Híbrido (BM25 + FAISS)
    try:
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
        chunks = splitter.split_documents(documents)
        chunks = [c for c in chunks if c.page_content and c.page_content.strip()]

        if not chunks:
            logging.warning(f"Nenhum chunk gerado para {store_key}")
            return

        logging.info(f"Gerando índices Híbridos para {len(chunks)} chunks ({store_key})...")
        
        # --- A. Keywords (Sparse) ---
        bm25_retriever = BM25Retriever.from_documents(chunks)
        # O valor de k será sobrescrito na query, mas definimos padrão
        bm25_retriever.k = 4
        
        # --- B. Semântico (Dense) ---
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        embeddings = OllamaEmbeddings(model="nomic-embed-text", base_url=base_url)
        vstore = FAISS.from_documents(documents=chunks, embedding=embeddings)
        faiss_retriever = vstore.as_retriever(search_kwargs={"k": 4})
        
        # --- C. Ensemble (Híbrido) ---
        # Pesando 40% Keywords + 60% Semântico
        ensemble_retriever = EnsembleRetriever(
            retrievers=[bm25_retriever, faiss_retriever],
            weights=[0.4, 0.6]
        )
        
        if t_id:
            _tenant_retrievers[store_key] = ensemble_retriever
        else:
            _global_retriever = ensemble_retriever
            
        logging.info(f"Sistema Híbrido (Ensemble) inicializado com sucesso para {store_key}.")
        
    except Exception as e:
        logging.error(f"Erro crítico no processamento Híbrido ({store_key}): {e}")
        if t_id:
            _tenant_retrievers[store_key] = None
        else:
            _global_retriever = None


def similarity_search(query: str, tenant_id: str = None, username: str = None, k: int = 4, include_global: bool = False):
    """
    Busca Híbrida combinando BM25 + FAISS.
    """
    final_results = []
    
    # Normaliza para string
    tid_str = str(tenant_id) if tenant_id is not None else None
    usr_str = str(username) if username is not None else None
    
    # 1. Busca na base do usuário
    if tid_str and usr_str:
        store_key = f"{tid_str}_{usr_str}"
        # Garante que a base do usuário esteja inicializada
        init_search(tenant_id=tid_str, username=usr_str)
        t_retriever = _tenant_retrievers.get(store_key)
        
        # Se não encontrou a store (ou é None), tenta forçar um recarregamento
        if not t_retriever:
            logging.info(f"Retriever {store_key} vazio ou não encontrado. Forçando reload na busca.")
            init_search(tenant_id=tid_str, username=usr_str, force_reload=True)
            t_retriever = _tenant_retrievers.get(store_key)

        if t_retriever:
            try:
                # Ajusta o K dinamicamente para os retrievers internos
                # Nota: EnsembleRetriever não expõe fácil ajuste de K dinâmico para os filhos, 
                # mas podemos tentar se o objeto permitir, ou apenas confiar no padrão.
                # O invoke do Ensemble usa a config dos retrievers filhos.
                # Para simplificar, assumimos o K configurado na init ou padrão.
                
                # Mas para garantir, podemos tentar setar k nos filhos se acessíveis:
                for r in t_retriever.retrievers:
                    if hasattr(r, 'k'): r.k = k
                    if hasattr(r, 'search_kwargs'): r.search_kwargs['k'] = k
                
                docs = t_retriever.invoke(query)
                
                # Ensemble retorna Docs ordenados por Rank, sem score explícito no objeto Doc padrão.
                # Como nosso sistema espera 'score' (distância), vamos simular um score baixo (bom)
                # pois o Ensemble já garantiu a relevância.
                for i, doc in enumerate(docs):
                    # Simulando score: 0.1 para o primeiro, 0.11 para o segundo... 
                    # apenas para manter ordem se algo reordenar por score
                    dummy_score = 0.1 + (i * 0.01)
                    
                    final_results.append({
                        "content": doc.page_content,
                        "score": dummy_score,
                        "source": doc.metadata.get("source", "desconhecido"),
                        "page": doc.metadata.get("page", 0)
                    })
            except Exception as e:
                logging.error(f"Erro na busca do usuário ({usr_str} @ {tid_str}): {e}")

    # 2. Busca na base global (opcional)
    if include_global:
        init_search(tenant_id=None) # Garante global
        if _global_retriever:
            try:
                # Ajusta K
                for r in _global_retriever.retrievers:
                    if hasattr(r, 'k'): r.k = k
                    if hasattr(r, 'search_kwargs'): r.search_kwargs['k'] = k

                g_docs = _global_retriever.invoke(query)
                for i, doc in enumerate(g_docs):
                    dummy_score = 0.1 + (i * 0.01)
                    final_results.append({
                        "content": doc.page_content,
                        "score": dummy_score,
                        "source": doc.metadata.get("source", "desconhecido"),
                        "page": doc.metadata.get("page", 0)
                    })
            except Exception as e:
                logging.error(f"Erro na busca global: {e}")

    # Como o Ensemble já ordena por relevância (weighted rank), a lista `final_results` 
    # já deve estar na ordem correta vinda do invoke().
    # Contudo, se misturarmos Global + Local, a ordem pode bagunçar.
    # Vamos manter a ordem de inserção (Local primeiro, depois Global).
    
    return final_results[:k]
