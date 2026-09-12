from dataclasses import dataclass
from enum import Enum
from typing import Protocol
import sqlglot
import sqlparse
import re
import logging
from app.config import settings

logger = logging.getLogger(__name__)

class GuardrailSeverity(Enum):
    BLOCK = "block"
    WARN = "warn"

@dataclass
class GuardrailViolation:
    rule_name: str
    severity: GuardrailSeverity
    message: str
    detail: str = ""

@dataclass 
class GuardrailResult:
    passed: bool
    violations: list[GuardrailViolation]
    modified_sql: str

class GuardrailRule(Protocol):
    name: str
    def check(self, sql: str) -> GuardrailViolation | None: ...
    def modify(self, sql: str) -> str: ...

class DDLBlockRule:
    name = "ddl_block"
    def check(self, sql: str) -> GuardrailViolation | None:
        try:
            for statement in sqlglot.parse(sql):
                if not statement:
                    continue
                if isinstance(statement, (sqlglot.exp.Create, sqlglot.exp.Drop, sqlglot.exp.Alter)):
                    return GuardrailViolation(self.name, GuardrailSeverity.BLOCK, "DDL operations are not allowed")
        except Exception:
            pass
        return None
        
    def modify(self, sql: str) -> str:
        return sql

class DMLBlockRule:
    name = "dml_block"
    def check(self, sql: str) -> GuardrailViolation | None:
        try:
            for statement in sqlglot.parse(sql):
                if not statement:
                    continue
                if isinstance(statement, (sqlglot.exp.Insert, sqlglot.exp.Update, sqlglot.exp.Delete)):
                    return GuardrailViolation(self.name, GuardrailSeverity.BLOCK, "DML operations are not allowed")
        except Exception:
            pass
        return None
        
    def modify(self, sql: str) -> str:
        return sql

class MultiStatementRule:
    name = "multi_statement"
    def check(self, sql: str) -> GuardrailViolation | None:
        statements = sqlparse.split(sql)
        if len([s for s in statements if s.strip()]) > 1:
            return GuardrailViolation(self.name, GuardrailSeverity.BLOCK, "Multiple statements are not allowed")
        return None
        
    def modify(self, sql: str) -> str:
        return sql

class LimitEnforcementRule:
    name = "limit_enforcement"
    def check(self, sql: str) -> GuardrailViolation | None:
        if not settings.GUARDRAIL_ENFORCE_LIMIT:
            return None
        try:
            parsed = sqlglot.parse_one(sql)
            if not parsed.args.get("limit"):
                return GuardrailViolation(self.name, GuardrailSeverity.WARN, f"No LIMIT found, injecting LIMIT {settings.MAX_RESULT_ROWS}")
        except Exception:
            pass
        return None
        
    def modify(self, sql: str) -> str:
        if not settings.GUARDRAIL_ENFORCE_LIMIT:
            return sql
        try:
            parsed = sqlglot.parse_one(sql)
            if not parsed.args.get("limit"):
                return parsed.limit(settings.MAX_RESULT_ROWS).sql()
        except Exception:
            pass
        return sql

class SubqueryDepthRule:
    name = "subquery_depth"
    def check(self, sql: str) -> GuardrailViolation | None:
        try:
            parsed = sqlglot.parse_one(sql)
            # basic depth check using AST traversal
            depth = 0
            for node in parsed.find_all(sqlglot.exp.Select):
                # naive count
                depth += 1
            if depth > settings.GUARDRAIL_MAX_SUBQUERY_DEPTH:
                return GuardrailViolation(self.name, GuardrailSeverity.BLOCK, f"Subquery depth exceeds maximum of {settings.GUARDRAIL_MAX_SUBQUERY_DEPTH}")
        except Exception:
            pass
        return None
        
    def modify(self, sql: str) -> str:
        return sql

class CommentStrippingRule:
    name = "comment_stripping"
    def check(self, sql: str) -> GuardrailViolation | None:
        if "--" in sql or "/*" in sql:
            return GuardrailViolation(self.name, GuardrailSeverity.WARN, "Comments found in SQL")
        return None
        
    def modify(self, sql: str) -> str:
        return sqlparse.format(sql, strip_comments=True)

class ForbiddenKeywordRule:
    name = "forbidden_keyword"
    def check(self, sql: str) -> GuardrailViolation | None:
        forbidden = ["EXECUTE", "EXEC", "xp_", "sp_", "pg_read_file", "COPY", "pg_ls_dir"]
        upper_sql = sql.upper()
        for kw in forbidden:
            if kw.upper() in upper_sql:
                return GuardrailViolation(self.name, GuardrailSeverity.BLOCK, f"Forbidden keyword detected: {kw}")
        return None
        
    def modify(self, sql: str) -> str:
        return sql

class GuardrailMiddleware:
    def __init__(self):
        self.rules = [
            CommentStrippingRule(),
            ForbiddenKeywordRule(),
            DDLBlockRule(),
            DMLBlockRule(),
            MultiStatementRule(),
            SubqueryDepthRule(),
            LimitEnforcementRule()
        ]

    def check(self, sql: str) -> GuardrailResult:
        violations = []
        modified_sql = sql
        
        for rule in self.rules:
            modified_sql = rule.modify(modified_sql)
            violation = rule.check(modified_sql)
            if violation:
                violations.append(violation)
                
        passed = not any(v.severity == GuardrailSeverity.BLOCK for v in violations)
        return GuardrailResult(passed, violations, modified_sql)

    def log_violation(self, violation: GuardrailViolation, original_question: str):
        logger.warning(f"Guardrail Violation: {violation.rule_name} - {violation.message} (Question: {original_question})")
