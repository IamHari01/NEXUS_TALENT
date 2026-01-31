from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any

# --- Request Models ---


class AnalyzeRequest(BaseModel):
    """The initial payload sent by the frontend."""

    resume: str = Field(
        ..., description="The full text extracted from the user's resume."
    )
    job_title: str = Field(..., description="The target role the user is applying for.")
    location: str = Field(default="Remote", description="Desired work location.")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "resume": "John Doe, Senior Python Developer with 5 years experience...",
                "job_title": "Senior AI Engineer",
                "location": "San Francisco, CA",
            }
        }
    )


# --- Internal State Model (for LangGraph) ---


class AgentState(BaseModel):
    """
    The shared state object that flows through the LangGraph agents.
    This matches the expected input/output of your run_graph function.
    """

    resume: str
    job_title: str
    location: str
    jobs: List[Dict[str, Any]] = []
    score: float = 0.0
    missing_skills: Dict[str, Any] = {}
    learning_path: List[Dict[str, Any]] = []
    error: Optional[str] = None


# --- Response Models ---


class JobMatch(BaseModel):
    title: str
    company: str
    link: str
    score: float


class CareerAnalysisResponse(BaseModel):
    """The final response returned to the frontend."""

    score: float = Field(..., description="Overall ATS match score (0-100).")
    top_jobs: List[JobMatch]
    missing_skills: Dict[str, Any]
    learning_path: List[Dict[str, Any]]
    insights: Optional[str] = None
