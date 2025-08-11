# python
# infra/db/repository/target_games_repository_impl.py
from __future__ import annotations

from typing import List

from infra.db.base.db import session_scope
from infra.db.mapper.target_games_mapper import TargetGamesMapper
from usecase.port.target_games_repository import TargetGamesRepository


class TargetGamesRepositoryImpl(TargetGamesRepository):
    def __init__(self) -> None:
        self.target_games = TargetGamesMapper()

    def list_all_bgg_id(self) -> List[int]:
        """target_games テーブル内に存在する全ての bgg_id を list[int] で返す"""
        with session_scope() as session:
            return self.target_games.list_all_bgg_ids(session)