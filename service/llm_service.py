from service.ai_config import get_llm

# Usamos temperature 0.1 para respostas mais precisas e estruturadas
llm = get_llm(temperature=0.1)

def gerar_resposta(prompt: str | list) -> str:
    """
    Invoca o LLM. Aceita tanto uma string simples quanto uma 
    lista de mensagens formatadas por um template.
    """
    return llm.invoke(prompt).content
