from fastapi import FastAPI
from api.prompt_router_API import router as prompt_router
from api.rag_router_API import router as rag_router
from api.auth_API import router as auth_router

from core.startup import startup_event

from dotenv import load_dotenv
load_dotenv()

app = FastAPI(
    title="Gerador de Conteúdo AI",
    description="Backend para Processamento de LLM e RAG",
    version="1.0.0"
)

app.add_event_handler("startup", startup_event)

app.include_router(auth_router)
app.include_router(rag_router)
app.include_router(prompt_router)

@app.get("/health")
def health_check():
    """Endpoint leve para verificação de status global"""
    return {"status": "ok", "service": "JACN AI Portal API"}
