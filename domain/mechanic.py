from dataclasses import dataclass
from typing import Optional


@dataclass
class Mechanic:
    """メカニクスエンティティ"""
    name: str
    bgg_url: Optional[str] = None

    def __post_init__(self):
        if not self.name or not self.name.strip():
            raise ValueError("Mechanic name cannot be empty")
        if self.game_count is not None and self.game_count < 0:
            raise ValueError("Game count cannot be negative")

    def is_valid(self) -> bool:
        """メカニクス情報の妥当性チェック"""
        return bool(self.name and self.name.strip())

    def increment_game_count(self) -> None:
        """ゲーム数をインクリメント"""
        if self.game_count is None:
            self.game_count = 1
        else:
            self.game_count += 1