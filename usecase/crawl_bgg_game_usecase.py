from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod
import logging


class CrawlBGGGameUseCase(ABC):

    @abstractmethod
    def execute(self, pages: int) -> Dict[str, Any]:
        pass