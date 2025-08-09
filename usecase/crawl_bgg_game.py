from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod
import logging


class CrawlBggGameUseCaseInterface(ABC):
    """BGGゲームクローリングユースケースのインターフェース"""

    @abstractmethod
    def execute(self, bgg_id: int) -> Dict[str, Any]:
        """BGGからゲーム情報をクローリングして保存"""
        pass


class CrawlBggGameUseCase(CrawlBggGameUseCaseInterface):
    """BGGからゲーム情報をクローリングするユースケース"""

    def __init__(self,
                 game_mapper=None,  # GameMapperの注入
                 artist_mapper=None,  # ArtistMapperの注入
                 category_mapper=None,  # CategoryMapperの注入
                 bgg_client=None):  # BGG APIクライアントの注入
        self.game_mapper = game_mapper
        self.artist_mapper = artist_mapper
        self.category_mapper = category_mapper
        self.bgg_client = bgg_client
        self.logger = logging.getLogger(__name__)

    def execute(self, bgg_id: int) -> Dict[str, Any]:
        """
        BGGからゲーム情報をクローリングして保存

        Args:
            bgg_id (int): BGGのゲームID

        Returns:
            Dict[str, Any]: 処理結果

        Raises:
            ValueError: 無効なbgg_idの場合
            CrawlException: クローリング処理でエラーが発生した場合
        """
        try:
            # 入力値検証
            self._validate_input(bgg_id)

            # 既存データの確認
            existing_game = self._check_existing_game(bgg_id)
            if existing_game:
                self.logger.info(f"Game with bgg_id {bgg_id} already exists")
                return self._create_result(existing_game, "already_exists")

            # BGGからデータを取得
            bgg_data = self._fetch_bgg_data(bgg_id)

            # データの正規化と変換
            normalized_data = self._normalize_game_data(bgg_data)

            # ゲーム情報の保存
            saved_game = self._save_game(normalized_data)

            # 関連データ（アーティスト、カテゴリなど）の保存
            self._save_related_data(saved_game, bgg_data)

            self.logger.info(f"Successfully crawled and saved game with bgg_id {bgg_id}")
            return self._create_result(saved_game, "success")

        except Exception as e:
            self.logger.error(f"Error crawling game {bgg_id}: {str(e)}")
            raise CrawlException(f"Failed to crawl game {bgg_id}") from e

    def _validate_input(self, bgg_id: int) -> None:
        """入力値の検証"""
        if not isinstance(bgg_id, int) or bgg_id <= 0:
            raise ValueError("bgg_id must be a positive integer")

    def _check_existing_game(self, bgg_id: int) -> Optional[Any]:
        """既存ゲームの確認"""
        if self.game_mapper:
            return self.game_mapper.filter_by(bgg_id=bgg_id)
        return None

    def _fetch_bgg_data(self, bgg_id: int) -> Dict[str, Any]:
        """BGGからデータを取得"""
        if not self.bgg_client:
            raise CrawlException("BGG client not configured")

        # ここでBGG APIからデータを取得
        # 例：self.bgg_client.get_game(bgg_id)
        self.logger.info(f"Fetching data from BGG for game {bgg_id}")

        # モックデータ（実装時に実際のAPIコールに置き換え）
        return {
            "bgg_id": bgg_id,
            "name": "Sample Game",
            "year_published": 2020,
            "min_players": 2,
            "max_players": 4,
            "artists": ["Artist 1", "Artist 2"],
            "categories": ["Strategy", "Board Game"]
        }

    def _normalize_game_data(self, bgg_data: Dict[str, Any]) -> Dict[str, Any]:
        """BGGデータをデータベース形式に正規化"""
        return {
            "bgg_id": bgg_data.get("bgg_id"),
            "primary_name": bgg_data.get("name"),
            "year_released": bgg_data.get("year_published"),
            "min_players": bgg_data.get("min_players"),
            "max_players": bgg_data.get("max_players"),
            "min_playtime": bgg_data.get("min_playtime"),
            "max_playtime": bgg_data.get("max_playtime"),
            "min_age": bgg_data.get("min_age"),
            "avg_rating": bgg_data.get("avg_rating"),
            "ratings_count": bgg_data.get("ratings_count"),
            "weight": bgg_data.get("weight"),
            "image_url": bgg_data.get("image_url")
        }

    def _save_game(self, game_data: Dict[str, Any]) -> Any:
        """ゲーム情報の保存"""
        if not self.game_mapper:
            raise CrawlException("Game mapper not configured")

        return self.game_mapper.create(**game_data)

    def _save_related_data(self, game: Any, bgg_data: Dict[str, Any]) -> None:
        """関連データ（アーティスト、カテゴリなど）の保存"""
        # アーティスト情報の保存
        self._save_artists(game, bgg_data.get("artists", []))

        # カテゴリ情報の保存
        self._save_categories(game, bgg_data.get("categories", []))

    def _save_artists(self, game: Any, artists: List[str]) -> None:
        """アーティスト情報の保存と関連付け"""
        if not self.artist_mapper or not artists:
            return

        for artist_name in artists:
            # アーティストが存在しない場合は作成
            existing_artist = self.artist_mapper.filter_by(name=artist_name)
            if not existing_artist:
                artist = self.artist_mapper.create(name=artist_name)
            else:
                artist = existing_artist[0] if existing_artist else None

            # ここでgame_artistsテーブルへの関連付けを行う
            # 実装は具体的なデータベース構造に依存
            self.logger.info(f"Associated artist {artist_name} with game {game.id}")

    def _save_categories(self, game: Any, categories: List[str]) -> None:
        """カテゴリ情報の保存と関連付け"""
        if not self.category_mapper or not categories:
            return

        for category_name in categories:
            # カテゴリが存在しない場合は作成
            existing_category = self.category_mapper.filter_by(name=category_name)
            if not existing_category:
                category = self.category_mapper.create(name=category_name)
            else:
                category = existing_category[0] if existing_category else None

            # ここでgame_categoriesテーブルへの関連付けを行う
            # 実装は具体的なデータベース構造に依存
            self.logger.info(f"Associated category {category_name} with game {game.id}")

    def _create_result(self, game: Any, status: str) -> Dict[str, Any]:
        """処理結果の作成"""
        return {
            "status": status,
            "game_id": game.id if hasattr(game, 'id') else None,
            "bgg_id": game.bgg_id if hasattr(game, 'bgg_id') else None,
            "message": f"Game processing completed with status: {status}"
        }


class CrawlException(Exception):
    """クローリング処理の例外"""
    pass