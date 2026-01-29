from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from service import auth_service, llm_service, prompt_template_service
from db.database import SessionLocal
from db.models import Tenant, Prompt
from datetime import datetime, date
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)

def parse_date(val):
    if not val:
        return datetime.utcnow()
    if isinstance(val, datetime):
        return val
    try:
        # Tenta formatos comuns no SQLite/SQLAlchemy
        if isinstance(val, str):
            val = val.replace('T', ' ').replace('Z', '')
            if '.' in val:
                return datetime.strptime(val, '%Y-%m-%d %H:%M:%S.%f')
            return datetime.strptime(val, '%Y-%m-%d %H:%M:%S')
    except Exception as e:
        logger.warning(f"Falha ao parsear data '{val}': {e}")
    return datetime.utcnow()

router = APIRouter(prefix="/prompt", tags=["Prompt Hub"])
security = HTTPBearer()

def get_current_user_data(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = auth_service.validar_token(token)
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

class FeedbackRequest(BaseModel):
    prompt_id: int
    value: int = Field(..., ge=-1, le=1)

@router.get("/")
async def raiz():
    return "Gerador de conteúdo via LLM API rodando!"

@router.post("/gerar_conteudo")
def gerar_prompt(tema: str, user_data: dict = Depends(get_current_user_data)):
    """
    Gera um conteúdo profissional via LLM.
    Requer token JWT válido no header 'Authorization'.
    """
    username = user_data["username"]
    tenant_id = user_data["tenant_id"]
    
    db = SessionLocal()
    try:
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            raise HTTPException(status_code=404, detail="Organização não encontrada.")
            
        # Verificar limites diários
        hoje = date.today()
        hoje_start = datetime.combine(hoje, datetime.min.time())
        
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Verificando limites para tenant {tenant_id}, hoje: {hoje_start}")
        
        try:
            count_hoje = db.query(Prompt).filter(
                Prompt.tenant_id == tenant_id,
                Prompt.created_at >= hoje_start
            ).count()
        except Exception as query_error:
            logger.error(f"Erro na query de contagem de prompts: {query_error}")
            import traceback
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=500, detail=f"Erro interno no banco (datas): {query_error}")
        
        if count_hoje >= tenant.max_prompts_per_day:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Limite diário de prompts atingido ({tenant.max_prompts_per_day}). Faça upgrade para continuar."
            )

        # Formata o prompt com o template
        mensagens = prompt_template_service.format_prompt(tema=tema, usuario=username)
        
        # O llm_service processa o template e retorna a resposta
        resposta_bruta = llm_service.gerar_resposta(mensagens)
        resposta_texto = resposta_bruta.content if hasattr(resposta_bruta, 'content') else str(resposta_bruta)

        # Salvar no histórico
        novo_prompt = Prompt(
            usuario=username,
            tenant_id=tenant_id,
            tema=tema,
            prompt=str(mensagens), # Simplificado
            resposta=resposta_texto
        )
        db.add(novo_prompt)
        db.commit()
        
        return {
            "status": "sucesso",
            "prompt_id": novo_prompt.id,
            "usuario": username,
            "tenant_id": tenant_id,
            "tema": tema,
            "conteudo_gerado": resposta_texto
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao processar prompt: {e}")
    finally:
        db.close()
@router.get("/historico")
def get_historico(user_data: dict = Depends(get_current_user_data)):
    """Retorna o histórico de prompts gerados pelo usuário atual dentro de seu inquilino."""
    db = SessionLocal()
    try:
        tenant_id = user_data["tenant_id"]
        username = user_data["username"]
        role = user_data["role"]
        
        query = db.query(Prompt).filter(Prompt.tenant_id == tenant_id)
        if role != "admin":
            query = query.filter(Prompt.usuario == username)
            
        prompts = query.order_by(Prompt.created_at.desc()).limit(100).all()
        return [
            {
                "id": p.id,
                "usuario": p.usuario,
                "tema": p.tema,
                "conteudo": p.resposta,
                "feedback": p.feedback,
                "created_at": parse_date(p.created_at).isoformat()
            }
            for p in prompts
        ]
    finally:
        db.close()

@router.post("/feedback")
def save_feedback(payload: FeedbackRequest, user_data: dict = Depends(get_current_user_data)):
    db = SessionLocal()
    try:
        p = db.query(Prompt).filter(
            Prompt.id == payload.prompt_id,
            Prompt.tenant_id == user_data["tenant_id"]
        ).first()
        
        if not p:
            raise HTTPException(status_code=404, detail="Prompt não encontrado.")
            
        p.feedback = payload.value
        db.commit()
        return {"status": "sucesso", "mensagem": "Feedback salvo."}
    except Exception as e:
        db.rollback()
        logger.error(f"Erro ao salvar feedback Prompt: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao salvar feedback.")
    finally:
        db.close()
