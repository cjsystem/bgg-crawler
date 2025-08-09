from dataclasses import dataclass


@dataclass
class GameBestPlayerCount:
    """ゲームベストプレイヤー数エンティティ"""
    player_count: int

    def __post_init__(self):
        if self.game_id <= 0:
            raise ValueError("Game ID must be positive")
        if self.player_count <= 0:
            raise ValueError("Player count must be positive")
        if self.player_count > 20:  # 現実的な上限
            raise ValueError("Player count seems unrealistic (max 20)")

    def is_valid(self) -> bool:
        """ベストプレイヤー数情報の妥当性チェック"""
        return (self.game_id > 0
                and self.player_count > 0
                and self.player_count <= 20)

    def is_solo_play(self) -> bool:
        """ソロプレイかの判定"""
        return self.player_count == 1

    def is_small_group(self) -> bool:
        """小グループ（2-4人）かの判定"""
        return 2 <= self.player_count <= 4

    def is_large_group(self) -> bool:
        """大グループ（5人以上）かの判定"""
        return self.player_count >= 5