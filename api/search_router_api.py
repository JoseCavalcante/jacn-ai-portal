from fastapi import APIRouter, HTTPException, status
from service.search_service import similarity_search, init_search
from service.rag_chain_service import ask_rag
from pydantic import BaseModel

router = APIRouter()


class AskRequest(BaseModel):
    question: str
    k: int = 2
    score_threshold: float = 0.6

@router.post("/search")
def search():
    try:
        init_search() 
        results = similarity_search("O que é LangChain?", k=2)

        return {
            "query": "O que é LangChain?",
            "results": results
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
#===============================================================================

@router.post("/ask")
def ask(payload: AskRequest):
    try:
        init_search()

        docs = similarity_search(payload.question, payload.k)

        filtered_docs = [
            d for d in docs if d["score"] <= payload.score_threshold
        ]

        if not filtered_docs:
            return {
                "answer": "Não encontrei essa informação nos documentos.",
                "sources": []
            }

        context = "\n\n".join(d["content"] for d in filtered_docs)

        response = ask_rag(
            context=context,
            question=payload.question
        )

        return {
            "question": payload.question,
            "answer": response.content,
            "sources": filtered_docs
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))