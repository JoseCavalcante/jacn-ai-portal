from service.ai_config import get_llm
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
import os


def get_rag_chain():
    llm = get_llm()

    prompt = PromptTemplate(
        input_variables=["context", "question"],
        template="""Você é um assistente técnico especializado.

Responda à PERGUNTA do usuário baseando-se EXCLUSIVAMENTE no CONTEXTO fornecido abaixo.
O contexto contém fragmentos de documentos identificados por [[FONTE: nome_do_arquivo, PÁGINA: numero]].

Regras:
1. Se a resposta não estiver no contexto, diga exatamente: "Não encontrei essa informação nos documentos."
2. Ao responder, você pode mencionar o nome do documento de onde extraiu a informação se for relevante para a precisão técnica.
3. Seja direto, profissional e siga o idioma da pergunta.
4. Formate a resposta em parágrafos contínuos. NÃO quebre linhas a cada frase.

CONTEXTO:
{context}

PERGUNTA:
{question}

RESPOSTA:
"""
    )

    return prompt | llm


def ask_rag(context: str, question: str):
    chain = get_rag_chain()
    return chain.invoke(
        {
            "context": context,
            "question": question
        }
    )
