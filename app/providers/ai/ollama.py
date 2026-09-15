import httpx

from app.core.config import settings
from app.providers.ai.base import AIProvider


class OllamaProvider(AIProvider):

    def generate(
        self,
        prompt: str,
        context: dict | None = None,
    ) -> str:

        response = httpx.post(
            f"{settings.ollama_base_url}/api/generate",
            json={
                "model": settings.ollama_model,
                "prompt": prompt,
                "stream": False,
            },
            timeout=120,
        )

        response.raise_for_status()

        return response.json()["response"]
