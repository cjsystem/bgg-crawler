from abc import ABC, abstractmethod
from typing import Optional

from domain.game import Game


class BGGGameParserService(ABC):
    """BGGゲームHTMLパーサーのインターフェース"""

    @abstractmethod
    def parse_game(self, bgg_id: int) -> Optional[Game]:
        """
        BGGからゲーム情報を取得してパース

        Args:
            bgg_id (int): BGGのゲームID

        Returns:
            Optional[Game]: パースされたゲームエンティティ。取得失敗時はNone

        Raises:
            ValueError: 無効なbgg_idの場合
            BGGParseException: パース処理でエラーが発生した場合
        """
        pass