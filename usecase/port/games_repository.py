# python
# infra/db/repository/games_repository.py
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Dict

from domain.game import Game


class GamesRepository(ABC):
    """Gameエンティティの一括登録/更新用リポジトリ"""

    @abstractmethod
    def bulk_create_games(self, game_list: List[Game]) -> Dict[int, int]:
        """ゲーム群を一括UPSERTし、関連のテーブル・紐付けも更新する
        Args:
            game_list: ドメインのGameエンティティ一覧（非リレーション＋各クレジット/ランク/人数を含む）

        Returns:
            Dict[int, int]: bgg_id -> games.id のマッピング
        """
        raise NotImplementedError

    @abstractmethod
    def list_all_bgg_id(self) -> List[int]:
        """games テーブル内に存在する全ての bgg_id を list[int] で返す"""
        raise NotImplementedError