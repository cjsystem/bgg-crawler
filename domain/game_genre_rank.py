from dataclasses import dataclass
from typing import Optional


@dataclass
class GameGenreRank:
    """ゲームジャンルランクエンティティ"""
    genre_id: int
    rank_in_genre: Optional[int] = None

    def __post_init__(self):
        if self.genre_id <= 0:
            raise ValueError("Genre ID must be positive")
        if self.rank_in_genre is not None and self.rank_in_genre <= 0:
            raise ValueError("Rank in genre must be positive")

    def is_valid(self) -> bool:
        """ジャンルランク情報の妥当性チェック"""
        return (self.genre_id > 0
                and (self.rank_in_genre is None or self.rank_in_genre > 0))

    def has_ranking(self) -> bool:
        """ランキングが存在するかの判定"""
        return self.rank_in_genre is not None

    def is_top_ranked(self, threshold: int = 10) -> bool:
        """上位ランクかの判定"""
        return (self.rank_in_genre is not None
                and self.rank_in_genre <= threshold)

    def get_rank_tier(self) -> str:
        """ランクのティア（階層）を取得"""
        if self.rank_in_genre is None:
            return "ランク外"
        elif self.rank_in_genre <= 10:
            return "トップ10"
        elif self.rank_in_genre <= 50:
            return "トップ50"
        elif self.rank_in_genre <= 100:
            return "トップ100"
        else:
            return f"{self.rank_in_genre}位"