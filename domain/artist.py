from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Artist:
    """アーティストエンティティ"""
    name: str
    bgg_url: Optional[str]

    def __post_init__(self):
        if not self.name or not self.name.strip():
            raise ValueError("Artist name cannot be empty")

    def is_valid(self) -> bool:
        """アーティスト情報の妥当性チェック"""
        return bool(self.name and self.name.strip())