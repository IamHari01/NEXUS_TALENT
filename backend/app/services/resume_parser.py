import logging
from io import BytesIO
from pypdf import PdfReader
import instructor
import google.generativeai as genai

from app.api.schemas import ResumeData
from app.core.security import security  # Professional sanitization
from app.core.config import settings  # Pydantic settings
from app.core.observability import tracer  # Real-time tracing

logger = logging.getLogger("nexus-talent")

# Patch the Gemini client for structured outputs
client = instructor.from_gemini(
    client=genai.GenerativeModel(model_name="gemini-1.5-flash"),
    mode=instructor.Mode.GEMINI_JSON,
)


async def parse_resume_pdf(file_bytes: bytes) -> ResumeData:
    """
    Industry-grade structured PDF parser.
    Combines Security Guarding -> Sanitization -> LLM Extraction.
    """
    with tracer.start_as_current_span("secure_resume_parsing") as span:
        try:
            # 1. Security Check: File Size Validation
            # Protects your infrastructure from DoS attacks
            security.validate_file_size(len(file_bytes))

            # 2. Safe Extraction
            # Uses BytesIO to handle files in-memory (Standard for Cloud/Docker)
            reader = PdfReader(BytesIO(file_bytes))
            raw_text = "".join([page.extract_text() or "" for page in reader.pages])

            # 3. Sanitization
            # Neutralizes malicious strings and artifacts before LLM processing
            sanitized_text = security.sanitize_input(raw_text)

            if not sanitized_text:
                raise ValueError("Could not extract valid text from the provided PDF.")

            span.set_attribute("resume.char_count", len(sanitized_text))

            # 4. Structured Extraction via Instructor
            # Converts raw text into a validated Pydantic ResumeData object
            resume_object = await client.chat.completions.create(
                response_model=ResumeData,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional resume parser. Extract details accurately into JSON.",
                    },
                    {
                        "role": "user",
                        "content": f"Extract details from this resume: {sanitized_text[:12000]}",
                    },
                ],
            )

            logger.info("Resume successfully parsed and structured.")
            return resume_object

        except Exception as e:
            span.record_exception(e)
            span.set_status("error", str(e))
            logger.error(f"Structured parsing failed: {str(e)}")
            raise e
