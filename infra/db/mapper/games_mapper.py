# python
# infra/db/mapper/games_mapper.py
from __future__ import annotations

from typing import Optional, List, Dict, Any, Iterable, Tuple
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy import and_

from infra.db.models import Games


class GamesMapper:
    """games テーブル用マッパー（非リレーション列のみを対象）
    - トランザクション管理（commit/rollback）は呼び出し側に委譲します
    - 一意キー: bgg_id
    """

    # DB上の編集対象カラム（非リレーション）
    EDITABLE_COLS: Tuple[str, ...] = (
        "bgg_id",
        "primary_name",
        "japanese_name",
        "year_released",
        "image_url",
        "avg_rating",
        "ratings_count",
        "comments_count",
        "min_players",
        "max_players",
        "min_playtime",
        "max_playtime",
        "min_age",
        "weight",
        "rank_overall",
    )

    def _filter_payload(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """許可されたキーのみに絞り込み"""
        return {k: data.get(k) for k in self.EDITABLE_COLS if k in data}

    # 作成・取得・削除

    def create(self, data: Dict[str, Any], session: Session) -> Games:
        """新規作成（必須: bgg_id, primary_name）"""
        payload = self._filter_payload(data)
        if "bgg_id" not in payload or "primary_name" not in payload:
            raise ValueError("bgg_id と primary_name は必須です")

        # bgg_id 重複チェック（ユニーク制約違反を避ける）
        existing = self.get_by_bgg_id(payload["bgg_id"], session)
        if existing:
            raise ValueError(f"bgg_id={payload['bgg_id']} は既に存在します")

        row = Games(**payload)
        session.add(row)
        session.flush()  # id 採番
        return row

    def get_by_id(self, id_: int, session: Session) -> Optional[Games]:
        return session.query(Games).filter(Games.id == id_).first()

    def get_by_bgg_id(self, bgg_id: int, session: Session) -> Optional[Games]:
        return session.query(Games).filter(Games.bgg_id == bgg_id).first()

    def get_many_by_bgg_ids(self, bgg_ids: Iterable[int], session: Session) -> List[Games]:
        ids = list({int(x) for x in bgg_ids or []})
        if not ids:
            return []
        return session.query(Games).filter(Games.bgg_id.in_(ids)).all()

    def delete_by_id(self, id_: int, session: Session) -> bool:
        row = self.get_by_id(id_, session)
        if not row:
            return False
        session.delete(row)
        return True

    # 更新系

    def update_by_id(self, id_: int, updates: Dict[str, Any], session: Session) -> Optional[Games]:
        """指定IDのゲームを部分更新（Noneを渡したカラムはNULLに更新）"""
        row = self.get_by_id(id_, session)
        if not row:
            return None
        payload = self._filter_payload(updates)
        for k, v in payload.items():
            setattr(row, k, v)
        session.flush()
        return row

    def update_by_bgg_id(self, bgg_id: int, updates: Dict[str, Any], session: Session) -> Optional[Games]:
        """bgg_id で部分更新"""
        row = self.get_by_bgg_id(bgg_id, session)
        if not row:
            return None
        payload = self._filter_payload(updates)
        for k, v in payload.items():
            setattr(row, k, v)
        session.flush()
        return row

    def upsert_by_bgg_id(self, data: Dict[str, Any], session: Session) -> Games:
        """bgg_id をキーにUPSERT（存在すれば更新、なければ作成）
        - dataに含まれるキーだけを更新（含まれないカラムは保持）
        """
        payload = self._filter_payload(data)
        if "bgg_id" not in payload:
            raise ValueError("bgg_id は必須です")

        row = self.get_by_bgg_id(payload["bgg_id"], session)
        if row is None:
            if "primary_name" not in payload:
                raise ValueError("新規作成時は primary_name が必須です")
            row = Games(**payload)
            session.add(row)
            session.flush()
            return row

        # 部分更新
        for k, v in payload.items():
            if k == "bgg_id":
                continue
            setattr(row, k, v)
        session.flush()
        return row

    def bulk_upsert_by_bgg_id(self, rows: List[Dict[str, Any]], session: Session) -> List[Games]:
        """bgg_id をキーに複数UPSERT
        - 1件ずつ upsert_by_bgg_id を呼びます（シンプル・安全重視）
        - 呼び出し側でトランザクション管理してください
        """
        out: List[Games] = []
        for r in rows or []:
            out.append(self.upsert_by_bgg_id(r, session))
        return out

    # 簡易検索・一覧

    def search(
        self,
        session: Session,
        name_part: Optional[str] = None,
        year_min: Optional[int] = None,
        year_max: Optional[int] = None,
        rating_min: Optional[Decimal] = None,
        players_min: Optional[int] = None,
        players_max: Optional[int] = None,
        order_by: str = "rank_overall",
        desc: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Games]:
        """条件検索（名前部分一致/年/評価/プレイヤー数など）"""
        q = session.query(Games)

        if name_part:
            q = q.filter(Games.primary_name.like(f"%{name_part}%"))

        if year_min is not None or year_max is not None:
            conds = []
            if year_min is not None:
                conds.append(Games.year_released >= int(year_min))
            if year_max is not None:
                conds.append(Games.year_released <= int(year_max))
            if conds:
                q = q.filter(and_(*conds))

        if rating_min is not None:
            q = q.filter(Games.avg_rating >= rating_min)

        # プレイヤー条件（min/max どちらかが範囲にかかる程度の広めの条件）
        if players_min is not None:
            q = q.filter(Games.max_players >= int(players_min))
        if players_max is not None:
            q = q.filter(Games.min_players <= int(players_max))

        # ソート
        order_attr = getattr(Games, order_by, Games.rank_overall)
        q = q.order_by(order_attr.desc() if desc else order_attr.asc())

        # ページング
        if offset:
            q = q.offset(int(offset))
        if limit:
            q = q.limit(int(limit))

        return q.all()

    def list_recent(self, session: Session, limit: int = 20) -> List[Games]:
        """作成日時の新しい順（created_at DESC）で取得"""
        return (
            session.query(Games)
            .order_by(Games.created_at.desc(), Games.id.desc())
            .limit(int(limit))
            .all()
        )

    # 補助

    def exists_bgg_id(self, bgg_id: int, session: Session) -> bool:
        return self.get_by_bgg_id(bgg_id, session) is not None

    def get_id_map_by_bgg_ids(self, bgg_ids: Iterable[int], session: Session) -> Dict[int, int]:
        """bgg_id -> id のマッピングを返す"""
        rows = (
            session.query(Games.bgg_id, Games.id)
            .filter(Games.bgg_id.in_(list({int(x) for x in bgg_ids or []})))
            .all()
        )
        return {bgg_id: id_ for bgg_id, id_ in rows}

    def list_all_bgg_ids(self, session: Session) -> List[int]:
        """games テーブル内の全 bgg_id を昇順で返す"""
        rows = (
            session.query(Games.bgg_id)
            .order_by(Games.created_at.asc(), Games.id.asc())
            .all()
        )
        return [row[0] for row in rows]
