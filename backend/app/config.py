from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str
    READ_ONLY_DATABASE_URL: str
    GROQ_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    LLM_PROVIDER: str = "groq"
    LLM_MODEL: str = "llama-3.3-70b-versatile"
    MAX_RESULT_ROWS: int = 500
    GUARDRAIL_MAX_SUBQUERY_DEPTH: int = 3
    GUARDRAIL_ENFORCE_LIMIT: bool = True
    SCHEMA_SIMILARITY_THRESHOLD: float = 0.25

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
