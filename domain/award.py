from dataclasses import dataclass
from typing import Optional


@dataclass
class Award:
    """ゲーム受賞エンティティ"""
    award_name: str
    award_year: int
    award_type: str
    award_category: Optional[str] = None
    bgg_url: Optional[str] = None

    def __post_init__(self):
        if not self.award_name or not self.award_name.strip():
            raise ValueError("Award name cannot be empty")
        if self.award_year < 1900 or self.award_year > 2100:
            raise ValueError("Award year must be between 1900 and 2100")
        if not self.award_type or not self.award_type.strip():
            raise ValueError("Award type cannot be empty")
        if len(self.award_type) > 20:
            raise ValueError("Award type must be 20 characters or less")

    def is_valid(self) -> bool:
        """受賞情報の妥当性チェック"""
        return (self.game_id > 0
                and bool(self.award_name and self.award_name.strip())
                and 1900 <= self.award_year <= 2100
                and bool(self.award_type and self.award_type.strip())
                and len(self.award_type) <= 20)

    def is_winner(self) -> bool:
        """受賞（ノミネートではない）かの判定"""
        return self.award_type.lower() in ['winner', '受賞', 'won']

    def is_nomination(self) -> bool:
        """ノミネートかの判定"""
        return self.award_type.lower() in ['nominee', 'nomination', 'ノミネート']