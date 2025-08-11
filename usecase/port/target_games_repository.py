# python
# usecase/port/target_games_repository.py
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List


class TargetGamesRepository(ABC):

    @abstractmethod
    def list_all_bgg_id(self) -> List[int]:
        """target_games テーブル内に存在する全ての bgg_id を list[int] で返す"""
        raise NotImplementedError