from typing import Optional, List
from decimal import Decimal
import re
from bs4 import BeautifulSoup
from domain.game import Game
from domain.award import Award
from domain.genre import Genre
from domain.game_genre_rank import GameGenreRank


class BGGGameMainParser:
    """BGG HTMLパーサー"""

    @staticmethod
    def parse_game_from_html(html_content: str, bgg_id: int) -> Optional[Game]:
        """HTMLからGameエンティティを作成"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')

            # 基本情報の取得
            primary_name = BGGGameMainParser._extract_primary_name(soup)
            year_released = BGGGameMainParser._extract_year_released(soup)
            image_url = BGGGameMainParser._extract_image_url(soup)
            avg_rating = BGGGameMainParser._extract_avg_rating(soup)
            ratings_count = BGGGameMainParser._extract_ratings_count(soup)
            comments_count = BGGGameMainParser._extract_comments_count(soup)
            min_players, max_players = BGGGameMainParser._extract_player_range(soup)
            min_playtime, max_playtime = BGGGameMainParser._extract_playtime_range(soup)
            min_age = BGGGameMainParser._extract_min_age(soup)
            weight = BGGGameMainParser._extract_weight(soup)
            rank_overall = BGGGameMainParser._extract_rank_overall(soup)

            # リスト系データの取得
            game_awards = BGGGameMainParser._extract_awards(soup)
            game_best_player_counts = BGGGameMainParser._extract_best_player_counts(soup)
            game_genre_ranks = BGGGameMainParser._extract_genre_ranks(soup)

            return Game(
                bgg_id=bgg_id,
                primary_name=primary_name or f"Unknown Game {bgg_id}",
                year_released=year_released,
                image_url=image_url,
                avg_rating=avg_rating,
                ratings_count=ratings_count,
                comments_count=comments_count,
                min_players=min_players,
                max_players=max_players,
                min_playtime=min_playtime,
                max_playtime=max_playtime,
                min_age=min_age,
                weight=weight,
                rank_overall=rank_overall,
                game_awards=game_awards,
                game_best_player_counts=game_best_player_counts,
                game_genre_ranks=game_genre_ranks
            )

        except Exception as e:
            print(f"Error parsing HTML for game {bgg_id}: {str(e)}")
            return None

    @staticmethod
    def _extract_primary_name(soup: BeautifulSoup) -> Optional[str]:
        """primary_nameを抽出"""
        name_elem = soup.find('span', {'itemprop': 'name', 'class': 'ng-binding'})
        return name_elem.get_text(strip=True) if name_elem else None

    @staticmethod
    def _extract_year_released(soup: BeautifulSoup) -> Optional[int]:
        """year_releasedを抽出"""
        year_elem = soup.find('span', class_='game-year ng-binding ng-scope')
        if year_elem:
            year_text = year_elem.get_text(strip=True)
            # "(2018)" から数字を抽出
            match = re.search(r'\((\d{4})\)', year_text)
            if match:
                return int(match.group(1))
        return None

    @staticmethod
    def _extract_image_url(soup: BeautifulSoup) -> Optional[str]:
        """image_urlを抽出"""
        img_elem = soup.find('img', {'itemprop': 'image', 'class': 'img-responsive'})
        return img_elem.get('src') if img_elem else None

    @staticmethod
    def _extract_avg_rating(soup: BeautifulSoup) -> Optional[Decimal]:
        """avg_ratingを抽出"""
        rating_elem = soup.find('span', {'itemprop': 'ratingValue'})
        if rating_elem and rating_elem.get('content'):
            try:
                return Decimal(rating_elem.get('content'))
            except:
                pass
        return None

    @staticmethod
    def _extract_ratings_count(soup: BeautifulSoup) -> Optional[int]:
        """ratings_countを抽出 - 修正版"""
        # より具体的なセレクタで検索
        ratings_link = soup.find('a', {'ui-sref': 'geekitem.ratings({rated:1,comment:\'\',status:\'\'})'})
        if not ratings_link:
            # href属性でも検索
            ratings_link = soup.find('a', href=re.compile(r'/ratings\?rated=1'))

        if ratings_link:
            rating_text = ratings_link.get_text(strip=True)
            # "53K Rating" または "53K Ratings" から数字を抽出
            match = re.search(r'(\d+(?:\.\d+)?)\s*([KMB]?)\s*Rating', rating_text, re.IGNORECASE)
            if match:
                number = float(match.group(1))
                unit = match.group(2).upper()
                if unit == 'K':
                    number *= 1000
                elif unit == 'M':
                    number *= 1000000
                elif unit == 'B':
                    number *= 1000000000
                return int(number)
        return None

    @staticmethod
    def _extract_comments_count(soup: BeautifulSoup) -> Optional[int]:
        """comments_countを抽出"""
        comments_link = soup.find('a', {'ui-sref': 'geekitem.ratings({comment:1,rated:\'\',status:\'\'})'})
        if not comments_link:
            comments_link = soup.find('a', href=re.compile(r'/ratings\?comment=1'))

        if comments_link:
            comment_text = comments_link.get_text(strip=True)
            # "7.3K Comment" から数字を抽出
            match = re.search(r'(\d+(?:\.\d+)?)\s*([KMB]?)\s*Comment', comment_text, re.IGNORECASE)
            if match:
                number = float(match.group(1))
                unit = match.group(2).upper()
                if unit == 'K':
                    number *= 1000
                elif unit == 'M':
                    number *= 1000000
                elif unit == 'B':
                    number *= 1000000000
                return int(number)
        return None

    @staticmethod
    def _extract_player_range(soup: BeautifulSoup) -> tuple[Optional[int], Optional[int]]:
        """min_players, max_playersを抽出 - 修正版"""
        # 特定のng-ifパターンのspan要素を探す
        player_container = soup.find('span', {'ng-if': re.compile(r'.*minplayers.*maxplayers.*')})

        if player_container:
            # min用のspan（ng-if="min > 0"）
            min_span = player_container.find('span', {'ng-if': 'min > 0'})
            min_players = None
            if min_span:
                try:
                    min_players = int(min_span.get_text(strip=True))
                except ValueError:
                    pass

            # max用のspan（ng-if="max>0 && min != max"）
            max_span = player_container.find('span', {'ng-if': 'max>0 && min != max'})
            max_players = min_players  # デフォルトはmin_playersと同じ

            if max_span:
                # max_spanの中から数字だけを探す
                max_text = max_span.get_text(strip=True)
                # "–4" から "4" を抽出
                max_match = re.search(r'(\d+)$', max_text)
                if max_match:
                    try:
                        max_players = int(max_match.group(1))
                    except ValueError:
                        pass

            return min_players, max_players

        return None, None

    @staticmethod
    def _extract_playtime_range(soup: BeautifulSoup) -> tuple[Optional[int], Optional[int]]:
        """min_playtime, max_playtimeを抽出 - 修正版"""
        # minplaytime/maxplaytimeの属性を持つspan要素を探す
        time_container = soup.find('span',
                                   {'min': re.compile(r'.*minplaytime.*'), 'max': re.compile(r'.*maxplaytime.*')})

        if time_container:
            # min用のspan（ng-if="min > 0"）
            min_span = time_container.find('span', {'ng-if': 'min > 0'})
            min_playtime = None
            if min_span:
                try:
                    min_playtime = int(min_span.get_text(strip=True))
                except ValueError:
                    pass

            # max用のspan（ng-if="max>0 && min != max"）
            max_span = time_container.find('span', {'ng-if': 'max>0 && min != max'})
            max_playtime = min_playtime  # デフォルトはmin_playtimeと同じ

            if max_span:
                # max_spanの中から数字だけを探す
                max_text = max_span.get_text(strip=True)
                # "–120" から "120" を抽出
                max_match = re.search(r'(\d+)$', max_text)
                if max_match:
                    try:
                        max_playtime = int(max_match.group(1))
                    except ValueError:
                        pass

            return min_playtime, max_playtime

        return None, None

    @staticmethod
    def _extract_min_age(soup: BeautifulSoup) -> Optional[int]:
        """min_ageを抽出"""
        age_elem = soup.find('span', {'itemprop': 'suggestedMinAge'})
        if age_elem:
            age_text = age_elem.get_text(strip=True)
            try:
                return int(age_text)
            except ValueError:
                pass
        return None

    @staticmethod
    def _extract_weight(soup: BeautifulSoup) -> Optional[Decimal]:
        """weightを抽出 - 修正版"""
        # ng-classに'gameplay-weight'を含むspan要素を探す
        weight_elem = soup.find('span', {'ng-class': re.compile(r'.*gameplay-weight.*')})
        if weight_elem:
            weight_text = weight_elem.get_text(strip=True)
            # "3.87" のような数値を抽出
            match = re.search(r'(\d+\.\d+)', weight_text)
            if match:
                try:
                    return Decimal(match.group(1))
                except:
                    pass
        return None

    @staticmethod
    def _extract_rank_overall(soup: BeautifulSoup) -> Optional[int]:
        """rank_overallを抽出"""
        rank_elem = soup.find('a', class_='rank-value ng-binding ng-scope')
        if rank_elem:
            rank_text = rank_elem.get_text(strip=True)
            try:
                return int(rank_text)
            except ValueError:
                pass
        return None

    @staticmethod
    def _extract_awards(soup: BeautifulSoup) -> List[Award]:
        """受賞情報を抽出"""
        awards = []

        # 受賞リストを探す
        award_list = soup.find('ul', class_='list-unstyled ng-scope')
        if award_list:
            award_items = award_list.find_all('li', class_='ng-scope')

            for item in award_items:
                award_link = item.find('a')
                if award_link:
                    award_text = award_link.get_text(strip=True)
                    bgg_url = award_link.get('href')

                    # 受賞テキストを解析
                    award_info = BGGGameMainParser._parse_award_text(award_text)
                    if award_info:
                        awards.append(Award(
                            award_name=award_info['name'],
                            award_year=award_info['year'],
                            award_type=award_info['type'],
                            bgg_url=f"https://boardgamegeek.com{bgg_url}" if bgg_url else None
                        ))

        return awards

    @staticmethod
    def _parse_award_text(award_text: str) -> Optional[dict]:
        """受賞テキストを解析"""
        # "2020 Gra Roku Game of the Year Winner" のようなパターンを解析
        match = re.match(r'(\d{4})\s+(.+?)\s+(Winner|Nominee|Finalist)$', award_text, re.IGNORECASE)
        if match:
            year = int(match.group(1))
            name_and_category = match.group(2).strip()
            award_type = match.group(3).strip()

            return {
                'year': year,
                'name': name_and_category,
                'type': award_type,
                'category': None  # より詳細な解析が必要な場合は追加
            }
        return None

    @staticmethod
    def _extract_best_player_counts(soup: BeautifulSoup) -> List[int]:
        """ベストプレイヤー数を抽出（単一数字も含む）"""
        best_counts = []

        # "Best: 3–4" または "Best: 3" のようなテキストを探す
        for span in soup.find_all('span', class_='ng-binding'):
            text = span.get_text(strip=True)
            if 'Best:' in text:
                # "Best: 3–4" または "Best: 3" を抽出
                match = re.search(r'Best:\s*(\d+)(?:[–-](\d+))?', text)
                if match:
                    min_best = int(match.group(1))  # 最小値は必ず取得
                    max_best = int(match.group(2)) if match.group(2) else min_best  # 最大値がない場合はmin_bestと同じ

                    # 範囲を展開（例：3–4 → [3, 4]、または単一値 [3]）
                    best_counts = list(range(min_best, max_best + 1))
                    break

        return best_counts

    @staticmethod
    def _extract_genre_ranks(soup: BeautifulSoup) -> List[GameGenreRank]:
        """ジャンルランク情報を抽出 - 修正版"""
        genre_ranks = []

        # ランク情報のul要素を探す（title属性に"Rank"を含むもののみ）
        rank_lists = soup.find_all('ul', class_='ranks ng-scope')

        for rank_list in rank_lists:
            # titleに"Rank"が含まれているかチェック（受賞情報を除外）
            title = rank_list.get('title', '')
            if 'Rank' not in title:
                continue

            rank_item = rank_list.find('li', class_='rank')
            if rank_item:
                # ジャンル名を取得
                genre_span = rank_item.find('span', class_='rank-title ng-binding')
                if genre_span:
                    genre_name = genre_span.get_text(strip=True)

                    # ランクを取得
                    rank_link = rank_item.find('a', class_='rank-value ng-binding ng-scope')
                    rank_value = None
                    genre_url = None

                    if rank_link:
                        try:
                            rank_value = int(rank_link.get_text(strip=True))
                        except ValueError:
                            pass
                        genre_url = rank_link.get('href')

                    # Genre エンティティを作成
                    genre = Genre(
                        name=genre_name,
                        bgg_url=f"https://boardgamegeek.com/{genre_url}" if genre_url else None
                    )

                    # GameGenreRank エンティティを作成
                    genre_ranks.append(GameGenreRank(
                        genre=genre,
                        rank_in_genre=rank_value
                    ))

        return genre_ranks


class BGGHTMLParserException(Exception):
    """BGG HTMLパーサー例外"""
    pass