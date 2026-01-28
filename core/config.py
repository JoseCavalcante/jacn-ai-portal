from dotenv import load_dotenv
import os
from pathlib import Path

# Resolve o caminho absoluto do .env na raiz do projeto
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env", override=True)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
JWT_SECRET = os.getenv("JWT_SECRET", "CHANGE_ME").strip()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")    
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")