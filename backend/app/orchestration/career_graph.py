from typing import TypedDict, List, Optional, Dict, Any
from langgraph.graph import StateGraph, START, END
from app.agents.sourcing_agent import sourcing_agent
from app.agents.ats_agent import ats_agent
from app.agents.gap_agent import gap_agent
from app.agents.pathfinder_agent import pathfinder_agent
from app.services.resume_parser import parse_resume_pdf  # Integrated Parser
from app.api.schemas import ResumeData
from app.core.observability import tracer


# 1. Define the Industry-Grade State Schema
class AgentState(TypedDict):
    # Inputs
    resume_bytes: bytes  # Raw input from FastAPI
    job_title: str
    location: str

    # Structured Internal Data
    resume_object: Optional[ResumeData]  # Structured & Sanitized
    jobs: List[Dict[str, Any]]

    # Results
    score: float
    missing_skills: Dict[str, Any]
    learning_path: List[Dict[str, Any]]
    error: Optional[str]


# 2. Dedicated Parsing Node
async def parser_node(state: AgentState):
    """Initial Security & Parsing Layer."""
    try:
        resume_obj = await parse_resume_pdf(state["resume_bytes"])
        return {"resume_object": resume_obj}
    except Exception as e:
        return {"error": f"Parsing failed: {str(e)}"}


# 3. Logic for Conditional Routing
def should_analyze_gaps(state: AgentState):
    """Router: Decisions based on ATS performance."""
    if state.get("score", 0) < 85:
        return "gap"
    return "path"


# 4. Build the Compiled Graph
def create_career_intelligence_graph():
    workflow = StateGraph(AgentState)

    # Add Nodes
    workflow.add_node("parse", parser_node)  # Entry Security/Sanitization Node
    workflow.add_node("source", sourcing_agent)
    workflow.add_node("score", ats_agent)
    workflow.add_node("gap", gap_agent)
    workflow.add_node("path", pathfinder_agent)

    # Define Workflow Logic
    workflow.add_edge(START, "parse")  # Ensure parse happens first
    workflow.add_edge("parse", "source")
    workflow.add_edge("source", "score")

    # Conditional Routing
    workflow.add_conditional_edges(
        "score", should_analyze_gaps, {"gap": "gap", "path": "path"}
    )

    workflow.add_edge("gap", "path")
    workflow.add_edge("path", END)

    return workflow.compile()


career_engine = create_career_intelligence_graph()


async def run_graph(input_data: Dict[str, Any]):
    """
    Entry point to execute the Agentic Workflow.
    """
    with tracer.start_as_current_span("CareerGraph_Workflow") as span:
        span.set_attribute("flow.type", "multi_agent_matchmaking")

        try:
            initial_state = {
                "resume_bytes": input_data.get("resume_bytes"),
                "job_title": input_data.get("job_title"),
                "location": input_data.get("location"),
                "jobs": [],
                "score": 0.0,
                "resume_object": None,  # To be filled by 'parse' node
            }

            result = await career_engine.ainvoke(initial_state)

            if result.get("error"):
                span.set_status("error", result["error"])

            return result

        except Exception as e:
            span.record_exception(e)
            span.set_status("error", str(e))
            return {"error": str(e)}
