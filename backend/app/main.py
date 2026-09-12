from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import logging
from contextlib import asynccontextmanager

from app.config import settings
from app.database.schema_extractor import SchemaExtractor
from app.pipeline.schema_filter import SchemaFilter
from app.pipeline.guardrails import GuardrailMiddleware
from app.pipeline.executor import QueryExecutor
from app.pipeline.hallucination import HallucinationDetector
from app.pipeline.confidence import ConfidenceScorer
from app.llm.client import client as llm_client

from app.api.routes import query, schema, history

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize components
    logger.info("Initializing components...")
    
    app.state.schema_extractor = SchemaExtractor()
    app.state.schema_filter = SchemaFilter(app.state.schema_extractor)
    app.state.guardrails = GuardrailMiddleware()
    
    app.state.executor = QueryExecutor(settings.READ_ONLY_DATABASE_URL)
    await app.state.executor.initialize()
    
    app.state.llm_client = llm_client
    app.state.hallucination = HallucinationDetector(llm_client, app.state.schema_filter.model)
    app.state.confidence = ConfidenceScorer()
    
    # In-memory storage
    app.state.history = {}
    app.state.feedback = {}
    
    logger.info("Startup complete.")
    yield
    
    logger.info("Shutting down components...")
    await app.state.executor.close()

app = FastAPI(title="Text-to-SQL API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body},
    )

app.include_router(query.router, prefix="/v1", tags=["Query"])
app.include_router(schema.router, prefix="/v1", tags=["Schema"])
app.include_router(history.router, prefix="/v1", tags=["History"])

@app.get("/")
def read_root():
    return RedirectResponse(url="/docs")

@app.get("/health")
def health_check():
    return {"status": "ok", "version": "1.0.0"}
