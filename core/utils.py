import os
import re
import unicodedata
from pathlib import Path
from typing import Union

def slugify(value: str) -> str:
    """
    Converte uma string para um formato seguro para pastas.
    Ex: "Jacn Soluções Ltda" -> "jacn_solucoes_ltda"
    """
    # Normaliza caracteres unicode (acentos)
    value = str(value)
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    # Tudo para minúsculo e remove caracteres não alfanuméricos
    value = re.sub(r'[^\w\s-]', '', value).strip().lower()
    # Substitui espaços por underscores
    return re.sub(r'[-\s]+', '_', value)

def get_tenant_path(tenant_id: Union[int, str], tenant_name: str = None) -> str:
    """
    Resolve o caminho absoluto da pasta do inquilino de forma robusta.
    Tenta encontrar pastas que comecem com "ID_" ou sejam apenas o "ID".
    """
    base_dir = Path(__file__).resolve().parent.parent
    uploads_dir = os.path.join(base_dir, "data", "uploads")
    
    tid_str = str(tenant_id)
    
    # 1. Tenta match exato ou por prefixo (ID_*)
    if os.path.exists(uploads_dir):
        for d in os.listdir(uploads_dir):
            if d == tid_str or d.startswith(f"{tid_str}_"):
                return os.path.join(uploads_dir, d)
    
    # 2. Fallback caso não exista (cria no formato ID_Slug se tiver nome)
    if tenant_name:
        return os.path.join(uploads_dir, f"{tid_str}_{slugify(tenant_name)}")
    
    return os.path.join(uploads_dir, tid_str)
