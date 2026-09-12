from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class FeedbackRequest(BaseModel):
    query_id: str
    correct: bool
    corrected_sql: Optional[str] = None

@router.get("/history")
async def get_history(session_id: str, request: Request):
    history = request.app.state.history.get(session_id, [])
    return {"history": history}

@router.post("/feedback")
async def post_feedback(feedback: FeedbackRequest, request: Request):
    request.app.state.feedback[feedback.query_id] = feedback.model_dump()
    return {"status": "ok"}
