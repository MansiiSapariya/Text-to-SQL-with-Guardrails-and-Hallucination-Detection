from pydantic import BaseModel, Field
from typing import Optional

class ClarificationOption(BaseModel):
    interpretation: str = Field(..., description="One interpretation of the ambiguous question")
    example_sql: str = Field(..., description="Example SQL for this interpretation")

class ClarificationRequest(BaseModel):
    message: str = Field(..., description="Explanation of the ambiguity")
    options: list[ClarificationOption] = Field(..., description="Possible interpretations")

class SQLGenerationResult(BaseModel):
    sql: str = Field(..., description="A valid SQL SELECT statement. Never include DDL or DML.")
    explanation: str = Field(..., description="Plain English explanation of what this query does and what it returns")
    model_confidence: float = Field(..., ge=0.0, le=1.0, description="Your confidence that this SQL correctly answers the question, 0-1")
    tables_used: list[str] = Field(..., description="List of table names referenced in the query")
    columns_used: list[str] = Field(..., description="List of column names referenced in the query")
    assumptions: list[str] = Field(default_factory=list, description="Any assumptions made when writing this query")
    ambiguities: list[str] = Field(default_factory=list, description="Any ambiguities detected in the question")
    is_answerable: bool = Field(..., description="Whether the database schema can answer this question")
    clarification_needed: Optional[ClarificationRequest] = Field(None, description="If clarification needed, provide options")

class BackTranslationResult(BaseModel):
    question: str = Field(..., description="In one clear sentence, what question does this SQL query answer?")
    is_complete: bool = Field(..., description="Does the SQL fully answer the question, or only partially?")
    missing_aspects: list[str] = Field(default_factory=list, description="Aspects of the original question not captured by this SQL")
