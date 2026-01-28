from fastapi import APIRouter, Depends, Header, HTTPException
from service.llm_service import gerar_resposta
from service.auth_service import validar_token

router = APIRouter(prefix="/prompts", tags=["Prompts"])

@router.post("/")
def criar_prompt(
    tema: str,
    publico: str,
    objetivo: str,
    authorization: str = Header(...)
):
    token = authorization.replace("Bearer ", "")
    payload = validar_token(token)
    if not payload:
         raise HTTPException(status_code=401, detail="Token inválido ou expirado")

    prompt = f"Crie conteúdo sobre {tema} para {publico} com objetivo {objetivo}."
    resposta = gerar_resposta(prompt)

    return {
        "prompt": prompt,
        "resposta": resposta,
        "tenant_id": payload.get("tenant_id")
    }