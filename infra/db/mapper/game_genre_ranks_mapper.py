# python
# infra/db/mapper/game_genre_ranks_mapper.py
from typing import List, Dict, Optional
from sqlalchemy import text
from sqlalchemy.orm import Session

from infra.db.models import Games, Genres
from .genres_mapper import GenresMapper


class GameGenreRanksMapper:
    """ゲームごとのジャンル順位を管理するマッパー
    想定テーブル: game_genre_ranks (game_id, genre_id, rank_in_genre)
    一意制約: (game_id, genre_id)
    """

    def __init__(self) -> None:
        self._genres = GenresMapper()

    def get_genre_ranks_by_game(self, game_id: int, session: Session) -> List[Dict]:
        """指定ゲームのジャンル順位一覧を取得（JOINでジャンル名も返す）"""
        rs = session.execute(
            text("""
                SELECT
                    ggr.genre_id,
                    ge.name AS genre_name,
                    ge.bgg_url AS genre_bgg_url,
                    ggr.rank_in_genre
                FROM game_genre_ranks AS ggr
                JOIN genres AS ge ON ge.id = ggr.genre_id
                WHERE ggr.game_id = :game_id
                ORDER BY ggr.rank_in_genre NULLS LAST, ge.name ASC
            """),
            {"game_id": game_id}
        ).mappings().all()

        # List[RowMapping] -> List[Dict]
        return [dict(row) for row in rs]

    def clear_genre_ranks_for_game(self, game_id: int, session: Session) -> int:
        """指定ゲームのジャンル順位を全削除（戻り値は削除件数）"""
        result = session.execute(
            text("DELETE FROM game_genre_ranks WHERE game_id = :game_id"),
            {"game_id": game_id}
        )
        return result.rowcount or 0

    def upsert_genre_ranks_for_game(
        self,
        game_id: int,
        ranks: List[Dict],
        session: Session
    ) -> None:
        """ジャンル順位をUPSERT
        ranks の要素例: {"name": "Strategy", "bgg_url": "https://...", "rank_in_genre": 12}
        - まず genres を存在しなければ作成（bgg_urlは既存がNULLのときのみ更新）
        - 次に game_genre_ranks に (game_id, genre_id, rank_in_genre) をUPSERT
        """
        if not ranks:
            return

        # 1) ジャンルのUPSERT
        genre_rows = [{"name": r.get("name"), "bgg_url": r.get("bgg_url")} for r in ranks if r.get("name")]
        self._genres.bulk_create_genres(genre_rows, session)

        # 2) name -> id マップを取得
        names = {r["name"] for r in ranks if r.get("name")}
        name_to_id = self._genres.get_all_name_to_id_mapping(session)
        insert_rows = []
        for r in ranks:
            name = r.get("name")
            if not name:
                continue
            gid = name_to_id.get(name)
            if gid is None:
                # 念のためのフォールバック（理論上ここには来ない想定）
                g = self._genres.get_by_name(name, session)
                gid = getattr(g, "id", None) if g else None
            if gid is None:
                continue

            insert_rows.append({
                "game_id": game_id,
                "genre_id": gid,
                "rank_in_genre": r.get("rank_in_genre"),
            })

        if not insert_rows:
            return

        # 3) game_genre_ranks のUPSERT
        session.execute(
            text("""
                INSERT INTO game_genre_ranks (game_id, genre_id, rank_in_genre)
                VALUES (:game_id, :genre_id, :rank_in_genre)
                ON CONFLICT (game_id, genre_id) DO UPDATE
                SET rank_in_genre = EXCLUDED.rank_in_genre
            """),
            insert_rows
        )

    def remove_one(
        self,
        game_id: int,
        genre_id: int,
        session: Session
    ) -> bool:
        """特定の (game_id, genre_id) を1件削除"""
        result = session.execute(
            text("""
                DELETE FROM game_genre_ranks
                WHERE game_id = :game_id AND genre_id = :genre_id
            """),
            {"game_id": game_id, "genre_id": genre_id}
        )
        return (result.rowcount or 0) > 0

    def get_rank_for_one(
        self,
        game_id: int,
        genre_id: int,
        session: Session
    ) -> Optional[int]:
        """特定ジャンルのランク値を1件取得"""
        row = session.execute(
            text("""
                SELECT rank_in_genre
                FROM game_genre_ranks
                WHERE game_id = :game_id AND genre_id = :genre_id
                LIMIT 1
            """),
            {"game_id": game_id, "genre_id": genre_id}
        ).first()
        return None if row is None else row[0]