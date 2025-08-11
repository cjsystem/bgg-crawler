# python
# infra/db/mapper/awards_mapper.py
from typing import List, Optional, Dict, Set, Tuple
from sqlalchemy import text, tuple_
from sqlalchemy.orm import Session

from infra.db.models import Awards, Games


UniqueKey = Tuple[str, int, str, Optional[str]]  # (award_name, award_year, award_type, award_category)


class AwardsMapper:
    """受賞(Awards)用マッパー（外部提供のSessionを利用）"""

    def __init__(self) -> None:
        # 状態は持たない
        pass

    # 検索まわり

    def search_by_name(self, name_part: str, session: Session) -> List[Awards]:
        """賞の名前の部分一致で検索"""
        return (
            session.query(Awards)
            .filter(Awards.award_name.like(f"%{name_part}%"))
            .all()
        )

    def get_by_unique_key(
        self,
        award_name: str,
        award_year: int,
        award_type: str,
        award_category: Optional[str],
        session: Session,
    ) -> Optional[Awards]:
        """複合キーで1件取得"""
        q = (
            session.query(Awards)
            .filter(Awards.award_name == award_name)
            .filter(Awards.award_year == award_year)
            .filter(Awards.award_type == award_type)
        )
        if award_category is None:
            q = q.filter(Awards.award_category.is_(None))
        else:
            q = q.filter(Awards.award_category == award_category)
        return q.first()

    def get_awards_by_unique_keys(
        self,
        keys: Set[UniqueKey],
        session: Session
    ) -> List[Awards]:
        """複合キー集合で複数取得"""
        if not keys:
            return []
        # SQL の (col1, col2, col3, col4) IN ((...), (...)) を使用
        return (
            session.query(Awards)
            .filter(
                tuple_(
                    Awards.award_name,
                    Awards.award_year,
                    Awards.award_type,
                    Awards.award_category,
                ).in_(list(keys))
            )
            .all()
        )

    def get_all_key_to_id_mapping(self, session: Session) -> Dict[UniqueKey, int]:
        """全受賞の (name, year, type, category) → id マッピング"""
        rows = session.query(
            Awards.award_name,
            Awards.award_year,
            Awards.award_type,
            Awards.award_category,
            Awards.id
        ).all()
        return {(n, y, t, c): id_ for n, y, t, c, id_ in rows}

    # ゲーム関連取得・関連付け

    def get_games_by_award(self, award_id: int, session: Session) -> List[Games]:
        """受賞に紐づくゲーム一覧"""
        award = session.query(Awards).filter(Awards.id == award_id).first()
        return list(award.game) if award else []

    def link_to_game(self, award_id: int, game_id: int, session: Session) -> bool:
        """受賞とゲームを関連付け（commitは呼び出し側）"""
        award = session.query(Awards).filter(Awards.id == award_id).first()
        game = session.query(Games).filter(Games.id == game_id).first()
        if award and game:
            if game not in award.game:
                award.game.append(game)
            return True
        return False

    def unlink_from_game(self, award_id: int, game_id: int, session: Session) -> bool:
        """受賞とゲームの関連を削除（commitは呼び出し側）"""
        award = session.query(Awards).filter(Awards.id == award_id).first()
        game = session.query(Games).filter(Games.id == game_id).first()
        if award and game and game in award.game:
            award.game.remove(game)
            return True
        return False

    # 一括作成（UPSERT）

    def bulk_create_awards(self, award_data_list: List[dict], session: Session) -> List[Awards]:
        """複数受賞を一括作成（UPSERT）し、作成/更新後のレコードを返す
        - ここでは commit は行わない（呼び出し側でまとめて行う）
        - 一意性は (award_name, award_year, award_type, award_category)
        - bgg_url は既存がNULLのときのみ新値で更新
        受け取る dict 例:
          {
            "award_name": "Spiel des Jahres",
            "award_year": 2020,
            "award_type": "Winner",
            "award_category": None,    # 任意
            "bgg_url": "https://..."   # 任意
          }
        """
        if not award_data_list:
            return []

        # 複合キーで重複排除（最後の bgg_url を優先）
        dedup: Dict[UniqueKey, dict] = {}
        for row in award_data_list:
            name = row.get("award_name")
            year = row.get("award_year")
            a_type = row.get("award_type")
            category = row.get("award_category")
            if not name or year is None or not a_type:
                # 必須キー不足はスキップ
                continue
            key: UniqueKey = (name, int(year), a_type, category)
            dedup[key] = {
                "award_name": name,
                "award_year": int(year),
                "award_type": a_type,
                "award_category": category,
                "bgg_url": row.get("bgg_url"),
            }

        rows = list(dedup.values())
        keys: Set[UniqueKey] = set(dedup.keys())
        if not rows:
            return []

        # ON CONFLICT で bgg_url を条件付き更新
        session.execute(
            text("""
                INSERT INTO awards (
                    award_name, award_year, award_type, award_category, bgg_url
                )
                VALUES (:award_name, :award_year, :award_type, :award_category, :bgg_url)
                ON CONFLICT (award_name, award_year, award_type, award_category)
                DO UPDATE SET
                    bgg_url = CASE
                        WHEN awards.bgg_url IS NULL AND EXCLUDED.bgg_url IS NOT NULL
                        THEN EXCLUDED.bgg_url
                        ELSE awards.bgg_url
                    END
            """),
            rows
        )

        # 返却用に SELECT（複合キーINで厳密に抽出）
        return self.get_awards_by_unique_keys(keys, session)