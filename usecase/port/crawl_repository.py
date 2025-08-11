# python
# usecase/port/crawl_repository.py
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional
import datetime
from sqlalchemy.orm import Session

from infra.db.models import CrawlProgress


class CrawlRepository(ABC):

    @abstractmethod
    def create(
        self,
        session: Session,
        batch_id: str,
        total_games: int = 0,
        batch_type: Optional[str] = None,
        started_at: Optional[datetime.datetime] = None,
    ) -> CrawlProgress:
        """crawl_progress に1件作成して返す"""
        raise NotImplementedError