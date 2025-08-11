# python
# target_games_mapper.py
from typing import List, Optional
from sqlalchemy.orm import Session

from ..models import TargetGames


class TargetGamesMapper:
    """target_games テーブル用マッパー（外部Session注入方式）"""

    def __init__(self) -> None:
        # 状態は持たない（必要ならDIで設定を受け取る）
        pass

    def list_all(self, session: Session) -> List[TargetGames]:
        """全ターゲットゲームを取得（ページングなし）"""
        return (
            session.query(TargetGames)
            .order_by(TargetGames.created_at.asc())
            .all()
        )

    def list_all_bgg_ids(self, session: Session) -> List[int]:
        """全ターゲットゲームのbgg_idだけを取得"""
        rows = (
            session.query(TargetGames.bgg_id)
            .order_by(TargetGames.created_at.asc())
            .all()
        )
        # rows は List[Tuple[int]] なので一次元配列に変換
        return [row[0] for row in rows]

    def get_by_bgg_id(self, bgg_id: int, session: Session) -> Optional[TargetGames]:
        """bgg_idで1件取得"""
        return (
            session.query(TargetGames)
            .filter(TargetGames.bgg_id == bgg_id)
            .first()
        )