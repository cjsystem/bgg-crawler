from abc import ABC, abstractmethod
from typing import Optional, Dict

from domain.game import Game


class HttpClient(ABC):

    @abstractmethod
    def get_html(self,
                 url: str,
                 wait_element: Dict[str, str] = None,
                 additional_wait: int = 0) -> Optional[str]:
        pass