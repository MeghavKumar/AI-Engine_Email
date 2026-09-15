from abc import ABC, abstractmethod


class AIProvider(ABC):

    @abstractmethod
    def generate(
        self,
        prompt: str,
        context: dict | None = None,
    ) -> str:
        raise NotImplementedError
