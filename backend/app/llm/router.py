from app.llm.gemini import GeminiLLM
from app.llm.ollama import OllamaLLM
from app.core.observability import tracer
import logging


class LLMRouter:
    def __init__(self):
        self.gemini = GeminiLLM()
        self.ollama = OllamaLLM()
        self.logger = logging.getLogger(__name__)

    async def run(
        self, prompt: str, system_instruction: str = "", priority: bool = False
    ) -> str:
        with tracer.start_as_current_span("llm_router_execution") as span:
            # High priority (Gap Analysis/Pathfinding) uses Gemini Free Tier
            if priority:
                try:
                    return await self.gemini.generate(prompt, system_instruction)
                except Exception as e:
                    self.logger.warning(
                        f"Gemini Free Limit hit: {e}. Falling back to Ollama."
                    )
                    span.set_attribute("llm.fallback", True)

            # Default to local Ollama for everything else
            return await self.ollama.generate(prompt, system_instruction)
