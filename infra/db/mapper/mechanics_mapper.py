# python
# infra/db/mapper/mechanics_mapper.py
from typing import List, Optional, Dict, Set
from sqlalchemy import text
from sqlalchemy.orm import Session

from infra.db.models import Mechanics, Games


class MechanicsMapper:
    """メカニクス用マッパー（外部提供のSessionを利用）"""

    def __init__(self) -> None:
        pass

    def search_by_name(self, name_part: str, session: Session) -> List[Mechanics]:
        return (
            session.query(Mechanics)
            .filter(Mechanics.name.like(f"%{name_part}%"))
            .all()
        )

    def get_games_by_mechanic(self, mechanic_id: int, session: Session) -> List[Games]:
        mech = session.query(Mechanics).filter(Mechanics.id == mechanic_id).first()
        return list(mech.game) if mech else []

    def link_to_game(self, mechanic_id: int, game_id: int, session: Session) -> bool:
        mech = session.query(Mechanics).filter(Mechanics.id == mechanic_id).first()
        game = session.query(Games).filter(Games.id == game_id).first()
        if mech and game:
            if game not in mech.game:
                mech.game.append(game)
            return True
        return False

    def unlink_from_game(self, mechanic_id: int, game_id: int, session: Session) -> bool:
        mech = session.query(Mechanics).filter(Mechanics.id == mechanic_id).first()
        game = session.query(Games).filter(Games.id == game_id).first()
        if mech and game and game in mech.game:
            mech.game.remove(game)
            return True
        return False

    def get_mechanics_by_names(self, names: Set[str], session: Session) -> List[Mechanics]:
        if not names:
            return []
        return session.query(Mechanics).filter(Mechanics.name.in_(names)).all()

    def bulk_create_mechanics(self, data_list: List[dict], session: Session) -> List[Mechanics]:
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
                INSERT INTO mechanics (name, bgg_url)
                VALUES (:name, :bgg_url)
                ON CONFLICT (name) DO UPDATE
                SET bgg_url = CASE
                    WHEN mechanics.bgg_url IS NULL AND EXCLUDED.bgg_url IS NOT NULL
                    THEN EXCLUDED.bgg_url
                    ELSE mechanics.bgg_url
                END
            """),
            rows
        )
        return session.query(Mechanics).filter(Mechanics.name.in_(names)).all()

    def get_all_name_to_id_mapping(self, session: Session) -> Dict[str, int]:
        rows = session.query(Mechanics.name, Mechanics.id).all()
        return {name: id_ for name, id_ in rows}

    def get_by_name(self, name: str, session: Session) -> Optional[Mechanics]:
        return session.query(Mechanics).filter(Mechanics.name == name).first()