from dataclasses import dataclass
from app.pipeline.hallucination import SanityFlag

@dataclass
class ConfidenceResult:
    overall: float
    grade: str
    breakdown: dict[str, float]
    label: str

class ConfidenceScorer:
    def score(self, 
        syntax_valid: bool,
        model_confidence: float, 
        back_translation_score: float,
        sanity_flags: list[SanityFlag],
        tables_expected: list[str],
        tables_used: list[str],
    ) -> ConfidenceResult:
        
        syntax_score = 1.0 if syntax_valid else 0.0
        
        sanity_score = 1.0
        for flag in sanity_flags:
            if flag.severity == "high":
                sanity_score -= 0.25
            elif flag.severity == "medium":
                sanity_score -= 0.10
            elif flag.severity == "low":
                sanity_score -= 0.05
        sanity_score = max(0.0, sanity_score)
        
        expected_set = set(tables_expected)
        used_set = set(tables_used)
        if expected_set or used_set:
            intersection = expected_set.intersection(used_set)
            union = expected_set.union(used_set)
            jaccard = len(intersection) / len(union)
        else:
            jaccard = 1.0
            
        overall = (
            syntax_score * 0.10 +
            model_confidence * 0.15 +
            back_translation_score * 0.40 +
            sanity_score * 0.20 +
            jaccard * 0.15
        )
        
        overall = max(0.0, min(1.0, overall))
        
        if overall >= 0.8:
            grade = "high"
            label = "🟢 High Confidence"
        elif overall >= 0.5:
            grade = "medium"
            label = "🟡 Medium Confidence"
        else:
            grade = "low"
            label = "🔴 Low Confidence"
            
        return ConfidenceResult(
            overall=overall,
            grade=grade,
            breakdown={
                "syntax_validity": syntax_score,
                "model_confidence": model_confidence,
                "back_translation_alignment": back_translation_score,
                "result_sanity": sanity_score,
                "schema_coverage": jaccard
            },
            label=label
        )
