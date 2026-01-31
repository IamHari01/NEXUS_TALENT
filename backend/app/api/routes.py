from fastapi import APIRouter, HTTPException, status
from app.orchestration.career_graph import run_graph
from app.api.schemas import AnalyzeRequest
from app.core.observability import tracer
import logging

# Standardized logging for startup-level auditing
logger = logging.getLogger("nexus-talent")
router = APIRouter(prefix="/v1/career", tags=["Career Intelligence"])


@router.post("/analyze", status_code=status.HTTP_200_OK)
async def analyze(req: AnalyzeRequest):
    """
    Main entry point for the Career Intelligence Engine.
    Coordinates Sourcing, ATS Scoring, Gap Analysis, and Pathfinding.
    """
    # 1. Initialize the Root Span
    # Everything happening inside the agents will be 'children' of this span
    with tracer.start_as_current_span("CareerIntelligenceWorkflow") as span:
        try:
            # 2. Add high-level metadata for global monitoring
            span.set_attribute("http.method", "POST")
            span.set_attribute("user.job_title", req.job_title)
            span.set_attribute("user.location", req.location)

            # 3. Execute the Orchestrator
            # We pass the validated Pydantic model converted to a dict
            logger.info(f"Starting analysis for {req.job_title} in {req.location}")

            result = await run_graph(req.model_dump())

            # 4. Attach final outcome to the trace
            span.set_attribute("final.score_avg", result.get("score", 0))
            span.set_status("ok")

            return result

        except Exception as e:
            # 5. Production Error Handling
            # This ensures errors are recorded in Jaeger/Prometheus
            span.record_exception(e)
            span.set_status("error", str(e))
            logger.error(f"Workflow failed: {str(e)}")

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An internal error occurred while processing your career analysis.",
            )
