import httpx
import logging
from typing import List, Dict, Any
from app.core.config import settings
from app.core.observability import tracer

logger = logging.getLogger("nexus-talent")


async def fetch_jobs(title: str, location: str) -> List[Dict[str, Any]]:
    """
    Fetches real-time job listings from external providers.
    Uses asynchronous HTTP requests to maintain high performance.
    """
    with tracer.start_as_current_span("external_job_stream_fetch") as span:
        span.set_attribute("stream.query", title)
        span.set_attribute("stream.location", location)

        try:
            # Example using a mock aggregator or specific Job Board API
            # Replace URL with actual endpoint from your provider (e.g., Adzuna, Reed)
            api_url = f"https://api.jobprovider.com/v1/search"
            params = {
                "title": title,
                "location": location,
                "limit": 10,
                "country": "us",
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                # In a real scenario, you'd add headers={"Authorization": f"Bearer {settings.API_KEY}"}
                response = await client.get(api_url, params=params)

                if response.status_code != 200:
                    logger.error(f"External API error: {response.status_code}")
                    return []

                raw_data = response.json()

                # Standardize the job format for the Sourcing Agent
                standardized_jobs = []
                for job in raw_data.get("results", []):
                    standardized_jobs.append(
                        {
                            "title": job.get("job_title"),
                            "company": job.get("company_name"),
                            "location": job.get("location"),
                            "jd": job.get("description"),  # Crucial for ATS Agent
                            "link": job.get("redirect_url"),
                            "source": "external_api",
                        }
                    )

                span.set_attribute("stream.jobs_returned", len(standardized_jobs))
                return standardized_jobs

        except Exception as e:
            span.record_exception(e)
            logger.error(f"Job stream failure: {str(e)}")
            return []
