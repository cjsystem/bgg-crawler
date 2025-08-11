import logging
import re
from typing import Optional
from bs4 import BeautifulSoup
from adapter.service.bgg_game_main_parser import BGGGameMainParser
from adapter.service.bgg_game_credits_parser import BGGGameCreditsParser
from adapter.port.http_client import HttpClient
from domain.game import Game
from usecase.port.bgg_game_parser_service import BGGGameParserService


class BGGGameParserServiceImpl(BGGGameParserService):
    """BGGゲームHTMLパーサーの実装"""

    def __init__(self, http_client: HttpClient, timeout: int = 30, user_agent: str = None):
        """
        Args:
            http_client: HTTPクライアント
            timeout (int): HTTPリクエストのタイムアウト秒数
            user_agent (str): User-Agentヘッダー
        """
        self._http_client = http_client
        self.timeout = timeout
        self.user_agent = user_agent or "BGGGameCrawler/1.0"
        self.logger = logging.getLogger(__name__)

    def parse_ranking_ids(self, page_num: int) -> list[int]:
        """
        BGGランキング（Browse Board Games）ページからbgg_id一覧を取得する

        Args:
            page_num (int): ページ番号（1始まり）

        Returns:
            list[int]: 抽出したbgg_idのリスト（昇順・重複除去）
        """

        # 入力検証
        if not isinstance(page_num, int) or page_num <= 0:
            raise ValueError("page_num must be a positive integer (1-based)")

        # ページURLを構築
        url = f"https://boardgamegeek.com/browse/boardgame/page/{page_num}"

        # ランキングテーブルの行を待機して安定化
        wait_element = {"by": "css_selector", "value": "tr[id^='row_']"}

        # HTML取得
        html_content = self._http_client.get_html(url, wait_element, additional_wait=2)
        if not html_content:
            self.logger.warning(f"Failed to fetch ranking page HTML: {url}")
            return []

        # HTML解析
        soup = BeautifulSoup(html_content, "html.parser")
        ids: set[int] = set()

        # 1) サムネイル列・タイトル列のリンクから抽出（最も確実）
        # 例: <a href="/boardgame/342942/ark-nova">...</a>
        for a in soup.select(
                "td.collection_thumbnail a[href^='/boardgame/'], "
                "td.collection_objectname a[href^='/boardgame/']"
        ):
            href = a.get("href", "")
            m = re.match(r"^/boardgame/(\d+)(?:/|$)", href)
            if m:
                ids.add(int(m.group(1)))

        # 2) フォールバック: 広告用divのidから抽出（例: id='aad_thing_342942_textwithprices__'）
        for div in soup.select("div[id^='aad_thing_'][id$='_textwithprices__']"):
            div_id = div.get("id", "")
            m = re.match(r"^aad_thing_(\d+)_", div_id)
            if m:
                ids.add(int(m.group(1)))

        result = sorted(ids)
        self.logger.info(f"Extracted {len(result)} bgg_ids from ranking page {page_num}")
        return result

    def parse_game(self, bgg_id: int) -> Optional[Game]:
        """BGGからゲーム情報を取得してパース"""
        try:
            # 入力値検証
            self._validate_bgg_id(bgg_id)

            # メインページHTMLを取得
            game_main_html_content = self._get_bgg_game_html(bgg_id)
            if not game_main_html_content:
                raise BGGFetchException(f"Failed to fetch game {bgg_id}")

            # メインページからクレジットURLを抽出
            credits_url = self._extract_credits_url_from_main_html(game_main_html_content)
            if not credits_url:
                self.logger.warning(f"Credits URL not found in main page for game {bgg_id}")

            # メインページからゲーム基本情報をパース
            game = BGGGameMainParser.parse_game_from_html(game_main_html_content, bgg_id)
            if not game:
                raise BGGParseException(f"Failed to parse main game data for {bgg_id}")

            # クレジットページHTMLを取得（URLが抽出できた場合のみ）
            if credits_url:
                credit_html_content = self._get_bgg_game_credits_html_by_url(credits_url)
                if not credit_html_content:
                    self.logger.warning(f"Failed to fetch credits for game {bgg_id}, continuing with main data only")
                    return game

                # クレジット情報をパースして統合
                credits_parser = BGGGameCreditsParser()
                credits_data = credits_parser.parse_credits_html(credit_html_content)

                # クレジット情報をゲームオブジェクトに統合
                self._integrate_credits_into_game(game, credits_data)

                self.logger.info(f"Successfully parsed game {bgg_id} with credits")
            else:
                self.logger.info(f"Parsed game {bgg_id} without credits (URL not found)")

            return game

        except Exception as e:
            # ログ出力
            self.logger.error(f"Error parsing game {bgg_id}: {str(e)}")
            raise BGGParseException(f"Failed to parse game {bgg_id}") from e

    def _extract_credits_url_from_main_html(self, html_content: str) -> Optional[str]:
        """
        メインページHTMLからクレジットページのURLを抽出

        Args:
            html_content: メインページのHTML内容

        Returns:
            Optional[str]: クレジットページURL（見つからない場合はNone）
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')

            # ui-sref="geekitem.credits" を含むaタグを探す
            credits_link = soup.find('a', {'ui-sref': 'geekitem.credits'})

            if credits_link and credits_link.get('href'):
                href = credits_link.get('href')
                # 相対URLの場合は完全URLに変換
                if href.startswith('/'):
                    full_url = f"https://boardgamegeek.com{href}"
                else:
                    full_url = href

                self.logger.info(f"Extracted credits URL: {full_url}")
                return full_url

            # フォールバック：href属性で credits を含むリンクを探す
            credits_link = soup.find('a', href=lambda href: href and 'credits' in href)
            if credits_link:
                href = credits_link.get('href')
                if href.startswith('/'):
                    full_url = f"https://boardgamegeek.com{href}"
                else:
                    full_url = href

                self.logger.info(f"Extracted credits URL (fallback): {full_url}")
                return full_url

            self.logger.warning("Credits link not found in main HTML")
            return None

        except Exception as e:
            self.logger.error(f"Error extracting credits URL: {str(e)}")
            return None

    def _validate_bgg_id(self, bgg_id: int) -> None:
        """BGG IDの検証"""
        if not isinstance(bgg_id, int) or bgg_id <= 0:
            raise ValueError("BGG ID must be a positive integer")

    def _get_bgg_game_html(self, bgg_id: int) -> Optional[str]:
        """
        Args:
            bgg_id (int): BGGのゲームID

        Returns:
            Optional[str]: HTMLソース。エラー時はNone
        """
        url = f"https://boardgamegeek.com/boardgame/{bgg_id}"
        wait_element = {"by": "class_name", "value": "summary"}

        html_content = self._http_client.get_html(url, wait_element, additional_wait=2)

        return html_content

    def _get_bgg_game_credits_html_by_url(self, credits_url: str) -> Optional[str]:
        """
        指定されたURLからクレジットページのHTMLを取得

        Args:
            credits_url (str): クレジットページの完全URL

        Returns:
            Optional[str]: HTMLソース。エラー時はNone
        """
        # クレジットページ用の待機要素
        wait_element = {"by": "class_name", "value": "outline-item"}

        html_content = self._http_client.get_html(
            credits_url,
            wait_element,
            additional_wait=3  # クレジットページは少し長めに待機
        )

        if html_content:
            self.logger.info(f"Successfully fetched credits HTML from: {credits_url}")
        else:
            self.logger.warning(f"Failed to fetch credits HTML from: {credits_url}")

        return html_content

    def _get_bgg_game_credits_html(self, bgg_id: int) -> Optional[str]:
        """
        従来の方式でクレジットページHTMLを取得（フォールバック用）

        Args:
            bgg_id (int): BGGのゲームID

        Returns:
            Optional[str]: HTMLソース。エラー時はNone
        """
        url = f"https://boardgamegeek.com/boardgame/{bgg_id}/credits"

        # クレジットページ用の待機要素
        wait_element = {"by": "class_name", "value": "outline-item"}

        html_content = self._http_client.get_html(
            url,
            wait_element,
            additional_wait=3
        )

        return html_content

    def _integrate_credits_into_game(self, game: Game, credits_data: dict) -> None:
        """
        クレジット情報をゲームオブジェクトに統合する

        Args:
            game: 統合対象のGameオブジェクト
            credits_data: BGGGameCreditsParser.parse_credits_htmlの戻り値
        """
        try:
            # 日本語名の統合（メインページで取得できていない場合のみ）
            if not game.japanese_name and credits_data.get('japanese_name'):
                game.japanese_name = credits_data['japanese_name']
                self.logger.info(f"Added Japanese name from credits: {game.japanese_name}")

            # デザイナー情報の統合
            if credits_data.get('designers'):
                game.designers = credits_data['designers']
                self.logger.info(f"Added {len(game.designers)} designers")

            # アーティスト情報の統合
            if credits_data.get('artists'):
                game.artists = credits_data['artists']
                self.logger.info(f"Added {len(game.artists)} artists")

            # パブリッシャー情報の統合
            if credits_data.get('publishers'):
                game.publishers = credits_data['publishers']
                self.logger.info(f"Added {len(game.publishers)} publishers")

            # カテゴリ情報の統合
            if credits_data.get('categories'):
                game.categories = credits_data['categories']
                self.logger.info(f"Added {len(game.categories)} categories")

            # メカニクス情報の統合
            if credits_data.get('mechanics'):
                game.mechanics = credits_data['mechanics']
                self.logger.info(f"Added {len(game.mechanics)} mechanics")

            # 統合結果のサマリーをログ出力
            self._log_integration_summary(game, credits_data)

        except Exception as e:
            self.logger.error(f"Error integrating credits data: {str(e)}")
            # クレジット統合エラーは致命的ではないので、例外を再発生させない

    def _log_integration_summary(self, game: Game, credits_data: dict) -> None:
        """
        クレジット統合結果のサマリーをログ出力

        Args:
            game: 統合後のGameオブジェクト
            credits_data: 統合されたクレジットデータ
        """
        summary_lines = [
            f"=== Credits Integration Summary for Game {game.bgg_id} ===",
            f"Primary Name: {game.primary_name}",
            f"Japanese Name: {game.japanese_name or 'Not available'}",
            f"Designers: {len(game.designers)} integrated",
            f"Artists: {len(game.artists)} integrated",
            f"Publishers: {len(game.publishers)} integrated",
            f"Categories: {len(game.categories)} integrated",
            f"Mechanics: {len(game.mechanics)} integrated"
        ]

        # デザイナー名の詳細（最初の3人のみ）
        if game.designers:
            designer_names = [d.name for d in game.designers[:3]]
            summary_lines.append(f"Top Designers: {', '.join(designer_names)}")
            if len(game.designers) > 3:
                summary_lines.append(f"... and {len(game.designers) - 3} more")

        self.logger.info("\n".join(summary_lines))


class BGGParseException(Exception):
    """BGGパース処理の例外"""
    pass


class BGGFetchException(Exception):
    """BGG取得処理の例外"""
    pass