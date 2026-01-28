from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

# --- CONFIGURAÇÃO DE LIMITES POR TIER ---
TIER_LIMITS = {
    "free": {
        "max_documents": 5,
        "max_prompts_per_day": 100
    },
    "pro": {
        "max_documents": 50,
        "max_prompts_per_day": 500
    },
    "enterprise": {
        "max_documents": 1000,
        "max_prompts_per_day": 10000
    }
}

Base = declarative_base()


class Tenant(Base):
    __tablename__ = "tenants"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    subscription_tier = Column(String, default="free")
    
    # Usage Tracking
    max_documents = Column(Integer, default=5)
    max_prompts_per_day = Column(Integer, default=10)
    current_document_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    users = relationship("User", back_populates="tenant")
    prompts = relationship("Prompt", back_populates="tenant")
    chat_messages = relationship("ChatMessage", back_populates="tenant")


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=True)
    role = Column(String, default="member") # admin, member
    tenant_id = Column(Integer, ForeignKey("tenants.id"))
    
    tenant = relationship("Tenant", back_populates="users")


class Prompt(Base):
    __tablename__ = "prompts"
    id = Column(Integer, primary_key=True)
    usuario = Column(String)
    tenant_id = Column(Integer, ForeignKey("tenants.id"))
    tema = Column(String)
    prompt = Column(Text)
    resposta = Column(Text)
    feedback = Column(Integer, default=0) # 0: none, 1: positive, -1: negative
    created_at = Column(DateTime, default=datetime.utcnow)
    
    tenant = relationship("Tenant", back_populates="prompts")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True)
    usuario = Column(String)
    tenant_id = Column(Integer, ForeignKey("tenants.id"))
    pergunta = Column(Text)
    resposta = Column(Text)
    sources = Column(Text) # Armazenado como JSON string
    feedback = Column(Integer, default=0) # 0: none, 1: positive, -1: negative
    created_at = Column(DateTime, default=datetime.utcnow)
    
    tenant = relationship("Tenant", back_populates="chat_messages")
