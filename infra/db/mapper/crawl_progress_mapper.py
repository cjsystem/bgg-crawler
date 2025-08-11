# python
# infra/db/mapper/crawl_progress_mapper.py
from __future__ import annotations

from typing import List, Optional
import datetime
import logging
from sqlalchemy.orm import Session

from infra.db.models import CrawlProgress


class CrawlProgressMapper:
    """crawl_progress テーブル用マッパー（外部Session注入方式）"""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    # ---------- Query ----------

    def get_by_id(self, id_: int, session: Session) -> Optional[CrawlProgress]:
        return session.query(CrawlProgress).filter(CrawlProgress.id == id_).first()

    def get_by_batch_id(self, batch_id: str, session: Session) -> Optional[CrawlProgress]:
        return session.query(CrawlProgress).filter(CrawlProgress.batch_id == batch_id).first()

    def list_recent(self, session: Session, limit: int = 20) -> List[CrawlProgress]:
        return (
            session.query(CrawlProgress)
            .order_by(CrawlProgress.started_at.desc())
            .limit(limit)
            .all()
        )

    # ---------- Create / Upsert ----------

    def create(
        self,
        session: Session,
        batch_id: str,
        total_games: int = 0,
        batch_type: Optional[str] = None,
        started_at: Optional[datetime.datetime] = None,
    ) -> CrawlProgress:
        """新規作成（既存batch_idがある場合は例外が発生）"""
        entity = CrawlProgress(
            batch_id=batch_id,
            total_games=int(total_games),
            batch_type=batch_type or "manual",
            started_at=started_at,  # None の場合はサーバデフォルト
        )
        session.add(entity)
        session.flush()  # id を取得
        return entity

    def get_or_create(
        self,
        session: Session,
        batch_id: str,
        total_games: int = 0,
        batch_type: Optional[str] = None,
    ) -> CrawlProgress:
        """batch_id で取得。なければ作成して返す"""
        existing = self.get_by_batch_id(batch_id, session)
        if existing:
            return existing
        return self.create(
            session=session,
            batch_id=batch_id,
            total_games=total_games,
            batch_type=batch_type,
        )

    # ---------- Update fields ----------

    def set_total_games(self, session: Session, batch_id: str, total_games: int) -> None:
        """total_games を更新"""
        row = self.get_by_batch_id(batch_id, session)
        if not row:
            raise ValueError(f"batch_id '{batch_id}' not found")
        row.total_games = int(total_games)

    def increment_processed(self, session: Session, batch_id: str, inc: int = 1) -> None:
        """processed_games を加算"""
        row = self.get_by_batch_id(batch_id, session)
        if not row:
            raise ValueError(f"batch_id '{batch_id}' not found")
        row.processed_games = (row.processed_games or 0) + int(inc)

    def increment_failed(self, session: Session, batch_id: str, inc: int = 1) -> None:
        """failed_games を加算"""
        row = self.get_by_batch_id(batch_id, session)
        if not row:
            raise ValueError(f"batch_id '{batch_id}' not found")
        row.failed_games = (row.failed_games or 0) + int(inc)

    def set_error_message(self, session: Session, batch_id: str, message: Optional[str]) -> None:
        """error_message を設定（None 可）"""
        row = self.get_by_batch_id(batch_id, session)
        if not row:
            raise ValueError(f"batch_id '{batch_id}' not found")
        row.error_message = message

    def mark_completed(self, session: Session, batch_id: str, error_message: Optional[str] = None) -> None:
        """完了時刻を設定し、必要ならエラーメッセージも更新"""
        row = self.get_by_batch_id(batch_id, session)
        if not row:
            raise ValueError(f"batch_id '{batch_id}' not found")
        row.completed_at = datetime.datetime.utcnow()
        if error_message is not None:
            row.error_message = error_message