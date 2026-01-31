import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# Absolute imports based on your repository structure
from app.api.routes import router as career_router
from app.core.observability import tracer  # Ensures OTEL initialization

# Initialize Production Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nexus-talent")


def create_app() -> FastAPI:
    """
    Factory to initialize the FastAPI application with
    production-grade instrumentation and middleware.
    """
    app = FastAPI(
        title="Nexus-Talent AI Engine",
        description="Startup-grade Job Intelligence & Agentic RAG Platform",
        version="1.0.0",
        docs_url="/api/docs",  # Standard professional path
        redoc_url="/api/redoc",
    )

    # 1. Security & CORS Configuration
    # Essential for connecting your Next.js frontend to this backend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, replace with your specific domain
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 2. Mount Routers
    # Connects the /v1/career/analyze endpoint for the frontend
    app.include_router(career_router)

    # 3. Health Check Endpoint
    @app.get("/health", tags=["Infrastructure"])
    async def health_check():
        return {"status": "healthy", "engine": "active"}

    # 4. Automated SigNoz/OTEL Instrumentation
    # Captures HTTP metrics (latencies, errors) automatically
    FastAPIInstrumentor.instrument_app(app)

    @app.on_event("startup")
    async def startup_event():
        logger.info("Nexus-Talent AI Engine successfully launched.")
        # Any additional startup logic (DB warmups) goes here

    return app


# Instance used by Uvicorn (e.g., uvicorn app.main:app)
app = create_app()
