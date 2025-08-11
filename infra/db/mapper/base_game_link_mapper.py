# python
# infra/db/mapper/link_mappers.py
from typing import Iterable, List, Dict, Set, Optional, Tuple
from sqlalchemy import text
from sqlalchemy.orm import Session


class BaseGameLinkMapper:
    """ゲームと各要素の中間テーブル用ベースマッパー
    - 具体テーブル（例: game_artists）とエンティティ側の列名（例: artist_id）を指定して利用
    """

    def __init__(self, table_name: str, entity_id_column: str) -> None:
        self._table = table_name
        self._entity_col = entity_id_column

    # 取得系

    def get_entity_ids_for_game(self, game_id: int, session: Session) -> List[int]:
        """指定ゲームに紐づくエンティティID一覧を昇順で返す"""
        sql = text(f"""
            SELECT {self._entity_col}
            FROM {self._table}
            WHERE game_id = :game_id
            ORDER BY {self._entity_col} ASC
        """)
        rows = session.execute(sql, {"game_id": game_id}).all()
        return [r[0] for r in rows]

    def get_game_ids_for_entity(self, entity_id: int, session: Session) -> List[int]:
        """指定エンティティに紐づくゲームID一覧を昇順で返す"""
        sql = text(f"""
            SELECT game_id
            FROM {self._table}
            WHERE {self._entity_col} = :entity_id
            ORDER BY game_id ASC
        """)
        rows = session.execute(sql, {"entity_id": entity_id}).all()
        return [r[0] for r in rows]

    def has_link(self, game_id: int, entity_id: int, session: Session) -> bool:
        """単一の紐付けが存在するか"""
        sql = text(f"""
            SELECT 1
            FROM {self._table}
            WHERE game_id = :game_id AND {self._entity_col} = :entity_id
            LIMIT 1
        """)
        row = session.execute(sql, {"game_id": game_id, "entity_id": entity_id}).first()
        return row is not None

    # 変更系（呼び出し側でcommitしてください）

    def add_links(self, game_id: int, entity_ids: Iterable[int], session: Session) -> int:
        """紐付けを追加（既存はスキップ）。戻り値は実質的に追加された件数"""
        ids: Set[int] = {int(i) for i in entity_ids or []}
        if not ids:
            return 0

        # 既存との差分だけINSERT
        existing = set(self.get_entity_ids_for_game(game_id, session))
        to_insert = sorted(ids - existing)
        if not to_insert:
            return 0

        params = [{"game_id": game_id, "entity_id": eid} for eid in to_insert]
        sql = text(f"""
            INSERT INTO {self._table} (game_id, {self._entity_col})
            VALUES (:game_id, :entity_id)
            ON CONFLICT (game_id, {self._entity_col}) DO NOTHING
        """)
        session.execute(sql, params)
        return len(to_insert)

    def remove_links(self, game_id: int, entity_ids: Iterable[int], session: Session) -> int:
        """指定IDの紐付けを削除。戻り値は削除件数（推定）"""
        ids: List[int] = [int(i) for i in (entity_ids or [])]
        if not ids:
            return 0
        sql = text(f"""
            DELETE FROM {self._table}
            WHERE game_id = :game_id
              AND {self._entity_col} = ANY(:ids)
        """)
        result = session.execute(sql, {"game_id": game_id, "ids": ids})
        return result.rowcount or 0

    def clear_links(self, game_id: int, session: Session) -> int:
        """指定ゲームの紐付けを全削除。戻り値は削除件数"""
        sql = text(f"DELETE FROM {self._table} WHERE game_id = :game_id")
        result = session.execute(sql, {"game_id": game_id})
        return result.rowcount or 0

    def replace_links(self, game_id: int, new_entity_ids: Iterable[int], session: Session) -> Dict[str, object]:
        """差分で入替を行う（追加・削除）。戻り値: {'added': [...], 'removed': [...], 'added_count': x, 'removed_count': y}"""
        new_ids: Set[int] = {int(i) for i in (new_entity_ids or [])}
        current_ids = set(self.get_entity_ids_for_game(game_id, session))

        to_add = sorted(new_ids - current_ids)
        to_remove = sorted(current_ids - new_ids)

        added_count = self.add_links(game_id, to_add, session) if to_add else 0
        removed_count = self.remove_links(game_id, to_remove, session) if to_remove else 0

        return {
            "added": to_add,
            "removed": to_remove,
            "added_count": added_count,
            "removed_count": removed_count,
        }


# 具体テーブル向けの実装クラス

class GameArtistsLinkMapper(BaseGameLinkMapper):
    def __init__(self) -> None:
        super().__init__(table_name="game_artists", entity_id_column="artist_id")


class GameAwardsLinkMapper(BaseGameLinkMapper):
    def __init__(self) -> None:
        super().__init__(table_name="game_awards", entity_id_column="award_id")


class GameCategoriesLinkMapper(BaseGameLinkMapper):
    def __init__(self) -> None:
        super().__init__(table_name="game_categories", entity_id_column="category_id")


class GameDesignersLinkMapper(BaseGameLinkMapper):
    def __init__(self) -> None:
        super().__init__(table_name="game_designers", entity_id_column="designer_id")


class GameMechanicsLinkMapper(BaseGameLinkMapper):
    def __init__(self) -> None:
        super().__init__(table_name="game_mechanics", entity_id_column="mechanic_id")


class GamePublishersLinkMapper(BaseGameLinkMapper):
    def __init__(self) -> None:
        super().__init__(table_name="game_publishers", entity_id_column="publisher_id")