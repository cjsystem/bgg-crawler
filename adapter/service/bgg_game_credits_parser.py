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
        - ひらがな/カタカナ（Kana）を最低1文字以上含む名称を優先
        - 複数候補がある場合は Kana の出現数が多い順、次点で文字列長が長い順で選択
        - Kana を含む候補が一切ない場合は None（中国語など漢字のみを誤検知しない）
        """
        try:
            alternate_section = soup.find('span', {'id': 'fullcredits-alternatename'})
            if not alternate_section:
                self.logger.warning("Alternate names section not found")
                return None

            parent_li = alternate_section.find_parent('li')
            if not parent_li:
                return None

            # 別名候補を抽出
            alternate_divs = parent_li.find_all('div', class_='ng-binding ng-scope')

            # パターン定義
            kana_pattern = re.compile(r'[\u3040-\u309F\u30A0-\u30FF]')  # ひらがな・カタカナ
            # 日本語でよく使う記号（任意・補助的）。選択ロジックの順位付け補助に使う
            jp_symbol_pattern = re.compile(r'[・ー「」『』（）\u3001\u3002]')

            candidates = []
            for div in alternate_divs:
                raw = div.get_text().strip()
                if not raw:
                    continue
                # 括弧内を除去（例: 名称（国/地域））
                name = re.sub(r'\([^)]*\)', '', raw).strip()
                if not name:
                    continue

                kana_count = len(kana_pattern.findall(name))
                symbol_count = len(jp_symbol_pattern.findall(name))
                # Kana を含むものだけを候補にする（中国語の漢字のみを除外）
                if kana_count > 0:
                    candidates.append((name, kana_count, symbol_count, len(name)))

            if not candidates:
                self.logger.info("No alternate names contain Kana; skipping Japanese name selection to avoid false positives")
                return None

            # スコアリング: Kana数（優先）→ 日本語記号数 → 文字列長 の順で降順
            candidates.sort(key=lambda x: (x[1], x[2], x[3]), reverse=True)
            selected = candidates[0][0]

            self.logger.info(f"Found Japanese name: {selected}")
            return selected

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