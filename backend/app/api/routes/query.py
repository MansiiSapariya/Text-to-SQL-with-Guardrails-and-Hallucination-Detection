import uuid
import datetime
import asyncio
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import sqlglot

from app.llm.models import SQLGenerationResult
from app.llm.prompts import build_sql_generation_prompt
from app.llm.client import DEFAULT_MODEL

router = APIRouter()

class QueryRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=500)
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

class QueryResponse(BaseModel):
    query_id: str
    session_id: str
    question: str
    sql: str
    sql_explanation: str
    results: list[dict]
    columns: list[str]
    row_count: int
    truncated: bool
    execution_time_ms: float
    confidence: dict
    guardrail_warnings: list[dict]
    hallucination_flags: list[str]
    assumptions: list[str]
    is_answerable: bool
    clarification_needed: Optional[dict]
    error: Optional[str]
    timestamp: str

@router.post("/query", response_model=QueryResponse)
async def execute_query(req: QueryRequest, request: Request):
    app_state = request.app.state
    
    query_id = str(uuid.uuid4())
    timestamp = datetime.datetime.utcnow().isoformat()
    
    # 1 & 2. Filter schema
    relevant_tables = app_state.schema_filter.get_relevant_tables(req.question)
    schema_ctx, rels, samples = app_state.schema_filter.format_schema_for_prompt(relevant_tables)
    
    # 3. Generate SQL (instructor is sync — offload to thread pool)
    prompt = build_sql_generation_prompt(schema_ctx, rels, samples, req.question)

    def _generate_sql():
        return app_state.llm_client.chat.completions.create(
            model=DEFAULT_MODEL,
            response_model=SQLGenerationResult,
            messages=prompt,
        )

    gen_result: SQLGenerationResult = await asyncio.to_thread(_generate_sql)
    
    # 4 & 5. Early exits
    if not gen_result.is_answerable or gen_result.clarification_needed:
        return QueryResponse(
            query_id=query_id,
            session_id=req.session_id,
            question=req.question,
            sql="",
            sql_explanation="",
            results=[],
            columns=[],
            row_count=0,
            truncated=False,
            execution_time_ms=0.0,
            confidence={},
            guardrail_warnings=[],
            hallucination_flags=[],
            assumptions=[],
            is_answerable=gen_result.is_answerable,
            clarification_needed=gen_result.clarification_needed.model_dump() if gen_result.clarification_needed else None,
            error="Question is not answerable or needs clarification." if not gen_result.is_answerable else None,
            timestamp=timestamp
        )

    # 6. Syntax validation
    syntax_valid = True
    try:
        sqlglot.parse_one(gen_result.sql)
    except Exception:
        syntax_valid = False
        
    # 7 & 8. Guardrails
    guard_result = app_state.guardrails.check(gen_result.sql)
    warnings = [{"rule": v.rule_name, "message": v.message} for v in guard_result.violations]
    
    if not guard_result.passed:
        return QueryResponse(
            query_id=query_id,
            session_id=req.session_id,
            question=req.question,
            sql=gen_result.sql,
            sql_explanation=gen_result.explanation,
            results=[],
            columns=[],
            row_count=0,
            truncated=False,
            execution_time_ms=0.0,
            confidence={},
            guardrail_warnings=warnings,
            hallucination_flags=[],
            assumptions=gen_result.assumptions,
            is_answerable=True,
            clarification_needed=None,
            error="Query blocked by guardrails.",
            timestamp=timestamp
        )
        
    modified_sql = guard_result.modified_sql
    
    # 9. Execute
    try:
        exec_result = await app_state.executor.execute(modified_sql)
    except Exception as e:
        return QueryResponse(
            query_id=query_id,
            session_id=req.session_id,
            question=req.question,
            sql=modified_sql,
            sql_explanation=gen_result.explanation,
            results=[],
            columns=[],
            row_count=0,
            truncated=False,
            execution_time_ms=0.0,
            confidence={},
            guardrail_warnings=warnings,
            hallucination_flags=[],
            assumptions=gen_result.assumptions,
            is_answerable=True,
            clarification_needed=None,
            error=f"Execution error: {str(e)}",
            timestamp=timestamp
        )

    # 10 & 11. Hallucination
    bt_score = await app_state.hallucination.back_translation_check(req.question, modified_sql)
    sanity_flags = app_state.hallucination.result_sanity_check(exec_result, req.question)
    
    h_flags = bt_score.flags + [f.message for f in sanity_flags]

    # 12. Confidence
    conf = app_state.confidence.score(
        syntax_valid=syntax_valid,
        model_confidence=gen_result.model_confidence,
        back_translation_score=bt_score.alignment_score,
        sanity_flags=sanity_flags,
        tables_expected=relevant_tables,
        tables_used=gen_result.tables_used
    )

    # 13. Store history
    resp = QueryResponse(
        query_id=query_id,
        session_id=req.session_id,
        question=req.question,
        sql=modified_sql,
        sql_explanation=gen_result.explanation,
        results=exec_result.rows,
        columns=exec_result.columns,
        row_count=exec_result.row_count,
        truncated=exec_result.truncated,
        execution_time_ms=exec_result.execution_time_ms,
        confidence=conf.__dict__,
        guardrail_warnings=warnings,
        hallucination_flags=h_flags,
        assumptions=gen_result.assumptions,
        is_answerable=True,
        clarification_needed=None,
        error=None,
        timestamp=timestamp
    )
    
    if req.session_id not in app_state.history:
        app_state.history[req.session_id] = []
    app_state.history[req.session_id].append(resp)
    
    return resp
