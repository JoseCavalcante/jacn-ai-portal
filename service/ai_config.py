import os
from langchain_groq import ChatGroq
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

def get_llm(temperature=0.3):
    """
    Factory para instanciar o modelo Groq de forma centralizada.
    Padrão: llama-3.3-70b-versatile
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY não encontrada no ambiente (.env)")
        
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=temperature,
        api_key=api_key
    )
