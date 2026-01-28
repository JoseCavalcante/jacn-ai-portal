import jwt
import time
from fastapi import Header
from core.config import JWT_SECRET
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Union
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from db.database import SessionLocal
from db.models import User, Tenant

# Configuração do contexto de hashing (usando sha256_crypt por ser mais estável em Windows/Python 3.11)
pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    """Verifica se a senha em texto plano corresponde ao hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """Gera um hash seguro para a senha."""
    return pwd_context.hash(password)

def obter_JWT():
    """Retorna o segredo JWT centralizado no core/config."""
    return JWT_SECRET

def verificar_login(username_tentativa: str, senha_tentativa: str) -> Optional[User]:
    """
    Verifica as credenciais do usuário. 
    Suporta fallback para texto plano caso o hash falhe (migração).
    """
    db = SessionLocal()
    try:
        username_tentativa = username_tentativa.strip().lower()
        user = db.query(User).filter(User.username == username_tentativa).first()
        
        if not user:
            return None
            
        try:
            if verify_password(senha_tentativa, user.password_hash):
                return user
        except Exception:
            # Fallback para texto plano se necessário
            if user.password_hash == senha_tentativa:
                return user
        
        return None
    finally:
        db.close()

def cadastrar_usuario(usuario: str, senha_plana: str, tenant_name: str = None, tenant_id: int = None) -> bool:
    """
    Cadastra um novo usuário e opcionalmente uma nova organização.
    Se tenant_id for fornecido, vincula diretamente (usado por admins para membros).
    """
    db = SessionLocal()
    try:
        usuario = usuario.strip().lower()
        existing_user = db.query(User).filter(User.username == usuario).first()
        if existing_user:
            return False
            
        # Lógica de Tenant:
        # 1. Se tenant_id foi passado, usamos ele (usuário convidado por admin)
        # 2. Se tenant_name foi passado, criamos/buscamos o tenant (novo cadastro SaaS)
        # 3. Se nenhum for passado, retornamos erro (evita cair no tenant 1 por erro)
        
        tenant = None
        if tenant_id:
            tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
            if not tenant:
                print(f"Erro: Tenant ID {tenant_id} não encontrado.")
                return False
        elif tenant_name:
            tenant_name = tenant_name.strip()
            tenant = db.query(Tenant).filter(Tenant.name == tenant_name).first()
            if not tenant:
                tenant = Tenant(name=tenant_name)
                db.add(tenant)
                db.flush() # Gera o ID do tenant
        else:
            # Caso crítico: sem tenant e sem nome, não podemos cadastrar.
            # No passado isso fazia db.query(Tenant).first(), o que era inseguro.
            print("Erro: Tentativa de cadastro sem Tenant ID ou Nome de Organização.")
            return False

        if not tenant:
            return False

        novo_usuario = User(
            username=usuario,
            password_hash=get_password_hash(senha_plana),
            tenant_id=tenant.id,
            role="admin" if tenant_name else "member"
        )
        db.add(novo_usuario)
        db.commit()
        return True
    except Exception as e:
        print(f"Erro ao cadastrar usuário: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def criar_token(usuario: str, senha: str) -> Optional[str]:   
    """Gera um token JWT com validade de 8 horas."""
    user = verificar_login(usuario, senha)
    if not user:
        return None
    
    payload = {
        "sub": user.username,
        "tenant_id": user.tenant_id,
        "role": user.role,
        "exp": int(time.time() + (8 * 3600))
    }
    return jwt.encode(payload, obter_JWT(), algorithm="HS256")

def validar_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Valida o token JWT e retorna o payload ou None se for inválido.
    """
    if not token or not isinstance(token, str):
        return None
        
    try:
        payload = jwt.decode(token, obter_JWT(), algorithms=["HS256"])
        return payload
    except Exception as e:
        # Avoid direct print in prod, but keeping it simple for now
        print(f"Debug JWT: Erro ao validar token: {e}")
        return None

def validar_token_optional(authorization: Optional[str] = Header(None)) -> Optional[Dict[str, Any]]:
    """
    Versão opcional para o registro público.
    """
    if not authorization:
        return None
    token = authorization
    if authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
    return validar_token(token)

def alterar_senha(usuario: str, nova_senha_plana: str) -> bool:
    db = SessionLocal()
    try:
        usuario_target = usuario.strip().lower()
        user = db.query(User).filter(User.username == usuario_target).first()
        
        if not user:
            return False
            
        user.password_hash = get_password_hash(nova_senha_plana)
        db.commit()
        return True
    except Exception as e:
        print(f"Erro ao alterar senha: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def obter_info_tenant(tenant_id: int) -> Optional[Dict[str, Any]]:
    """Busca informações de limites e uso de um Tenant."""
    db = SessionLocal()
    try:
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            return None
        return {
            "name": tenant.name,
            "subscription_tier": tenant.subscription_tier,
            "max_documents": tenant.max_documents,
            "max_prompts_per_day": tenant.max_prompts_per_day,
            "current_document_count": tenant.current_document_count
        }
    finally:
        db.close()
