from fastapi import APIRouter, HTTPException, Depends, Header, status
from service import auth_service
from typing import Optional
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter(prefix="/auth", tags=["Auth"])
security = HTTPBearer()

def get_current_user_data(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Injeção de dependência para validar o token JWT e extrair os dados do usuário.
    """
    token = credentials.credentials
    payload = auth_service.validar_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
        )
    return payload

@router.post("/register")
def register(
    usuario: str, 
    senha: str, 
    tenant_name: Optional[str] = None, 
    user_data: Optional[dict] = Depends(auth_service.validar_token_optional)
):
    """
    Cadastra um novo usuário. 
    Se o solicitante for admin, vincula ao mesmo tenant do admin.
    """
    tenant_id = user_data.get("tenant_id") if user_data else None
    
    sucesso = auth_service.cadastrar_usuario(usuario, senha, tenant_name=tenant_name, tenant_id=tenant_id)
    if not sucesso:
        raise HTTPException(
            status_code=400, 
            detail="Usuário já cadastrado ou erro ao processar cadastro"
        )
        
    return {"status": "sucesso", "mensagem": "Usuário cadastrado com sucesso"}

@router.post("/login")
def login(usuario: str, senha: str):
    """
    Realiza o login e retorna um token JWT válido e metadados do usuário.
    """
    user = auth_service.verificar_login(usuario, senha)
    if not user:
        raise HTTPException(status_code=401, detail="Usuário ou senha inválidos")
        
    token = auth_service.criar_token(usuario, senha)
    if not token:
        raise HTTPException(status_code=401, detail="Erro ao gerar acesso")
    
    return {
        "status": "sucesso", 
        "token": token,
        "user": {
            "username": user.username,
            "role": user.role,
            "tenant_id": user.tenant_id
        }
    }


@router.post("/change-password")
def change_password(
    nova_senha: str, 
    usuario_alvo: Optional[str] = None, 
    user_data: dict = Depends(get_current_user_data)
):
    """
    Altera a senha de um usuário. 
    Se usuario_alvo for fornecido, requer cargo de 'admin'.
    """
    requester = user_data.get("sub", "").lower()
    requester_role = user_data.get("role", "member")
    
    if usuario_alvo and usuario_alvo.lower() != requester:
        if requester_role != "admin":
            raise HTTPException(status_code=403, detail="Apenas administradores podem alterar senhas de terceiros")
        target = usuario_alvo
    else:
        target = requester

    sucesso = auth_service.alterar_senha(target, nova_senha)
    
    if not sucesso:
        raise HTTPException(status_code=400, detail="Erro ao alterar senha ou usuário não encontrado")
        
    return {"status": "sucesso", "mensagem": f"Senha do usuário {target} alterada com sucesso"}
@router.get("/me/tenant")
def get_my_tenant(user_data: dict = Depends(get_current_user_data)):
    """
    Retorna informações detalhadas (limites e uso) da organização do usuário logado.
    """
    tenant_id = user_data.get("tenant_id")
    info = auth_service.obter_info_tenant(tenant_id)
    if not info:
        raise HTTPException(status_code=404, detail="Organização não encontrada")
    return info
