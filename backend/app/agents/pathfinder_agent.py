import os
import asyncio
from typing import Dict, Any, List
from googleapiclient.discovery import build  # pip install google-api-python-client
from app.core.observability import tracer
from app.services.redis_cache import get_cache, set_cache, generate_cache_key

# Configuration
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)


async def pathfinder_agent(state: Dict[str, Any]):
    """
    Industry-level Learning Path Generator.
    Integrates real-time YouTube search, Redis caching, and SigNoz tracing.
    """
    gaps = state.get("missing_skills", {})
    # Normalize input from Gap Agent
    missing_skills = (
        gaps.get("hard_skills", []) + gaps.get("soft_skills", [])
        if isinstance(gaps, dict)
        else gaps
    )

    if not missing_skills:
        state["learning_path"] = []
        return state

    with tracer.start_as_current_span("PathfinderAgent") as span:
        span.set_attribute("agent.type", "learning_pathfinder")
        span.set_attribute("skills.to_solve", len(missing_skills))

        # 1. Hashed Cache Check
        cache_key = generate_cache_key("learning_v2", ",".join(sorted(missing_skills)))
        cached_path = get_cache(cache_key)
        if cached_path:
            span.set_attribute("cache.hit", True)
            state["learning_path"] = cached_path
            return state

        span.set_attribute("cache.hit", False)
        learning_path = []

        # 2. Real-time Search Execution
        for skill in missing_skills:
            # We use a nested span with 'search' semantic conventions for SigNoz
            with tracer.start_as_current_span(
                "youtube_search_operation"
            ) as search_span:
                search_span.set_attribute("search.query", skill)
                search_span.set_attribute("search.system", "youtube_v3")

                try:
                    # Industry standard: specifically search for 'full course' to improve quality
                    query = f"{skill} masterclass full course 2026"

                    # Run in thread pool if using synchronous google-api-client
                    request = youtube.search().list(
                        q=query, part="snippet", maxResults=1, type="video"
                    )
                    response = await asyncio.to_thread(request.execute)

                    video_data = response.get("items", [{}])[0]
                    video_id = video_data.get("id", {}).get("videoId")

                    path_item = {
                        "skill": skill,
                        "resource_url": (
                            f"https://www.youtube.com/watch?v={video_id}"
                            if video_id
                            else None
                        ),
                        "title": video_data.get("snippet", {}).get(
                            "title", "Resource not found"
                        ),
                        "milestones": [
                            f"Master {skill} fundamentals",
                            f"Build a {skill} project",
                            f"Optimize {skill} for production",
                        ],
                        "estimated_time": "12-15 hours",
                    }
                    learning_path.append(path_item)

                except Exception as e:
                    search_span.record_exception(e)
                    search_span.set_status("error", "YouTube API failure")
                    continue

        # 3. Persistence (7-day TTL)
        set_cache(cache_key, learning_path, ttl=604800)
        state["learning_path"] = learning_path

        return state
