import instructor
from groq import Groq
from openai import OpenAI
from app.config import settings

def get_instructor_client():
    """Returns an instructor-wrapped client based on LLM_PROVIDER setting."""
    if settings.LLM_PROVIDER == "groq":
        groq_client = Groq(api_key=settings.GROQ_API_KEY)
        return instructor.from_openai(groq_client, mode=instructor.Mode.JSON)
    elif settings.LLM_PROVIDER == "gemini":
        gemini_client = OpenAI(
            api_key=settings.GEMINI_API_KEY,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
        )
        return instructor.from_openai(gemini_client)
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {settings.LLM_PROVIDER}")

client = get_instructor_client()

DEFAULT_MODEL = settings.LLM_MODEL
