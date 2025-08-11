from bs4 import BeautifulSoup
import re
import logging
from typing import List, Optional
from domain.designer import Designer
from domain.artist import Artist
from domain.publisher import Publisher
from domain.category import Category
from domain.mechanic import Mechanic


class BGGGameCreditsParser:
    """Board Game Geek ゲームクレジットページのHTMLパーサー"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def parse_credits_html(self, html_content: str) -> dict:
        """
        クレジットHTMLを解析してゲーム情報を抽出する

        Args:
            html_content: BGGクレジットページのHTML内容

        Returns:
            dict: 抽出された情報の辞書
        """
        soup = BeautifulSoup(html_content, 'html.parser')

        return {
            'japanese_name': self._extract_japanese_name(soup),
            'designers': self._extract_designers(soup),
            'artists': self._extract_artists(soup),
            'publishers': self._extract_publishers(soup),
            'categories': self._extract_categories(soup),
            'mechanics': self._extract_mechanics(soup)
        }

    def _extract_japanese_name(self, soup: BeautifulSoup) -> Optional[str]:
        """
        別名から日本語名を抽出する

        Args:
            soup: BeautifulSoupオブジェクト

        Returns:
            Optional[str]: 日本語名（見つからない場合はNone）
        """
        try:
            # alternate namesセクションを探す
            alternate_section = soup.find('span', {'id': 'fullcredits-alternatename'})
            if not alternate_section:
                self.logger.warning("Alternate names section not found")
                return None

            # 親要素に移動してalternate namesのコンテンツを探す
            parent_li = alternate_section.find_parent('li')
            if not parent_li:
                return None

            # ng-repeat="name in creditsctrl.geekitem.data.item.alternatenames"を含むdivを探す
            alternate_divs = parent_li.find_all('div', class_='ng-binding ng-scope')

            # 日本語文字（ひらがな、カタカナ、漢字）を含む名前を探す
            japanese_pattern = re.compile(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]')

            for div in alternate_divs:
                name = div.get_text().strip()
                if japanese_pattern.search(name):
                    # 括弧内の情報を除去
                    clean_name = re.sub(r'\([^)]*\)', '', name).strip()
                    self.logger.info(f"Found Japanese name: {clean_name}")
                    return clean_name

            self.logger.info("Japanese name not found in alternate names")
            return None

        except Exception as e:
            self.logger.error(f"Error extracting Japanese name: {e}")
            return None

    def _extract_designers(self, soup: BeautifulSoup) -> List[Designer]:
        """デザイナー情報を抽出する"""
        return self._extract_credits_with_links(soup, 'fullcredits-boardgamedesigner', 'boardgamedesigner', Designer)

    def _extract_artists(self, soup: BeautifulSoup) -> List[Artist]:
        """アーティスト情報を抽出する"""
        return self._extract_credits_with_links(soup, 'fullcredits-boardgameartist', 'boardgameartist', Artist)

    def _extract_publishers(self, soup: BeautifulSoup) -> List[Publisher]:
        """パブリッシャー情報を抽出する"""
        return self._extract_credits_with_links(soup, 'fullcredits-boardgamepublisher', 'boardgamepublisher', Publisher)

    def _extract_categories(self, soup: BeautifulSoup) -> List[Category]:
        """カテゴリ情報を抽出する"""
        return self._extract_credits_with_links(soup, 'fullcredits-boardgamecategory', 'boardgamecategory', Category)

    def _extract_mechanics(self, soup: BeautifulSoup) -> List[Mechanic]:
        """メカニクス情報を抽出する"""
        return self._extract_credits_with_links(soup, 'fullcredits-boardgamemechanic', 'boardgamemechanic', Mechanic)

    def _extract_credits_with_links(self, soup: BeautifulSoup, section_id: str, link_prefix: str, entity_class) -> List:
        """
        リンク付きクレジット情報を抽出する汎用メソッド

        Args:
            soup: BeautifulSoupオブジェクト
            section_id: セクションのID
            link_prefix: リンクのプレフィックス（例: 'boardgamedesigner'）
            entity_class: 作成するエンティティクラス

        Returns:
            List: エンティティオブジェクトのリスト
        """
        try:
            results = []
            seen_urls = set()  # 重複チェック用

            # 該当セクションを探す
            section = soup.find('span', {'id': section_id})
            if not section:
                self.logger.warning(f"Section {section_id} not found")
                return results

            # 親要素のliを取得
            parent_li = section.find_parent('li')
            if not parent_li:
                self.logger.warning(f"Parent li not found for section {section_id}")
                return results

            # より具体的に ng-repeat を含む div を探す
            # ng-if="info.datatype == 'geekitem_linkdata'" の div を探す
            linkdata_div = parent_li.find('div', {'ng-if': "info.datatype == 'geekitem_linkdata'"})
            if not linkdata_div:
                self.logger.warning(f"Link data div not found for section {section_id}")
                return results

            # ng-repeat="link in creditsctrl.geekitem.data.item.links[info.keyname]" を含む div を探す
            repeat_divs = linkdata_div.find_all('div', class_='ng-scope')

            for div in repeat_divs:
                # このdivが ng-repeat を含むかチェック
                ng_repeat = div.get('ng-repeat')
                if not ng_repeat or 'link in creditsctrl.geekitem.data.item.links' not in ng_repeat:
                    continue

                # リンクを含むaタグを探す
                link = div.find('a', href=True)
                if link and link.get('href', '').startswith(f'/{link_prefix}/'):
                    name = link.get_text().strip()
                    href = link.get('href')

                    if name and href and href not in seen_urls:
                        seen_urls.add(href)  # 重複チェック

                        # フルURLを構築
                        bgg_url = f"https://boardgamegeek.com{href}" if not href.startswith('http') else href

                        try:
                            # エンティティオブジェクトを作成
                            entity = entity_class(name=name, bgg_url=bgg_url)
                            results.append(entity)
                            self.logger.debug(f"Added {entity_class.__name__}: {name}")
                        except Exception as e:
                            self.logger.error(f"Error creating {entity_class.__name__} for {name}: {e}")

            self.logger.info(f"Extracted {len(results)} unique {entity_class.__name__.lower()}s")
            return results

        except Exception as e:
            self.logger.error(f"Error extracting {entity_class.__name__.lower()}s: {e}")
            return []

    def get_extraction_summary(self, parsed_data: dict) -> str:
        """
        抽出結果のサマリーを生成する

        Args:
            parsed_data: parse_credits_htmlの戻り値

        Returns:
            str: サマリー文字列
        """
        summary_lines = [
            "=== BGG Game Credits Extraction Summary ===",
            f"Japanese Name: {parsed_data.get('japanese_name', 'Not found')}",
            f"Designers: {len(parsed_data.get('designers', []))} found",
            f"Artists: {len(parsed_data.get('artists', []))} found",
            f"Publishers: {len(parsed_data.get('publishers', []))} found",
            f"Categories: {len(parsed_data.get('categories', []))} found",
            f"Mechanics: {len(parsed_data.get('mechanics', []))} found",
            ""
        ]

        # 各セクションの詳細を追加
        for section_name, items in parsed_data.items():
            if section_name != 'japanese_name' and items:
                summary_lines.append(f"{section_name.capitalize()}:")
                for item in items[:5]:  # 最初の5件のみ表示
                    if hasattr(item, 'name'):
                        summary_lines.append(f"  - {item.name}")
                if len(items) > 5:
                    summary_lines.append(f"  ... and {len(items) - 5} more")
                summary_lines.append("")

        return "\n".join(summary_lines)


# 使用例
if __name__ == "__main__":
    # ログ設定
    logging.basicConfig(level=logging.INFO)

    # HTMLファイルを読み込んで解析
    parser = BGGGameCreditsParser()

    # HTMLファイルのパス（実際のパスに変更してください）
    html_file_path = "output/html_boardgamegeek.com_boardgame_224517_brass-birmingham_credits_20250810_131025.html"

    try:
        with open(html_file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        # HTML解析実行
        game_info = parser.parse_credits_html(html_content)

        # 結果表示
        summary = parser.get_extraction_summary(game_info)
        print(summary)

        # 各情報の詳細表示
        print("\n=== Detailed Results ===")
        for designer in game_info['designers']:
            print(f"Designer: {designer.name} - {designer.bgg_url}")

        for artist in game_info['artists']:
            print(f"Artist: {artist.name} - {artist.bgg_url}")

        for publisher in game_info['publishers']:
            print(f"Publisher: {publisher.name} - {publisher.bgg_url}")

        for category in game_info['categories']:
            print(f"Category: {category.name} - {category.bgg_url}")

        for mechanic in game_info['mechanics']:
            print(f"Mechanic: {mechanic.name} - {mechanic.bgg_url}")

    except FileNotFoundError:
        print(f"HTMLファイルが見つかりません: {html_file_path}")
    except Exception as e:
        print(f"エラーが発生しました: {e}")