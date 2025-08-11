# target_games_mapper.py
from typing import List, Optional

from ..base.db_mapper_base import DBMapperBase
from ..models import TargetGames


class TargetGamesMapper(DBMapperBase[TargetGames]):
    """target_games テーブル用マッパー"""

    def __init__(self):
        super().__init__(TargetGames)

    def list_all(self) -> List[TargetGames]:
        """全ターゲットゲームを取得（ページングなし）"""
        session = self.get_session()
        try:
            return session.query(TargetGames).order_by(TargetGames.created_at.asc()).all()
        finally:
            session.close()

    def list_all_bgg_ids(self) -> List[int]:
        """全ターゲットゲームのbgg_idだけを取得"""
        session = self.get_session()
        try:
            rows = session.query(TargetGames.bgg_id).order_by(TargetGames.created_at.asc()).all()
            # rows は List[Tuple[int]] なので一次元配列に変換
            return [row[0] for row in rows]
        finally:
            session.close()

    def get_by_bgg_id(self, bgg_id: int) -> Optional[TargetGames]:
        """bgg_idで1件取得"""
        session = self.get_session()
        try:
            return session.query(TargetGames).filter(TargetGames.bgg_id == bgg_id).first()
        finally:
            session.close()