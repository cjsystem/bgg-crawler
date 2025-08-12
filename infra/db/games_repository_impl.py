# python
from __future__ import annotations

import logging
import time
from typing import List, Dict, Optional, Tuple, Any, Set

from sqlalchemy import text

from infra.db.base.db import session_scope
from infra.db.mapper.base_game_link_mapper import (
    GameDesignersLinkMapper,
    GameArtistsLinkMapper,
    GamePublishersLinkMapper,
    GameCategoriesLinkMapper,
    GameMechanicsLinkMapper,
    GameAwardsLinkMapper,
)
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
      4) 紐付けテーブルの置換（高速化のため一括削除＋一括挿入）
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

        # 紐付けマッパー（現在は内部一括処理へ移行中のため直接は使用しない）
        self.link_designers = GameDesignersLinkMapper()
        self.link_artists = GameArtistsLinkMapper()
        self.link_publishers = GamePublishersLinkMapper()
        self.link_categories = GameCategoriesLinkMapper()
        self.link_mechanics = GameMechanicsLinkMapper()
        self.link_awards = GameAwardsLinkMapper()

        # ロガー
        self.logger = logging.getLogger(__name__)

    def bulk_create_games(self, game_list: List[Game]) -> Dict[int, int]:
        """Game群の一括取込（UPSERT＋紐付け更新）"""
        if not game_list:
            self.logger.info("bulk_create_games: 0件のため処理をスキップします")
            return {}

        t0 = time.perf_counter()
        total_games = len(game_list)
        self.logger.info(f"[STEP0] bulk_create_games start: {total_games} games")

        with session_scope() as session:
            try:
                # トランザクション中だけ同期コミットを緩和（性能チューニング）
                session.execute(text("SET LOCAL synchronous_commit = OFF"))

                # 1) distinct 抽出 → 各エンティティを一括UPSERT
                t1 = time.perf_counter()
                distincts = self._collect_distincts(game_list)
                cnt_designers = len(distincts["designers"])
                cnt_artists = len(distincts["artists"])
                cnt_publishers = len(distincts["publishers"])
                cnt_categories = len(distincts["categories"])
                cnt_mechanics = len(distincts["mechanics"])
                cnt_genres = len(distincts["genres"])
                cnt_awards = len(distincts["awards"])
                self.logger.info(
                    f"[STEP1] distinct collected: designers={cnt_designers}, artists={cnt_artists}, "
                    f"publishers={cnt_publishers}, categories={cnt_categories}, mechanics={cnt_mechanics}, "
                    f"genres={cnt_genres}, awards={cnt_awards}"
                )

                self.designers.bulk_create_designers(distincts["designers"], session)
                self.artists.bulk_create_artists(distincts["artists"], session)
                self.publishers.bulk_create_publishers(distincts["publishers"], session)
                self.categories.bulk_create_categories(distincts["categories"], session)
                self.mechanics.bulk_create_mechanics(distincts["mechanics"], session)
                self.genres.bulk_create_genres(distincts["genres"], session)
                self.awards.bulk_create_awards(distincts["awards"], session)
                self.logger.info(f"[STEP1] upsert distinct finished in {time.perf_counter() - t1:.2f}s")

                # 2) 各IDマッピング取得
                t2 = time.perf_counter()
                self.logger.info("[STEP2] fetching id mappings ...")
                name_to_designer_id = self.designers.get_all_name_to_id_mapping(session)
                name_to_artist_id = self.artists.get_all_name_to_id_mapping(session)
                name_to_publisher_id = self.publishers.get_all_name_to_id_mapping(session)
                name_to_category_id = self.categories.get_all_name_to_id_mapping(session)
                name_to_mechanic_id = self.mechanics.get_all_name_to_id_mapping(session)
                name_to_genre_id = self.genres.get_all_name_to_id_mapping(session)
                award_key_to_id = self.awards.get_all_key_to_id_mapping(session)
                self.logger.info(
                    f"[STEP2] mappings: designers={len(name_to_designer_id)}, artists={len(name_to_artist_id)}, "
                    f"publishers={len(name_to_publisher_id)}, categories={len(name_to_category_id)}, "
                    f"mechanics={len(name_to_mechanic_id)}, genres={len(name_to_genre_id)}, "
                    f"awards={len(award_key_to_id)} in {time.perf_counter() - t2:.2f}s"
                )

                # 3) Games（非リレーション列）UPSERT
                t3 = time.perf_counter()
                upsert_rows = [self._to_games_row(g) for g in game_list]
                self.logger.info(f"[STEP3] upserting games (rows={len(upsert_rows)}) ...")
                self.games.bulk_upsert_by_bgg_id(upsert_rows, session)

                # bgg_id -> games.id
                bgg_ids = [g.bgg_id for g in game_list]
                bgg_id_to_game_id = self.games.get_id_map_by_bgg_ids(bgg_ids, session)
                missing = sorted(set(bgg_ids) - set(bgg_id_to_game_id.keys()))
                if missing:
                    self.logger.warning(
                        f"[STEP3] id mapping missing for {len(missing)} bgg_ids (showing first 10): {missing[:10]}"
                    )
                self.logger.info(
                    f"[STEP3] games upsert finished in {time.perf_counter() - t3:.2f}s (mapped={len(bgg_id_to_game_id)})"
                )

                # 4) 紐付けテーブルの置換（一括削除＋一括挿入で往復を削減）
                t4 = time.perf_counter()
                self.logger.info("[STEP4] applying link diffs (bulk mode) ...")

                affected_game_ids: Set[int] = set(bgg_id_to_game_id.values())

                # ゲーム→IDリストの集約（各リンク種別）
                map_designers: Dict[int, List[int]] = {}
                map_artists: Dict[int, List[int]] = {}
                map_publishers: Dict[int, List[int]] = {}
                map_categories: Dict[int, List[int]] = {}
                map_mechanics: Dict[int, List[int]] = {}
                map_awards: Dict[int, List[int]] = {}

                for g in game_list:
                    gid = bgg_id_to_game_id[g.bgg_id]

                    if g.designers:
                        map_designers[gid] = [
                            name_to_designer_id[d.name]
                            for d in g.designers
                            if d and d.name in name_to_designer_id
                        ]
                    if g.artists:
                        map_artists[gid] = [
                            name_to_artist_id[a.name]
                            for a in g.artists
                            if a and a.name in name_to_artist_id
                        ]
                    if g.publishers:
                        map_publishers[gid] = [
                            name_to_publisher_id[p.name]
                            for p in g.publishers
                            if p and p.name in name_to_publisher_id
                        ]
                    if g.categories:
                        map_categories[gid] = [
                            name_to_category_id[c.name]
                            for c in g.categories
                            if c and c.name in name_to_category_id
                        ]
                    if g.mechanics:
                        map_mechanics[gid] = [
                            name_to_mechanic_id[m.name]
                            for m in g.mechanics
                            if m and m.name in name_to_mechanic_id
                        ]
                    if g.awards:
                        aw_ids: List[int] = []
                        for aw in g.awards:
                            if not aw:
                                continue
                            key = self._award_key(aw.award_name, aw.award_year, aw.award_type, None)
                            if key in award_key_to_id:
                                aw_ids.append(award_key_to_id[key])
                        if aw_ids:
                            map_awards[gid] = aw_ids

                stat = {}
                stat["designers"] = self._bulk_replace_link_table(
                    session, table="game_designers", id_col="designer_id",
                    mapping=map_designers, affected_ids=affected_game_ids
                )
                stat["artists"] = self._bulk_replace_link_table(
                    session, table="game_artists", id_col="artist_id",
                    mapping=map_artists, affected_ids=affected_game_ids
                )
                stat["publishers"] = self._bulk_replace_link_table(
                    session, table="game_publishers", id_col="publisher_id",
                    mapping=map_publishers, affected_ids=affected_game_ids
                )
                stat["categories"] = self._bulk_replace_link_table(
                    session, table="game_categories", id_col="category_id",
                    mapping=map_categories, affected_ids=affected_game_ids
                )
                stat["mechanics"] = self._bulk_replace_link_table(
                    session, table="game_mechanics", id_col="mechanic_id",
                    mapping=map_mechanics, affected_ids=affected_game_ids
                )
                stat["awards"] = self._bulk_replace_link_table(
                    session, table="game_awards", id_col="award_id",
                    mapping=map_awards, affected_ids=affected_game_ids
                )

                self.logger.info(
                    "[STEP4] links applied (bulk) in %.2fs (rows: designers=%d, artists=%d, publishers=%d, "
                    "categories=%d, mechanics=%d, awards=%d)"
                    % (
                        time.perf_counter() - t4,
                        stat["designers"], stat["artists"], stat["publishers"],
                        stat["categories"], stat["mechanics"], stat["awards"],
                    )
                )

                # 5) ジャンルランクUPSERT（ゲームごとにクリア→UPSERT）
                t5 = time.perf_counter()
                self.logger.info("[STEP5] upserting genre ranks ...")
                total_ranks = 0
                for idx, g in enumerate(game_list, start=1):
                    gid = bgg_id_to_game_id[g.bgg_id]
                    self.genre_ranks.clear_genre_ranks_for_game(gid, session)
                    ranks_payload = []
                    for gr in (g.genre_ranks or []):
                        genre_name = getattr(gr.genre, "name", None)
                        genre_url = getattr(gr.genre, "bgg_url", None)
                        ranks_payload.append({
                            "name": genre_name,
                            "bgg_url": genre_url,
                            "rank_in_genre": getattr(gr, "rank_in_genre", None),
                        })
                    self.genre_ranks.upsert_genre_ranks_for_game(gid, ranks_payload, session)
                    total_ranks += len(ranks_payload)
                    if idx % 200 == 0:
                        self.logger.info(f"[STEP5] progress: {idx}/{total_games} games ranks upserted ...")
                self.logger.info(f"[STEP5] genre ranks upsert finished in {time.perf_counter() - t5:.2f}s (rows={total_ranks})")

                # 6) ベストプレイヤー数置換
                t6 = time.perf_counter()
                self.logger.info("[STEP6] replacing best player counts ...")
                total_best_counts = 0
                for idx, g in enumerate(game_list, start=1):
                    gid = bgg_id_to_game_id[g.bgg_id]
                    counts = g.best_player_counts or []
                    self.best_players.replace_counts(gid, counts, session)
                    total_best_counts += len(counts)
                    if idx % 200 == 0:
                        self.logger.info(f"[STEP6] progress: {idx}/{total_games} games best counts replaced ...")
                self.logger.info(
                    f"[STEP6] best player counts replace finished in {time.perf_counter() - t6:.2f}s (rows={total_best_counts})"
                )

                # まとめ
                total_elapsed = time.perf_counter() - t0
                self.logger.info(
                    f"[DONE] bulk_create_games finished: games={total_games}, mapped={len(bgg_id_to_game_id)}, "
                    f"links_total={sum(stat.values())}, ranks_total={total_ranks}, "
                    f"best_counts_total={total_best_counts}, elapsed={total_elapsed:.2f}s"
                )

                # commit は session_scope により自動。戻り値は bgg_id -> games.id
                return bgg_id_to_game_id

            except Exception as e:
                self.logger.exception(f"[ERROR] bulk_create_games failed: {e}")
                # session_scope により rollback 済み。呼び出し元へ再送出。
                raise

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

    # ---------- bulk helpers (STEP4 用) ----------

    def _bulk_replace_link_table(
        self,
        session,
        table: str,
        id_col: str,
        mapping: Dict[int, List[int]],
        affected_ids: Set[int],
        insert_chunk: int = 1000
    ) -> int:
        """
        指定リンクテーブルの行を、対象ゲームIDに対して丸ごと置換する
        - まず対象ゲームIDの既存行を1回の DELETE で削除
        - その後、望ましい (game_id, id_col) を executemany で INSERT（ON CONFLICT DO NOTHING）
        Returns: 挿入行数
        """
        if not affected_ids:
            return 0

        # 既存行の一括削除
        session.execute(
            text(f"DELETE FROM {table} WHERE game_id = ANY(:gids)"),
            {"gids": list(affected_ids)},
        )

        # 望ましいリンクの平坦化（重複排除）
        rows: List[Dict[str, int]] = []
        seen = set()
        for gid, ids in mapping.items():
            for eid in (ids or []):
                key = (gid, eid)
                if key in seen:
                    continue
                seen.add(key)
                rows.append({"game_id": gid, id_col: eid})

        if not rows:
            return 0

        # チャンク分割で一括挿入
        inserted = 0
        for i in range(0, len(rows), insert_chunk):
            chunk = rows[i:i + insert_chunk]
            session.execute(
                text(f"""
                    INSERT INTO {table} (game_id, {id_col})
                    VALUES (:game_id, :{id_col})
                    ON CONFLICT DO NOTHING
                """),
                chunk,
            )
            inserted += len(chunk)

        return inserted