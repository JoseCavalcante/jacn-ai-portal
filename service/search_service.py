import os
import glob
import logging
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

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


def init_search(tenant_id: str = None, username: str = None, force_reload=False):
    """
    Inicializa ou recarrega o FAISS para um usuário específico dentro de um inquilino.
    Se tenant_id for None, inicializa a base global (data/docs).
    Se tenant_id e username forem str/int, inicializa a base do usuário (data/uploads/{tenant_id}/{username}).
    """
    global _tenant_stores, _global_store
    
    # Normaliza tenant_id e username para string
    tid_str = str(tenant_id) if tenant_id is not None else None
    usr_str = str(username) if username is not None else None
    
    # Chave única para o índice do usuário: tenant_id + username
    if tid_str and usr_str:
        store_key = f"{tid_str}_{usr_str}"
        # Tenta encontrar pasta ID_Nome ou apenas ID
        pattern = os.path.join("data", "uploads", f"{tid_str}_*")
        matching = glob.glob(pattern)
        tenant_base = matching[0] if matching else os.path.join("data", "uploads", tid_str)
        docs_paths = [os.path.join(tenant_base, usr_str)]
    elif tid_str:
        store_key = tid_str
        pattern = os.path.join("data", "uploads", f"{tid_str}_*")
        matching = glob.glob(pattern)
        tenant_base = matching[0] if matching else os.path.join("data", "uploads", tid_str)
        docs_paths = [tenant_base]
    else:
        store_key = "global"
        docs_paths = ["data/docs"]

    if tid_str:
        if store_key in _tenant_stores and not force_reload:
            return
    else:
        if _global_store is not None and not force_reload:
            return

    logging.info(f"--- INIT SEARCH DEBUG ---")
    logging.info(f"Store Key: {store_key}")
    logging.info(f"Docs Paths: {docs_paths}")

    documents = []
    for path in docs_paths:
        if not os.path.exists(path):
            logging.info(f"Path não existe, criando: {path}")
            os.makedirs(path, exist_ok=True)
            continue
            
        files = os.listdir(path)
        logging.info(f"Arquivos em {path}: {files}")
        
        for file in files:
            if file.lower().endswith(".pdf"):
                caminho_pdf = os.path.join(path, file)
                caminho_pdf = garantir_pdf_textual(caminho_pdf)
                
                try:
                    loader = PyPDFLoader(caminho_pdf)
                    docs = loader.load()
                    if docs:
                        documents.extend(docs)
                        logging.info(f"PDF carregado: {file} ({len(docs)} páginas)")
                    else:
                        logging.warning(f"PDF sem texto válido: {file}")
                except Exception as e:
                    logging.warning(f"Erro ao ler {file}: {e}")

    if not documents:
        logging.info(f"Nenhum documento encontrado para {store_key}")
        if tid_str:
            _tenant_stores[store_key] = None
        else:
            _global_store = None
        return

    # Divide em chunks
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    chunks = splitter.split_documents(documents)
    chunks = [c for c in chunks if c.page_content and c.page_content.strip()]

    if not chunks:
        return

    # Cria embeddings e FAISS
    try:
        logging.info(f"Gerando embeddings para {store_key}...")
        embeddings = OllamaEmbeddings(model="nomic-embed-text")
        vstore = FAISS.from_documents(documents=chunks, embedding=embeddings)
        
        if tid_str:
            _tenant_stores[store_key] = vstore
        else:
            _global_store = vstore
        logging.info(f"FAISS {store_key} inicializado com {len(chunks)} chunks.")
    except Exception as e:
        logging.error(f"Erro ao inicializar FAISS for {store_key}: {e}")
        if tid_str:
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
