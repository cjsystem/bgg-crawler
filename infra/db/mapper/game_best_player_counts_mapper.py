# python
# infra/db/mapper/game_best_player_counts_mapper.py
from typing import Iterable, List, Dict, Set
from sqlalchemy import text
from sqlalchemy.orm import Session

from infra.db.models import GameBestPlayerCounts


class GameBestPlayerCountsMapper:
    """game_best_player_counts テーブル用マッパー
    - best_player_counts はゲームごとに複数の整数(player_count)を持つ
    - 一意制約: (game_id, player_count)
    注意: commit/rollback は呼び出し側で行ってください
    """

    # 取得系

    def list_counts_by_game(self, game_id: int, session: Session) -> List[int]:
        """指定ゲームのベストプレイヤー数（整数）一覧を昇順で返す"""
        rs = session.execute(
            text("""
                SELECT player_count
                FROM game_best_player_counts
                WHERE game_id = :game_id
                ORDER BY player_count ASC
            """),
            {"game_id": game_id}
        ).all()
        return [row[0] for row in rs]

    def list_rows_by_game(self, game_id: int, session: Session) -> List[GameBestPlayerCounts]:
        """指定ゲームの行オブジェクト一覧を返す"""
        return (
            session.query(GameBestPlayerCounts)
            .filter(GameBestPlayerCounts.game_id == game_id)
            .order_by(GameBestPlayerCounts.player_count.asc())
            .all()
        )

    def exists(self, game_id: int, player_count: int, session: Session) -> bool:
        """単一(player_count)の存在確認"""
        row = session.execute(
            text("""
                SELECT 1
                FROM game_best_player_counts
                WHERE game_id = :game_id AND player_count = :player_count
                LIMIT 1
            """),
            {"game_id": game_id, "player_count": int(player_count)}
        ).first()
        return row is not None

    def list_game_ids_by_player_count(self, player_count: int, session: Session) -> List[int]:
        """指定の player_count をベストとするゲームID一覧を昇順で返す"""
        rs = session.execute(
            text("""
                SELECT game_id
                FROM game_best_player_counts
                WHERE player_count = :player_count
                ORDER BY game_id ASC
            """),
            {"player_count": int(player_count)}
        ).all()
        return [row[0] for row in rs]

    # 変更系（呼び出し側で commit すること）

    def add_counts(self, game_id: int, counts: Iterable[int], session: Session) -> int:
        """複数の player_count を追加（既存はスキップ）。戻り値は追加件数"""
        normalized: List[int] = sorted({int(c) for c in (counts or []) if int(c) > 0})
        if not normalized:
            return 0

        # 既存との差分だけINSERT
        existing = set(self.list_counts_by_game(game_id, session))
        to_insert = [c for c in normalized if c not in existing]
        if not to_insert:
            return 0

        params = [{"game_id": game_id, "player_count": c} for c in to_insert]
        session.execute(
            text("""
                INSERT INTO game_best_player_counts (game_id, player_count)
                VALUES (:game_id, :player_count)
                ON CONFLICT (game_id, player_count) DO NOTHING
            """),
            params
        )
        return len(to_insert)

    def remove_counts(self, game_id: int, counts: Iterable[int], session: Session) -> int:
        """複数の player_count を削除。戻り値は削除件数（推定）"""
        normalized: List[int] = sorted({int(c) for c in (counts or [])})
        if not normalized:
            return 0
        result = session.execute(
            text("""
                DELETE FROM game_best_player_counts
                WHERE game_id = :game_id
                  AND player_count = ANY(:counts)
            """),
            {"game_id": game_id, "counts": normalized}
        )
        return result.rowcount or 0

    def clear_counts(self, game_id: int, session: Session) -> int:
        """指定ゲームのベストプレイヤー数を全削除。戻り値は削除件数"""
        result = session.execute(
            text("DELETE FROM game_best_player_counts WHERE game_id = :game_id"),
            {"game_id": game_id}
        )
        return result.rowcount or 0

    def replace_counts(self, game_id: int, new_counts: Iterable[int], session: Session) -> Dict[str, object]:
        """差分で入替（追加・削除）を行う
        戻り値:
          {
            'added': [..],
            'removed': [..],
            'added_count': x,
            'removed_count': y
          }
        """
        new_set: Set[int] = {int(c) for c in (new_counts or []) if int(c) > 0}
        current_set: Set[int] = set(self.list_counts_by_game(game_id, session))

        to_add = sorted(new_set - current_set)
        to_remove = sorted(current_set - new_set)

        added_count = self.add_counts(game_id, to_add, session) if to_add else 0
        removed_count = self.remove_counts(game_id, to_remove, session) if to_remove else 0

        return {
            "added": to_add,
            "removed": to_remove,
            "added_count": added_count,
            "removed_count": removed_count,
        }

    def upsert_one(self, game_id: int, player_count: int, session: Session) -> bool:
        """単一の player_count をUPSERT（存在しなければ追加、存在すれば何もしない）"""
        pc = int(player_count)
        if pc <= 0:
            return False
        session.execute(
            text("""
                INSERT INTO game_best_player_counts (game_id, player_count)
                VALUES (:game_id, :player_count)
                ON CONFLICT (game_id, player_count) DO NOTHING
            """),
            {"game_id": game_id, "player_count": pc}
        )
        return True