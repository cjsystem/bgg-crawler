# python
# infra/db/mapper/designers_mapper.py
from typing import List, Optional, Dict, Set
from sqlalchemy import text
from sqlalchemy.orm import Session

from infra.db.models import Designers, Games


class DesignersMapper:
    """デザイナー用マッパー（外部提供のSessionを利用）"""

    def __init__(self) -> None:
        pass

    def search_by_name(self, name_part: str, session: Session) -> List[Designers]:
        return (
            session.query(Designers)
            .filter(Designers.name.like(f"%{name_part}%"))
            .all()
        )

    def get_games_by_designer(self, designer_id: int, session: Session) -> List[Games]:
        designer = session.query(Designers).filter(Designers.id == designer_id).first()
        return list(designer.game) if designer else []

    def link_to_game(self, designer_id: int, game_id: int, session: Session) -> bool:
        designer = session.query(Designers).filter(Designers.id == designer_id).first()
        game = session.query(Games).filter(Games.id == game_id).first()
        if designer and game:
            if game not in designer.game:
                designer.game.append(game)
            return True
        return False

    def unlink_from_game(self, designer_id: int, game_id: int, session: Session) -> bool:
        designer = session.query(Designers).filter(Designers.id == designer_id).first()
        game = session.query(Games).filter(Games.id == game_id).first()
        if designer and game and game in designer.game:
            designer.game.remove(game)
            return True
        return False

    def get_designers_by_names(self, names: Set[str], session: Session) -> List[Designers]:
        if not names:
            return []
        return session.query(Designers).filter(Designers.name.in_(names)).all()

    def bulk_create_designers(self, data_list: List[dict], session: Session) -> List[Designers]:
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
                INSERT INTO designers (name, bgg_url)
                VALUES (:name, :bgg_url)
                ON CONFLICT (name) DO UPDATE
                SET bgg_url = CASE
                    WHEN designers.bgg_url IS NULL AND EXCLUDED.bgg_url IS NOT NULL
                    THEN EXCLUDED.bgg_url
                    ELSE designers.bgg_url
                END
            """),
            rows
        )
        return session.query(Designers).filter(Designers.name.in_(names)).all()

    def get_all_name_to_id_mapping(self, session: Session) -> Dict[str, int]:
        rows = session.query(Designers.name, Designers.id).all()
        return {name: id_ for name, id_ in rows}

    def get_by_name(self, name: str, session: Session) -> Optional[Designers]:
        return session.query(Designers).filter(Designers.name == name).first()