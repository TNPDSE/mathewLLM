from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
import uvicorn

from app.audit_service import ask_audit_question
from app.utils import settings
from app.audit_service import LAST_INTERACTION

app = FastAPI(
    title="Audit QA API",
    version="1.0.0"
)

# Internal API Key
INTERNAL_API_KEY = settings.INTERNAL_API_KEY


class QuestionRequest(BaseModel):
    question: str


def validate_api_key(x_api_key: str = Header(...)):
    if x_api_key != INTERNAL_API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid API Key"
        )


@app.get("/api/health")
def health():
    return {
        "status": "healthy",
        "service": "audit-qa-api"
    }


@app.post("/api/ask")
def ask(
    req: QuestionRequest,
    x_api_key: str = Header(...)
):

    validate_api_key(x_api_key)

    return ask_audit_question(req.question)


@app.post("/api/reset")
def reset_chat(x_api_key: str = Header(...)):

    validate_api_key(x_api_key)

    LAST_INTERACTION["question"] = None
    LAST_INTERACTION["response"] = None

    return {"status": "reset"}

# uvicorn app.main:app --reload --port 8001