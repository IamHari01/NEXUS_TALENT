import weaviate
from app.core.config import settings

client = weaviate.Client(url=settings.WEAVIATE_URL)


async def query_similar_jobs(title: str, skills: list):
    """
    RAG Retrieval Step: Finds the most relevant job descriptions
    based on the candidate's specific skill vector.
    """
    # Hybrid search: Vectorizes 'skills' + Matches 'title' keywords
    response = (
        client.query.get("Job", ["title", "company", "description"])
        .with_hybrid(
            query=f"{title} {' '.join(skills)}",
            alpha=0.75,  # Heavily weight semantic similarity
        )
        .with_limit(5)
        .do()
    )
    return response["data"]["Get"]["Job"]
