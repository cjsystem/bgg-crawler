from dataclasses import dataclass
from typing import Optional


@dataclass
class Category:
    """カテゴリエンティティ"""
    name: str
    bgg_url: Optional[str]

    def __post_init__(self):
        if not self.name or not self.name.strip():
            raise ValueError("Category name cannot be empty")

    def is_valid(self) -> bool:
        """カテゴリ情報の妥当性チェック"""
        return bool(self.name and self.name.strip())