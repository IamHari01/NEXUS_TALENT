import os
import google.generativeai as genai
from app.llm.base import BaseLLM
from app.core.observability import tracer


class GeminiLLM(BaseLLM):
    def __init__(self):
        # Gemini 1.5 Flash is currently free (15 RPM / 1M TPM)
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model_name = "gemini-1.5-flash"

    async def generate(self, prompt: str, system_instruction: str = "") -> str:
        with tracer.start_as_current_span("gemini_flash_call") as span:
            span.set_attribute("llm.model", self.model_name)
            model = genai.GenerativeModel(
                model_name=self.model_name, system_instruction=system_instruction
            )
            # asynchronous generation for FastAPI performance
            response = await model.generate_content_async(
                prompt, generation_config={"response_mime_type": "application/json"}
            )
            return response.text
