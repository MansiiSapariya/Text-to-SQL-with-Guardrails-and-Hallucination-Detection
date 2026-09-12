import asyncio
import numpy as np
from dataclasses import dataclass
from sentence_transformers import SentenceTransformer
from app.llm.models import BackTranslationResult
from app.llm.prompts import build_back_translation_prompt
from app.llm.client import DEFAULT_MODEL
from app.pipeline.executor import ExecutionResult

@dataclass
class BackTranslationScore:
    alignment_score: float
    back_translated_question: str
    flags: list[str]

@dataclass
class SanityFlag:
    flag_type: str
    message: str
    severity: str

class HallucinationDetector:
    def __init__(self, llm_client, embedding_model: SentenceTransformer):
        self.client = llm_client
        self.embedding_model = embedding_model

    async def back_translation_check(self, original_question: str, sql: str) -> BackTranslationScore:
        prompt = build_back_translation_prompt(sql)

        def _call_llm():
            return self.client.chat.completions.create(
                model=DEFAULT_MODEL,
                response_model=BackTranslationResult,
                messages=prompt,
            )

        result = await asyncio.to_thread(_call_llm)
        
        embeddings = self.embedding_model.encode([original_question, result.question], normalize_embeddings=True)
        alignment_score = float(np.dot(embeddings[0], embeddings[1]))
        
        flags = []
        if not result.is_complete:
            flags.append("Back-translation indicates SQL does not fully answer the question")
        if result.missing_aspects:
            flags.extend([f"Missing aspect: {aspect}" for aspect in result.missing_aspects])
            
        return BackTranslationScore(
            alignment_score=alignment_score,
            back_translated_question=result.question,
            flags=flags
        )

    def result_sanity_check(self, result: ExecutionResult, question: str) -> list[SanityFlag]:
        flags = []
        q_lower = question.lower()
        
        is_count_query = "count" in q_lower or "how many" in q_lower
        
        if result.row_count == 0 and not is_count_query:
            flags.append(SanityFlag("empty_result", "Query returned 0 rows but was not a count query", "medium"))
            
        if result.row_count > 0:
            for col in result.columns:
                nulls = sum(1 for row in result.rows if row.get(col) is None)
                if nulls / result.row_count > 0.5:
                    flags.append(SanityFlag("high_null_rate", f"Column {col} has >50% NULL values", "low"))
                    
            if is_count_query and result.row_count == 1:
                # check if count is 0
                for col, val in result.rows[0].items():
                    if isinstance(val, (int, float)) and val == 0:
                        flags.append(SanityFlag("zero_count", f"Aggregate query returned 0 for {col}", "low"))
                        
        return flags
