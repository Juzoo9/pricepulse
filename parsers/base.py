from abc import ABC, abstractmethod


class BaseParser(ABC):

    @abstractmethod
    async def parse(self, url: str) -> dict:
        ...

    @abstractmethod
    async def is_valid(self, url: str) -> bool:
        ...