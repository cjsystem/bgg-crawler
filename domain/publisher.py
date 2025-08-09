from dataclasses import dataclass
from typing import Optional


@dataclass
class Publisher:
    """パブリッシャーエンティティ"""
    name: str
    bgg_url: Optional[str] = None

    def __post_init__(self):
        if not self.name or not self.name.strip():
            raise ValueError("Publisher name cannot be empty")

    def is_valid(self) -> bool:
        """パブリッシャー情報の妥当性チェック"""
        return bool(self.name and self.name.strip())