from langchain_core.prompts import ChatPromptTemplate

def get_professional_prompt_template():
    """
    Retorna um template de prompt estruturado para geração de conteúdo.
    Define persona, diretrizes e formato esperado.
    """
    return ChatPromptTemplate.from_messages([
        ("system", """Você é um Assistente de Inteligência Artificial Especialista e Consultor Técnico.
        Sua tarefa é fornecer respostas precisas, claras e bem estruturadas sobre o tema solicitado.
        
        DIRETRIZES:
        1. Responda diretamente ao que foi solicitado de forma profissional.
        2. Se o tema for uma pergunta, forneça a resposta técnica detalhada.
        3. Se o tema for uma solicitação de criação de conteúdo, gere o conteúdo estruturado.
        4. Use um tom de voz executivo, preciso e inspirador.
        5. Responda sempre em Português Brasileiro (pt-BR)."""),
        
        ("human", "Tema ou Pergunta: '{tema}'. \n\nPor favor, forneça o melhor conteúdo ou resposta possível para o usuário '{usuario}'.")
    ])

def format_prompt(tema: str, usuario: str) -> str:
    """
    Formata o prompt usando o template estruturado.
    """
    template = get_professional_prompt_template()
    # Retorna o objeto formatado pronto para o LLM.invoke()
    return template.format_messages(tema=tema, usuario=usuario)
