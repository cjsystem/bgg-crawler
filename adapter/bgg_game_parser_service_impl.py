from typing import Optional

from adapter.port.http_client import HttpClient
from domain.game import Game
from usecase.port.bgg_game_parser_service import BGGGameParserService


class BGGGameParserServiceImpl(BGGGameParserService):
    """BGGゲームHTMLパーサーの実装"""

    def __init__(self, http_client: HttpClient, timeout: int = 30, user_agent: str = None):
        """
        Args:
            timeout (int): HTTPリクエストのタイムアウト秒数
            user_agent (str): User-Agentヘッダー
        """
        self._http_client = http_client
        self.timeout = timeout
        self.user_agent = user_agent or "BGGGameCrawler/1.0"

    def parse_game(self, bgg_id: int) -> Optional[Game]:
        """BGGからゲーム情報を取得してパース"""
        try:
            # 入力値検証
            self._validate_bgg_id(bgg_id)

            # HTMLを取得
            game_main_html_content = self._get_bgg_game_html(bgg_id)
            if not game_main_html_content:
                raise BGGFetchException(f"Failed to fetch game {bgg_id}")

            return None

        except Exception as e:
            # ログ出力（実際の実装ではloggerを使用）
            print(f"Error parsing game {bgg_id}: {str(e)}")
            raise BGGParseException(f"Failed to parse game {bgg_id}") from e

    def _validate_bgg_id(self, bgg_id: int) -> None:
        """BGG IDの検証"""
        if not isinstance(bgg_id, int) or bgg_id <= 0:
            raise ValueError("BGG ID must be a positive integer")

    def _get_bgg_game_html(self, bgg_id: int) -> Optional[str]:
        """
        BGGゲームページのHTMLを取得（特化メソッド）

        Args:
            bgg_id (int): BGGのゲームID

        Returns:
            Optional[str]: HTMLソース。エラー時はNone
        """
        url = f"https://boardgamegeek.com/boardgame/{bgg_id}"
        wait_element = {"by": "class_name", "value": "summary"}

        html_content = self._http_client.get_html(url, wait_element, additional_wait=2)

        return html_content


class BGGParseException(Exception):
    """BGGパース処理の例外"""
    pass


class BGGFetchException(Exception):
    """BGG HTML取得の例外"""
    pass