from dataclasses import dataclass
from typing import Optional


@dataclass
class Genre:
    """ジャンルエンティティ"""
    name: str
    bgg_url: Optional[str] = None

    def __post_init__(self):
        if not self.name or not self.name.strip():
            raise ValueError("Genre name cannot be empty")
        if len(self.name) > 100:
            raise ValueError("Genre name must be 100 characters or less")

    def is_valid(self) -> bool:
        """ジャンル情報の妥当性チェック"""
        return bool(self.name and self.name.strip() and len(self.name) <= 100)