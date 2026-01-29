import os
import glob
import logging
from typing import Union
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
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

# Dicionário de vectorstores por inquilino: {tenant_id: vectorstore}
_tenant_stores = {}
# Vectorstore global para documentos compartilhados
_global_store = None


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
    Inicializa ou recarrega o FAISS para um usuário (data/uploads/{tenant_id}/{username}) 
    ou globalmente (data/docs).
    """
    global _tenant_stores, _global_store
    
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
        if store_key in _tenant_stores and not force_reload:
            return
    else:
        if _global_store is not None and not force_reload:
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
            _tenant_stores[store_key] = None
        else:
            _global_store = None
        return

    # 6. Processamento (Chunks + Embeddings + FAISS)
    try:
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
        chunks = splitter.split_documents(documents)
        chunks = [c for c in chunks if c.page_content and c.page_content.strip()]

        if not chunks:
            logging.warning(f"Nenhum chunk gerado para {store_key}")
            return

        logging.info(f"Gerando embeddings para {len(chunks)} chunks ({store_key})...")
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        embeddings = OllamaEmbeddings(model="nomic-embed-text", base_url=base_url)
        vstore = FAISS.from_documents(documents=chunks, embedding=embeddings)
        
        if t_id:
            _tenant_stores[store_key] = vstore
        else:
            _global_store = vstore
            
        logging.info(f"FAISS inicializado com sucesso para {store_key}.")
        
    except Exception as e:
        logging.error(f"Erro crítico no processamento de FAISS ({store_key}): {e}")
        if t_id:
            _tenant_stores[store_key] = None
        else:
            _global_store = None


def similarity_search(query: str, tenant_id: str = None, username: str = None, k: int = 4, include_global: bool = False):
    """
    Busca por similaridade combinando a base do usuário e, opcionalmente, a global.
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
        t_store = _tenant_stores.get(store_key)
        
        # Se não encontrou a store (ou é None), tenta forçar um recarregamento
        if not t_store:
            logging.info(f"Store {store_key} vazia ou não encontrada. Forçando reload na busca.")
            init_search(tenant_id=tid_str, username=usr_str, force_reload=True)
            t_store = _tenant_stores.get(store_key)

        if t_store:
            try:
                t_res = t_store.similarity_search_with_score(query, k=k)
                for doc, score in t_res:
                    final_results.append({
                        "content": doc.page_content,
                        "score": float(score),
                        "source": doc.metadata.get("source", "desconhecido"),
                        "page": doc.metadata.get("page", 0)
                    })
            except Exception as e:
                logging.error(f"Erro na busca do usuário ({usr_str} @ {tid_str}): {e}")

    # 2. Busca na base global (opcional)
    if include_global:
        init_search(tenant_id=None) # Garante global
        if _global_store:
            try:
                g_res = _global_store.similarity_search_with_score(query, k=k)
                for doc, score in g_res:
                    final_results.append({
                        "content": doc.page_content,
                        "score": float(score),
                        "source": doc.metadata.get("source", "desconhecido"),
                        "page": doc.metadata.get("page", 0)
                    })
            except Exception as e:
                logging.error(f"Erro na busca global: {e}")

    # Ordena por score (menor distância primeiro) e limita a k
    final_results.sort(key=lambda x: x["score"])
    return final_results[:k]
