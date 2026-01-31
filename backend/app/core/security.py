import re
import html
from fastapi import HTTPException, status


class SecurityManager:
    """
    Centralized security logic for sanitizing resume inputs
    and managing API protection.
    """

    @staticmethod
    def sanitize_input(text: str) -> str:
        """
        Cleans raw resume or JD text to prevent XSS or prompt injection artifacts.
        """
        if not text:
            return ""
        # 1. Strip HTML tags
        clean_text = html.escape(text)
        # 2. Remove non-printable characters
        clean_text = "".join(char for char in clean_text if char.isprintable())
        # 3. Limit whitespace to prevent token bloat
        clean_text = re.sub(r"\s+", " ", clean_text).strip()

        return clean_text

    @staticmethod
    def validate_file_size(file_size: int, max_mb: int = 5):
        """Ensures resume uploads don't crash the server (DoS protection)."""
        if file_size > max_mb * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Resume file too large. Max size is {max_mb}MB.",
            )


# Shared security utility
security = SecurityManager()
