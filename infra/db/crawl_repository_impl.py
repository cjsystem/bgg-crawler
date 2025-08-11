# python
# infra/db/repository/crawl_repository_impl.py
from __future__ import annotations

from typing import Optional
import datetime
from sqlalchemy.orm import Session

from infra.db.mapper.crawl_progress_mapper import CrawlProgressMapper
from infra.db.models import CrawlProgress
from usecase.port.crawl_repository import CrawlRepository


class CrawlRepositoryImpl(CrawlRepository):
    def __init__(self) -> None:
        self.mapper = CrawlProgressMapper()

    def create(
        self,
        session: Session,
        batch_id: str,
        total_games: int = 0,
        batch_type: Optional[str] = None,
        started_at: Optional[datetime.datetime] = None,
    ) -> CrawlProgress:
        return self.mapper.create(
            session=session,
            batch_id=batch_id,
            total_games=total_games,
            batch_type=batch_type,
            started_at=started_at,
        )