from abc import ABC, abstractmethod


class BaseLLM(ABC):
    @abstractmethod
    async def generate(self, prompt: str, system_instruction: str = "") -> str:
        """Standard interface for all LLM calls."""
        pass
