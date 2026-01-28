import re
import unicodedata

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
