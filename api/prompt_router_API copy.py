from fastapi import APIRouter
from service import auth_service
from service import llm_service

from fastapi import HTTPException, status

router = APIRouter()

@router.get("/")
async def raiz():
    return "Gerador de conteúdo via LLM API rodando!"

@router.post("/gerar_conteudo")
def gerar_prompt(tema: str, usuario: str, senha: str):

    """
    Gera um prompt via LLM.
    Requer token JWT válido no header 'Authorization'.
    """
    
    token_str = auth_service.criar_token(usuario, senha)
    
    if token_str == None:
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    else:
        payload = auth_service.validar_token(token_str)
        usuario = payload.get("sub")
    
    prompt_texto = f"Crie um prompt profissional sobre '{tema}' para o usuário '{usuario}'"
    resposta = llm_service.gerar_resposta(prompt_texto)
    
    return {
        "usuario": usuario,
        "tema": tema,
        "prompt": resposta
    }