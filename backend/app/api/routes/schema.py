from fastapi import APIRouter, Request
from app.database.schema_extractor import SchemaContext

router = APIRouter()

@router.get("/schema")
async def get_schema(request: Request):
    ctx: SchemaContext = request.app.state.schema_extractor.get_schema_context()
    return {
        "tables": ctx.tables,
        "relationships": ctx.relationships,
        "total_tables": ctx.total_tables
    }

@router.get("/schema/tables")
async def get_tables(request: Request):
    ctx: SchemaContext = request.app.state.schema_extractor.get_schema_context()
    return {"tables": list(ctx.tables.keys())}
