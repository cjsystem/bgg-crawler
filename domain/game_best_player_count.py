from dataclasses import dataclass


@dataclass
class GameBestPlayerCount:
    """ゲームベストプレイヤー数エンティティ"""
    player_count: int

    def is_solo_play(self) -> bool:
        """ソロプレイかの判定"""
        return self.player_count == 1

    def is_small_group(self) -> bool:
        """小グループ（2-4人）かの判定"""
        return 2 <= self.player_count <= 4

    def is_large_group(self) -> bool:
        """大グループ（5人以上）かの判定"""
        return self.player_count >= 5