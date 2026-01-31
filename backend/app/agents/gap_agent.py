import logging
import json
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from app.core.observability import tracer
from app.llm.router import LLMRouter  # Your custom hybrid router


# 1. Define the Structured Response Schema
class GapAnalysisResponse(BaseModel):
    """Schema for high-fidelity structured output from the LLM"""

    hard_skills: List[str] = Field(
        description="Missing technical skills like Python, AWS, etc."
    )
    soft_skills: List[str] = Field(
        description="Missing soft skills like Leadership or Agile."
    )
    required_experience: str = Field(description="Specific experience gaps found.")
    priority_focus: str = Field(
        description="The single most critical skill to learn first."
    )


# Initialize the global router
llm_router = LLMRouter()


async def gap_agent(state: Dict[str, Any]):
    """
    Industry-grade Gap Analysis Agent.
    Orchestrates Hybrid LLM routing with forced Pydantic structured output.
    """
    resume = state.get("resume", "")
    jd = state.get("job", {}).get("jd", "")
    score = state.get("score", 0)

    # Performance Optimization: Early exit
    if score >= 90:
        state["missing_skills"] = None
        state["recommendation_status"] = "Perfect Match"
        return state

    with tracer.start_as_current_span("GapAnalysisAgent") as span:
        span.set_attribute("agent.type", "gap_analyzer")
        span.set_attribute("ats.score_incoming", score)

        try:
            # 2. Build the Professional Analysis Prompt
            prompt = f"""
            Analyze the following Resume against the Job Description. 
            Identify the delta (gaps) and prioritize what the candidate must learn.
            
            RESUME:
            {resume[:3000]}
            
            JOB DESCRIPTION:
            {jd[:3000]}
            """

            system_instruction = (
                "You are an expert ATS auditor. You must output only valid JSON "
                "matching this schema: "
                + json.dumps(GapAnalysisResponse.model_json_schema())
            )

            # 3. Execution via the Router (Priority=True uses Gemini, Fallback to Ollama)
            with tracer.start_as_current_span("llm_reasoning_step") as llm_span:
                raw_response = await llm_router.run(
                    prompt=prompt, system_instruction=system_instruction, priority=True
                )

                # 4. Parse & Validate Structured Output
                # Use Pydantic to ensure the 'contract' with the frontend is safe
                parsed_data = GapAnalysisResponse.model_validate_json(raw_response)

                llm_span.set_attribute("gap.count", len(parsed_data.hard_skills))

            # Update Global State
            state["missing_skills"] = parsed_data.model_dump()
            state["recommendation_status"] = "Gaps Identified"
            state["priority_skill"] = parsed_data.priority_focus

        except Exception as e:
            logging.error(f"Gap Analysis Agent Failure: {e}")
            span.record_exception(e)
            span.set_status("error", "LLM Processing Failure")
            state["missing_skills"] = {}
            state["error"] = "Pathfinder engine is currently recalculating."

        return state
