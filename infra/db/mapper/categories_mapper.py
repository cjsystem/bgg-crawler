# python
# infra/db/mapper/categories_mapper.py
from typing import List, Optional, Dict, Set
from sqlalchemy import text
from sqlalchemy.orm import Session

from infra.db.models import Categories, Games


class CategoriesMapper:
    """カテゴリ用マッパー（外部提供のSessionを利用）"""

    def __init__(self) -> None:
        pass

    def search_by_name(self, name_part: str, session: Session) -> List[Categories]:
        return (
            session.query(Categories)
            .filter(Categories.name.like(f"%{name_part}%"))
            .all()
        )

    def get_games_by_category(self, category_id: int, session: Session) -> List[Games]:
        cat = session.query(Categories).filter(Categories.id == category_id).first()
        return list(cat.game) if cat else []

    def link_to_game(self, category_id: int, game_id: int, session: Session) -> bool:
        cat = session.query(Categories).filter(Categories.id == category_id).first()
        game = session.query(Games).filter(Games.id == game_id).first()
        if cat and game:
            if game not in cat.game:
                cat.game.append(game)
            return True
        return False

    def unlink_from_game(self, category_id: int, game_id: int, session: Session) -> bool:
        cat = session.query(Categories).filter(Categories.id == category_id).first()
        game = session.query(Games).filter(Games.id == game_id).first()
        if cat and game and game in cat.game:
            cat.game.remove(game)
            return True
        return False

    def get_categories_by_names(self, names: Set[str], session: Session) -> List[Categories]:
        if not names:
            return []
        return session.query(Categories).filter(Categories.name.in_(names)).all()

    def bulk_create_categories(self, data_list: List[dict], session: Session) -> List[Categories]:
        if not data_list:
            return []

        dedup: Dict[str, dict] = {}
        for row in data_list:
            name = row.get("name")
            if not name:
                continue
            dedup[name] = {"name": name, "bgg_url": row.get("bgg_url")}

        rows = list(dedup.values())
        names = set(dedup.keys())

        session.execute(
            text("""
                INSERT INTO categories (name, bgg_url)
                VALUES (:name, :bgg_url)
                ON CONFLICT (name) DO UPDATE
                SET bgg_url = CASE
                    WHEN categories.bgg_url IS NULL AND EXCLUDED.bgg_url IS NOT NULL
                    THEN EXCLUDED.bgg_url
                    ELSE categories.bgg_url
                END
            """),
            rows
        )
        return session.query(Categories).filter(Categories.name.in_(names)).all()

    def get_all_name_to_id_mapping(self, session: Session) -> Dict[str, int]:
        rows = session.query(Categories.name, Categories.id).all()
        return {name: id_ for name, id_ in rows}

    def get_by_name(self, name: str, session: Session) -> Optional[Categories]:
        return session.query(Categories).filter(Categories.name == name).first()