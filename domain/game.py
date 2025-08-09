from dataclasses import dataclass, field
from typing import Optional
from decimal import Decimal

from domain.artist import Artist
from domain.award import Award
from domain.designer import Designer
from domain.game_genre_rank import GameGenreRank


@dataclass
class Game:
    """ゲームエンティティ"""
    bgg_id: int
    primary_name: str
    japanese_name: Optional[str] = None
    year_released: Optional[int] = None
    image_url: Optional[str] = None
    avg_rating: Optional[Decimal] = None
    ratings_count: Optional[int] = None
    comments_count: Optional[int] = None
    min_players: Optional[int] = None
    max_players: Optional[int] = None
    min_playtime: Optional[int] = None
    max_playtime: Optional[int] = None
    min_age: Optional[int] = None
    weight: Optional[Decimal] = None
    rank_overall: Optional[int] = None
    game_awards: list[Award] = field(default_factory=list)
    game_best_player_counts: list[int] = field(default_factory=list)
    game_designers: list[Designer] = field(default_factory=list)
    game_artists: list[Artist] = field(default_factory=list)
    game_genre_ranks: list[GameGenreRank] = field(default_factory=list)

    def __post_init__(self):
        if self.bgg_id <= 0:
            raise ValueError("BGG ID must be positive")
        if not self.primary_name or not self.primary_name.strip():
            raise ValueError("Primary name cannot be empty")
        if self.year_released is not None and (self.year_released < 1900 or self.year_released > 2100):
            raise ValueError("Year released must be between 1900 and 2100")
        if self.min_players is not None and self.min_players <= 0:
            raise ValueError("Min players must be positive")
        if self.max_players is not None and self.max_players <= 0:
            raise ValueError("Max players must be positive")
        if (self.min_players is not None and self.max_players is not None
                and self.min_players > self.max_players):
            raise ValueError("Min players cannot be greater than max players")

    def is_valid_for_crawling(self) -> bool:
        """クローリング可能かの判定"""
        return self.bgg_id > 0 and bool(self.primary_name and self.primary_name.strip())

    def is_multiplayer_game(self) -> bool:
        """マルチプレイヤーゲームかの判定"""
        return self.max_players is not None and self.max_players > 1

    def get_player_range_text(self) -> str:
        """プレイヤー数の範囲を文字列で取得"""
        if self.min_players is None or self.max_players is None:
            return "不明"
        if self.min_players == self.max_players:
            return f"{self.min_players}人"
        return f"{self.min_players}-{self.max_players}人"

    def get_playtime_range_text(self) -> str:
        """プレイ時間の範囲を文字列で取得"""
        if self.min_playtime is None or self.max_playtime is None:
            return "不明"
        if self.min_playtime == self.max_playtime:
            return f"{self.min_playtime}分"
        return f"{self.min_playtime}-{self.max_playtime}分"

    def is_highly_rated(self, threshold: float = 7.0) -> bool:
        """高評価ゲームかの判定"""
        return self.avg_rating is not None and float(self.avg_rating) >= threshold

    def has_sufficient_ratings(self, min_ratings: int = 100) -> bool:
        """十分な評価数があるかの判定"""
        return self.ratings_count is not None and self.ratings_count >= min_ratings