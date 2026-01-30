from fastapi import APIRouter, HTTPException, status, UploadFile, File
import json
from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import List
import logging
import os
import shutil

from service.search_service import similarity_search, init_search
from service.rag_chain_service import ask_rag
from service.auth_service import validar_token
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from db.database import SessionLocal
from db.models import Tenant, ChatMessage
from core.utils import slugify, get_tenant_path
import glob
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def parse_date(val):
    if not val:
        return datetime.utcnow()
    if isinstance(val, datetime):
        return val
    try:
        if isinstance(val, str):
            val = val.replace('T', ' ').replace('Z', '')
            if '.' in val:
                return datetime.strptime(val, '%Y-%m-%d %H:%M:%S.%f')
            return datetime.strptime(val, '%Y-%m-%d %H:%M:%S')
    except Exception as e:
        logger.warning(f"Falha ao parsear data '{val}': {e}")
    return datetime.utcnow()

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/rag", tags=["RAG Hub"])
security = HTTPBearer()

def get_current_user_data(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = validar_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {
        "username": payload.get("sub"),
        "tenant_id": payload.get("tenant_id"),
        "role": payload.get("role")
    }

# =========================
# MODELS
# =========================

class SearchRequest(BaseModel):
    question: str = Field(..., min_length=1, description="Pergunta a ser buscada na base")
    k: int = Field(default=4, ge=1, le=10, description="Número de documentos a retornar")

class AskRequest(SearchRequest):
    score_threshold: float = Field(
        default=1.5, ge=0.0, le=2.0,
        description="Threshold de score para filtrar documentos (quanto menor, melhor, pois FAISS retorna distância)"
    )

class FeedbackRequest(BaseModel):
    message_id: int
    value: int = Field(..., ge=-1, le=1) # -1: negative, 0: none, 1: positive

class SearchResult(BaseModel):
    title: str = Field(default="Sem título", description="Resumo ou título do fragmento")
    content: str
    score: float
    source: str = Field(default="desconhecido", description="Nome do arquivo de origem")
    page: int = Field(default=0, description="Número da página original")

def extrair_titulo_contextual(texto: str) -> str:
    """Extrai um título curto do início do fragmento."""
    limpo = " ".join(texto.split()).strip()
    if len(limpo) <= 60:
        return limpo
    corte = limpo[:60].rsplit(' ', 1)[0]
    return corte + "..."

class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]

class AskResponse(BaseModel):
    message_id: int
    question: str
    answer: str
    sources: List[SearchResult]


# Removed local get_tenant_dir in favor of core.utils.get_tenant_path

# =========================
# ENDPOINTS
# =========================

@router.get("/health_check_custom")
def health_custom():
    return {"status": "I AM LIVE AND RELOADED"}

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    user_data: dict = Depends(get_current_user_data)
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Apenas arquivos PDF são permitidos.")
    
    tenant_id = user_data.get("tenant_id")
    username = user_data.get("username")
    
    if not tenant_id or not username:
        raise HTTPException(status_code=401, detail="Usuário ou Organização não identificados no token.")

    db = SessionLocal()
    try:
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            raise HTTPException(status_code=404, detail="Organização não encontrada.")
            
        # Verificar limites
        if tenant.current_document_count >= tenant.max_documents:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail=f"Limite de documentos atingido ({tenant.max_documents}). Faça upgrade do seu plano."
            )
            
        # Pasta privada do usuário dentro do inquilino
        tid_str = str(tenant_id)
        usr_str = str(username)
        tenant_upload_dir = os.path.join(get_tenant_path(tenant_id, tenant.name), usr_str)
        
        logger.info(f"--- UPLOAD DEBUG ---")
        logger.info(f"User Data: {user_data}")
        logger.info(f"Computed Dir: {tenant_upload_dir}")
        
        os.makedirs(tenant_upload_dir, exist_ok=True)
        
        upload_path = os.path.join(tenant_upload_dir, file.filename)
        logger.info(f"Saving to: {upload_path}")
        
        with open(upload_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Atualizar contagem no banco
        tenant.current_document_count += 1
        db.commit()
        
        # Força o recarregamento da base de busca privada do usuário
        init_search(tenant_id=tid_str, username=usr_str, force_reload=True)
        
        return {"status": "sucesso", "mensagem": f"Arquivo {file.filename} indexado com sucesso!"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Erro no upload: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar arquivo: {e}")
    finally:
        db.close()

@router.get("/search", response_model=SearchResponse)
def search(msg: str, k: int, user_data: dict = Depends(get_current_user_data)):
    try:
        tenant_id = user_data["tenant_id"]
        username = user_data["username"]
        # include_global defaults to False, ensuring strict isolation
        results_raw = similarity_search(query=msg, tenant_id=tenant_id, username=username, k=k, include_global=False)
        results = [
            SearchResult(
                title=extrair_titulo_contextual(d["content"]),
                content=d["content"].replace('\n', ' ').strip(), 
                score=d["score"],
                source=os.path.basename(d.get("source", "desconhecido")).replace("_ocr.pdf", ".pdf"),
                page=int(d.get("page", 0)) + 1
            ) 
            for d in results_raw
        ]
        return SearchResponse(query=msg, results=results)
    except Exception as e:
        logger.exception(f"Erro em /search: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao buscar documentos."
        )


@router.post("/ask_prompt", response_model=AskResponse)
def ask(payload: AskRequest, user_data: dict = Depends(get_current_user_data)):
    try:
        tenant_id = user_data["tenant_id"]
        username = user_data["username"]
        
        # Busca isolada por usuário (include_global=False por padrão)
        docs_raw = similarity_search(query=payload.question, tenant_id=tenant_id, username=username, k=payload.k, include_global=False)

        if not docs_raw:
            return AskResponse(
                message_id=-1,
                question=payload.question,
                answer="Base de conhecimento não inicializada ou sem documentos relevantes.",
                sources=[]
            )

        # Filtragem: FAISS retorna DISTÂNCIA → menor é melhor
        filtered_docs_raw = [d for d in docs_raw if d["score"] <= payload.score_threshold]

        if not filtered_docs_raw:
            return AskResponse(
                message_id=-1,
                question=payload.question,
                answer="Não encontrei essa informação nos documentos permitidos.",
                sources=[]
            )

        # Limite máximo para contexto
        MAX_DOCS = 5
        filtered_docs_raw = filtered_docs_raw[:MAX_DOCS]

        formatted_docs = []
        for d in filtered_docs_raw:
            source_name = os.path.basename(d.get("source", "desconhecido")).replace("_ocr.pdf", ".pdf")
            page_num = int(d.get("page", 0)) + 1
            # Sanitize content to remove hard line breaks that might confuse the LLM
            clean_content = d['content'].replace('\n', ' ').strip()
            formatted_docs.append(f"[[FONTE: {source_name}, PÁGINA: {page_num}]]\n{clean_content}")

        context = "\n\n---\n\n".join(formatted_docs)
        
        MAX_CONTEXT_CHARS = 4000
        if len(context) > MAX_CONTEXT_CHARS:
            context = context[:MAX_CONTEXT_CHARS]

        response = ask_rag(context=context, question=payload.question)

        # Salva no histórico de chat
        db = SessionLocal()
        try:
            new_chat = ChatMessage(
                usuario=user_data["username"],
                tenant_id=tenant_id,
                pergunta=payload.question,
                resposta=response.content if hasattr(response, 'content') else str(response),
                sources=json.dumps([{
                    "content": d["content"],
                    "source": os.path.basename(d.get("source", "desconhecido")),
                    "page": int(d.get("page", 0)) + 1
                } for d in filtered_docs_raw])
            )
            db.add(new_chat)
            db.commit()
            db.refresh(new_chat)
            msg_id = new_chat.id
        except Exception as e:
            logger.error(f"Erro ao salvar histórico de chat: {e}")
            db.rollback()
            msg_id = -1
        finally:
            db.close()

        sources = [
            SearchResult(
                title=extrair_titulo_contextual(d["content"]),
                content=d["content"], 
                score=d["score"],
                source=os.path.basename(d.get("source", "desconhecido")).replace("_ocr.pdf", ".pdf"),
                page=int(d.get("page", 0)) + 1
            ) 
            for d in filtered_docs_raw
        ]

        return AskResponse(
            message_id=msg_id,
            question=payload.question,
            answer=response if isinstance(response, str) else (response.content if hasattr(response, 'content') else str(response)),
            sources=sources
        )

    except Exception as e:
        logger.exception(f"Erro em /ask_prompt: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao processar a pergunta."
        )

@router.get("/list_files")
def list_files(user_data: dict = Depends(get_current_user_data)):
    """Lista os arquivos PDF na pasta privada do usuário."""
    tenant_id = user_data.get("tenant_id")
    username = user_data.get("username")
    
    tenant_upload_dir = os.path.join(get_tenant_path(tenant_id), str(username))
    
    if not os.path.exists(tenant_upload_dir):
        return []
    
    files = []
    for f in os.listdir(tenant_upload_dir):
        if f.lower().endswith(".pdf") and not f.lower().endswith("_ocr.pdf"):
            path = os.path.join(tenant_upload_dir, f)
            stats = os.stat(path)
            files.append({
                "name": f,
                "size": stats.st_size,
                "created_at": datetime.fromtimestamp(stats.st_ctime).isoformat()
            })
    return files

@router.delete("/delete_file")
def delete_file(filename: str, user_data: dict = Depends(get_current_user_data)):
    """Remove um documento físico e atualiza os contadores e índice."""
    tenant_id = user_data.get("tenant_id")
    username = user_data.get("username")
    
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Nome de arquivo inválido.")

    tenant_upload_dir = os.path.join(get_tenant_path(tenant_id), str(username))
    file_path = os.path.join(tenant_upload_dir, filename)
    ocr_path = file_path.replace(".pdf", "_ocr.pdf")

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Arquivo não encontrado.")

    db = SessionLocal()
    try:
        # Remover arquivos físicos
        os.remove(file_path)
        if os.path.exists(ocr_path):
            os.remove(ocr_path)

        # Atualizar banco de dados
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if tenant:
            tenant.current_document_count = max(0, tenant.current_document_count - 1)
            db.commit()

        # Recarregar índice FAISS
        init_search(tenant_id=tenant_id, username=username, force_reload=True)

        return {"status": "sucesso", "mensagem": f"Arquivo {filename} removido com sucesso."}
    except Exception as e:
        db.rollback()
        logger.error(f"Erro ao deletar arquivo: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno ao remover arquivo: {e}")
    finally:
        db.close()

@router.get("/historico")
def get_historico(user_data: dict = Depends(get_current_user_data)):
    """Retorna o histórico de chat do inquilino atual."""
    db = SessionLocal()
    try:
        tenant_id = user_data["tenant_id"]
        username = user_data["username"]
        role = user_data["role"]
        
        query = db.query(ChatMessage).filter(ChatMessage.tenant_id == tenant_id)
        if role != "admin":
            query = query.filter(ChatMessage.usuario == username)
            
        messages = query.order_by(ChatMessage.created_at.desc()).limit(100).all()
        return [
            {
                "id": m.id,
                "usuario": m.usuario,
                "pergunta": m.pergunta,
                "resposta": m.resposta,
                "sources": json.loads(m.sources) if m.sources else [],
                "feedback": m.feedback,
                "created_at": parse_date(m.created_at).isoformat()
            }
            for m in messages
        ]
    finally:
        db.close()

@router.post("/feedback")
def save_feedback(payload: FeedbackRequest, user_data: dict = Depends(get_current_user_data)):
    db = SessionLocal()
    try:
        msg = db.query(ChatMessage).filter(
            ChatMessage.id == payload.message_id,
            ChatMessage.tenant_id == user_data["tenant_id"]
        ).first()
        
        if not msg:
            raise HTTPException(status_code=404, detail="Mensagem não encontrada.")
            
        msg.feedback = payload.value
        db.commit()
        return {"status": "sucesso", "mensagem": "Feedback salvo."}
    except Exception as e:
        db.rollback()
        logger.error(f"Erro ao salvar feedback RAG: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao salvar feedback.")
    finally:
        db.close()
