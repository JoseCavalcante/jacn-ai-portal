import logging
from service.search_service import init_search

logger = logging.getLogger(__name__)

def startup_event():
    """
    Hook de inicialização executado pelo FastAPI no boot.
    Configura o FAISS e prepara a base de busca.
    """
    logger.info("Inicializando FAISS...")
    try:
        init_search()
        logger.info("FAISS inicializado com sucesso (se houver PDFs válidos).")
    except Exception as e:
        logger.error(f"Falha crítica na inicialização do FAISS: {e}")
