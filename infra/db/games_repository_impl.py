# python
from __future__ import annotations

from typing import List, Dict, Optional, Tuple, Any

from infra.db.base.db import session_scope
from infra.db.mapper.base_game_link_mapper import GameDesignersLinkMapper, GameArtistsLinkMapper, \
    GamePublishersLinkMapper, GameCategoriesLinkMapper, GameMechanicsLinkMapper, GameAwardsLinkMapper
from infra.db.mapper.games_mapper import GamesMapper
from infra.db.mapper.artists_mapper import ArtistsMapper
from infra.db.mapper.designers_mapper import DesignersMapper
from infra.db.mapper.publishers_mapper import PublishersMapper
from infra.db.mapper.categories_mapper import CategoriesMapper
from infra.db.mapper.mechanics_mapper import MechanicsMapper
from infra.db.mapper.genres_mapper import GenresMapper
from infra.db.mapper.game_genre_ranks_mapper import GameGenreRanksMapper
from infra.db.mapper.awards_mapper import AwardsMapper
from infra.db.mapper.game_best_player_counts_mapper import GameBestPlayerCountsMapper

from domain.game import Game
from usecase.port.games_repository import GamesRepository


class GamesRepositoryImpl(GamesRepository):
    """Game一括取込の実装
    - 1つのトランザクション内で
      1) distinct 抽出 → 各エンティティUPSERT
      2) 各IDマッピング取得
      3) Games（非リレーション列）UPSERT
      4) 紐付けテーブルの差分更新
      5) ジャンルランクUPSERT
      6) ベストプレイヤー数置換
    """

    def __init__(self) -> None:
        # 同一infra層のマッパーを直接生成（DI不要）
        self.games = GamesMapper()
        self.artists = ArtistsMapper()
        self.designers = DesignersMapper()
        self.publishers = PublishersMapper()
        self.categories = CategoriesMapper()
        self.mechanics = MechanicsMapper()
        self.genres = GenresMapper()
        self.awards = AwardsMapper()
        self.genre_ranks = GameGenreRanksMapper()
        self.best_players = GameBestPlayerCountsMapper()

        # 紐付けマッパー
        self.link_designers = GameDesignersLinkMapper()
        self.link_artists = GameArtistsLinkMapper()
        self.link_publishers = GamePublishersLinkMapper()
        self.link_categories = GameCategoriesLinkMapper()
        self.link_mechanics = GameMechanicsLinkMapper()
        self.link_awards = GameAwardsLinkMapper()

    def bulk_create_games(self, game_list: List[Game]) -> Dict[int, int]:
        """Game群の一括取込（UPSERT＋紐付け更新）"""
        if not game_list:
            return {}

        with session_scope() as session:
            # 1) distinct 抽出 → 各エンティティを一括UPSERT
            distincts = self._collect_distincts(game_list)
            self.designers.bulk_create_designers(distincts["designers"], session)
            self.artists.bulk_create_artists(distincts["artists"], session)
            self.publishers.bulk_create_publishers(distincts["publishers"], session)
            self.categories.bulk_create_categories(distincts["categories"], session)
            self.mechanics.bulk_create_mechanics(distincts["mechanics"], session)
            self.genres.bulk_create_genres(distincts["genres"], session)
            self.awards.bulk_create_awards(distincts["awards"], session)

            # 2) 各IDマッピング取得
            name_to_designer_id = self.designers.get_all_name_to_id_mapping(session)
            name_to_artist_id = self.artists.get_all_name_to_id_mapping(session)
            name_to_publisher_id = self.publishers.get_all_name_to_id_mapping(session)
            name_to_category_id = self.categories.get_all_name_to_id_mapping(session)
            name_to_mechanic_id = self.mechanics.get_all_name_to_id_mapping(session)
            name_to_genre_id = self.genres.get_all_name_to_id_mapping(session)
            award_key_to_id = self.awards.get_all_key_to_id_mapping(session)

            # 3) Games（非リレーション列）UPSERT
            upsert_rows = [self._to_games_row(g) for g in game_list]
            self.games.bulk_upsert_by_bgg_id(upsert_rows, session)

            # bgg_id -> games.id
            bgg_ids = [g.bgg_id for g in game_list]
            bgg_id_to_game_id = self.games.get_id_map_by_bgg_ids(bgg_ids, session)

            # 4) 紐付け差分適用（designers/artists/publishers/categories/mechanics/awards）
            for g in game_list:
                gid = bgg_id_to_game_id[g.bgg_id]

                designer_ids = [name_to_designer_id[d.name] for d in (g.designers or []) if d.name in name_to_designer_id]
                self.link_designers.replace_links(gid, designer_ids, session)

                artist_ids = [name_to_artist_id[a.name] for a in (g.artists or []) if a.name in name_to_artist_id]
                self.link_artists.replace_links(gid, artist_ids, session)

                publisher_ids = [name_to_publisher_id[p.name] for p in (g.publishers or []) if p.name in name_to_publisher_id]
                self.link_publishers.replace_links(gid, publisher_ids, session)

                category_ids = [name_to_category_id[c.name] for c in (g.categories or []) if c.name in name_to_category_id]
                self.link_categories.replace_links(gid, category_ids, session)

                mechanic_ids = [name_to_mechanic_id[m.name] for m in (g.mechanics or []) if m.name in name_to_mechanic_id]
                self.link_mechanics.replace_links(gid, mechanic_ids, session)

                # awards（複合キー）
                award_ids = []
                for aw in (g.awards or []):
                    key = self._award_key(aw.award_name, aw.award_year, aw.award_type, None)
                    if key in award_key_to_id:
                        award_ids.append(award_key_to_id[key])
                self.link_awards.replace_links(gid, award_ids, session)

            # 5) ジャンルランクUPSERT（ゲームごとにクリア→UPSERT）
            for g in game_list:
                gid = bgg_id_to_game_id[g.bgg_id]
                self.genre_ranks.clear_genre_ranks_for_game(gid, session)
                ranks_payload = []
                for gr in (g.genre_ranks or []):
                    genre_name = getattr(gr.genre, "name", None)
                    genre_url = getattr(gr.genre, "bgg_url", None)
                    ranks_payload.append({
                        "name": genre_name,
                        "bgg_url": genre_url,
                        "rank_in_genre": getattr(gr, "rank_in_genre", None)
                    })
                self.genre_ranks.upsert_genre_ranks_for_game(gid, ranks_payload, session)

            # 6) ベストプレイヤー数置換
            for g in game_list:
                gid = bgg_id_to_game_id[g.bgg_id]
                self.best_players.replace_counts(gid, g.best_player_counts or [], session)

            # commit は session_scope により自動。戻り値は bgg_id -> games.id
            return bgg_id_to_game_id

    def list_all_bgg_id(self) -> List[int]:
        """games テーブル内に存在する全ての bgg_id を list[int] で返す"""
        with session_scope() as session:
            return self.games.list_all_bgg_ids(session)

    # ========== helpers ==========

    @staticmethod
    def _to_games_row(g: Game) -> Dict[str, Any]:
        """非リレーション列のみを抽出してGamesMapperに渡すペイロードを生成"""
        return {
            "bgg_id": g.bgg_id,
            "primary_name": g.primary_name,
            "japanese_name": g.japanese_name,
            "year_released": g.year_released,
            "image_url": g.image_url,
            "avg_rating": g.avg_rating,
            "ratings_count": g.ratings_count,
            "comments_count": g.comments_count,
            "min_players": g.min_players,
            "max_players": g.max_players,
            "min_playtime": g.min_playtime,
            "max_playtime": g.max_playtime,
            "min_age": g.min_age,
            "weight": g.weight,
            "rank_overall": g.rank_overall,
        }

    @staticmethod
    def _award_key(
        award_name: str,
        award_year: int,
        award_type: str,
        award_category: Optional[str],
    ) -> Tuple[str, int, str, Optional[str]]:
        return (award_name, int(award_year), award_type, award_category)

    @staticmethod
    def _dedup_by_name(items: List[Dict[str, Optional[str]]]) -> Dict[str, Dict]:
        dedup: Dict[str, Dict] = {}
        for it in items:
            name = (it.get("name") or "").strip()
            if not name:
                continue
            dedup[name] = {"name": name, "bgg_url": it.get("bgg_url")}
        return dedup

    def _collect_distincts(self, game_list: List[Game]) -> Dict[str, List[Dict]]:
        """Game配列からエンティティ別に distinct を抽出"""
        designers_map: Dict[str, Dict] = {}
        artists_map: Dict[str, Dict] = {}
        publishers_map: Dict[str, Dict] = {}
        categories_map: Dict[str, Dict] = {}
        mechanics_map: Dict[str, Dict] = {}
        genres_map: Dict[str, Dict] = {}
        awards_map: Dict[Tuple[str, int, str, Optional[str]], Dict] = {}

        for g in game_list:
            # designers
            designers_map.update(self._dedup_by_name(
                [{"name": d.name, "bgg_url": getattr(d, "bgg_url", None)} for d in (g.designers or [])]
            ))
            # artists
            artists_map.update(self._dedup_by_name(
                [{"name": a.name, "bgg_url": getattr(a, "bgg_url", None)} for a in (g.artists or [])]
            ))
            # publishers
            publishers_map.update(self._dedup_by_name(
                [{"name": p.name, "bgg_url": getattr(p, "bgg_url", None)} for p in (g.publishers or [])]
            ))
            # categories
            categories_map.update(self._dedup_by_name(
                [{"name": c.name, "bgg_url": getattr(c, "bgg_url", None)} for c in (g.categories or [])]
            ))
            # mechanics
            mechanics_map.update(self._dedup_by_name(
                [{"name": m.name, "bgg_url": getattr(m, "bgg_url", None)} for m in (g.mechanics or [])]
            ))
            # genres（genre_ranksから）
            genres_map.update(self._dedup_by_name(
                [{"name": getattr(gr.genre, "name", None), "bgg_url": getattr(gr.genre, "bgg_url", None)}
                 for gr in (g.genre_ranks or []) if getattr(gr, "genre", None)]
            ))
            # awards（複合キー）
            for aw in (g.awards or []):
                if not aw.award_name or aw.award_year is None or not aw.award_type:
                    continue
                key = self._award_key(aw.award_name, aw.award_year, aw.award_type, None)
                awards_map[key] = {
                    "award_name": aw.award_name,
                    "award_year": int(aw.award_year),
                    "award_type": aw.award_type,
                    "award_category": None,
                    "bgg_url": getattr(aw, "bgg_url", None),
                }

        return {
            "designers": list(designers_map.values()),
            "artists": list(artists_map.values()),
            "publishers": list(publishers_map.values()),
            "categories": list(categories_map.values()),
            "mechanics": list(mechanics_map.values()),
            "genres": list(genres_map.values()),
            "awards": list(awards_map.values()),
        }