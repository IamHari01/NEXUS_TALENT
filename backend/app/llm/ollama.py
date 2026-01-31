import httpx
import os
from app.llm.base import BaseLLM
from app.core.observability import tracer


class OllamaLLM(BaseLLM):
    def __init__(self, model: str = "llama3"):
        self.model = model
        self.url = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")

    async def generate(self, prompt: str, system_instruction: str = "") -> str:
        with tracer.start_as_current_span("ollama_local_call") as span:
            span.set_attribute("llm.model", self.model)
            full_prompt = f"{system_instruction}\n\n{prompt}"

            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    self.url,
                    json={"model": self.model, "prompt": full_prompt, "stream": False},
                )
                return response.json().get("response", "")
