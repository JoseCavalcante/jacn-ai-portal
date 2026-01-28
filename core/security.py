import jwt
from datetime import datetime, timedelta
from core.config import JWT_SECRET

def criar_token(usuario: str):
    payload = {
    "sub": usuario,
    "exp": datetime.utcnow() + timedelta(hours=8)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def validar_token(token: str):
    return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])