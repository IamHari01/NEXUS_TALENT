from app.services.redis_cache import get_cache, set_cache, generate_cache_key
from app.models.cross_encoder import ATSCrossEncoder

# Import both tracer and the new shortlist_counter from your observability module
from app.core.observability import tracer, shortlist_counter
import logging

logger = logging.getLogger(__name__)
encoder = ATSCrossEncoder()


async def ats_agent(state):
    """
    Industry-grade ATS Scoring Agent.
    Optimized for SigNoz Visualizations and performance.
    """
    resume = state.get("resume", "")
    # Robust check for nested JD data
    job_obj = state.get("job", {})
    jd = job_obj.get("jd", "")

    with tracer.start_as_current_span("ATSScoringAgent") as span:
        # 1. Semantic Attributes (Standardized for SigNoz filtering)
        span.set_attribute("service.name", "nexus-talent-api")
        span.set_attribute("component", "ml-inference")
        span.set_attribute("resume.size_bytes", len(resume))

        # 2. Optimized Cache Logic
        cache_key = generate_cache_key("ats_v1", resume[:500], jd[:500])

        with tracer.start_as_current_span("redis_check") as cache_span:
            cached_score = get_cache(cache_key)
            if cached_score is not None:
                cache_span.set_attribute("cache.hit", True)
                span.set_attribute("ats.source", "cache")
                state["score"] = cached_score
                return state
            cache_span.set_attribute("cache.hit", False)

        # 3. Model Inference with Error Boundaries
        try:
            with tracer.start_as_current_span(
                "cross_encoder_inference"
            ) as inference_span:
                # Actual AI calculation
                score = encoder.score(resume, jd)

                # Add metadata for model versioning
                inference_span.set_attribute(
                    "ml.model_name", "cross-encoder-distilbert"
                )
                inference_span.set_attribute("ml.score_output", score)

            # 4. Persistence & Metrics
            set_cache(cache_key, score, ttl=86400)

            # TRIGGER METRIC: This allows you to build a 'Success Rate' chart in SigNoz
            if score >= 80:
                shortlist_counter.add(1, {"job_title": job_obj.get("title", "unknown")})

            span.set_attribute("ats.score", score)
            state["score"] = score

        except Exception as e:
            logger.error(f"ATS Inference Error: {str(e)}")
            span.record_exception(e)
            span.set_status("error", "AI Analysis Failure")
            state["score"] = 0
            state["error"] = "Analysis engine temporarily unavailable."

        return state
