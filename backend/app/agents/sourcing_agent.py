import os
from typing import Dict, Any, List
from app.core.observability import tracer
from app.services.redis_cache import get_cache, set_cache, generate_cache_key
from app.services.job_stream import fetch_jobs
from app.services.weaviate_service import query_similar_jobs
from app.api.schemas import ResumeData


async def sourcing_agent(state: Dict[str, Any]):
    """
    Industry-grade Sourcing Agent with Structured Data Intelligence.
    Logic: Redis Cache -> Weaviate Semantic Skill-Match -> External API Fallback.
    """
    # Extract inputs and structured resume data
    title = state.get("job_title")
    location = state.get("location")
    resume_obj: ResumeData = state.get("resume_object")

    # Flatten skills for better vector embedding search
    skills = resume_obj.skills if resume_obj else []
    skills_query = ", ".join(skills) if skills else title

    with tracer.start_as_current_span("SourcingAgent") as span:
        span.set_attribute("agent.type", "high_precision_sourcing")
        span.set_attribute("search.title", title)
        span.set_attribute("search.skills_count", len(skills))

        # 1. Level 1: Redis Cache (Speed Layer)
        cache_key = generate_cache_key("jobs_v3", title, location, skills_query[:50])
        cached_jobs = get_cache(cache_key)

        if cached_jobs:
            span.set_attribute("data.source", "redis_cache")
            state["jobs"] = cached_jobs
            return state

        # 2. Level 2: Weaviate Semantic Vector Search (Precision Layer)
        # We query using both the Job Title and the actual parsed skills
        with tracer.start_as_current_span("weaviate_skill_matching") as v_span:
            internal_jobs = await query_similar_jobs(
                title=title,
                location=location,
                skills=skills,  # Passing structured skills to Weaviate
            )

            if internal_jobs and len(internal_jobs) >= 3:
                v_span.set_attribute("weaviate.match_count", len(internal_jobs))
                span.set_attribute("data.source", "weaviate_vector_db")
                state["jobs"] = internal_jobs
                return state

        # 3. Level 3: External API (Freshness Layer)
        try:
            with tracer.start_as_current_span("external_api_fetch") as api_span:
                # Fallback to streaming if our internal database has no matches
                jobs = await fetch_jobs(title, location)
                span.set_attribute("jobs.found", len(jobs))
                span.set_attribute("data.source", "external_api_fallback")

            # Cache the new results for 30 minutes
            set_cache(cache_key, jobs, ttl=1800)
            state["jobs"] = jobs

        except Exception as e:
            span.record_exception(e)
            span.set_status("error", "Sourcing Layer Failure")
            state["jobs"] = []
            state["error"] = "Could not retrieve jobs at this time."

        return state
