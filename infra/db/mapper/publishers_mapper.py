# python
# infra/db/mapper/publishers_mapper.py
from typing import List, Optional, Dict, Set
from sqlalchemy import text
from sqlalchemy.orm import Session

from infra.db.models import Publishers, Games


class PublishersMapper:
    """パブリッシャー用マッパー（外部提供のSessionを利用）"""

    def __init__(self) -> None:
        pass

    def search_by_name(self, name_part: str, session: Session) -> List[Publishers]:
        return (
            session.query(Publishers)
            .filter(Publishers.name.like(f"%{name_part}%"))
            .all()
        )

    def get_games_by_publisher(self, publisher_id: int, session: Session) -> List[Games]:
        publisher = session.query(Publishers).filter(Publishers.id == publisher_id).first()
        return list(publisher.game) if publisher else []

    def link_to_game(self, publisher_id: int, game_id: int, session: Session) -> bool:
        publisher = session.query(Publishers).filter(Publishers.id == publisher_id).first()
        game = session.query(Games).filter(Games.id == game_id).first()
        if publisher and game:
            if game not in publisher.game:
                publisher.game.append(game)
            return True
        return False

    def unlink_from_game(self, publisher_id: int, game_id: int, session: Session) -> bool:
        publisher = session.query(Publishers).filter(Publishers.id == publisher_id).first()
        game = session.query(Games).filter(Games.id == game_id).first()
        if publisher and game and game in publisher.game:
            publisher.game.remove(game)
            return True
        return False

    def get_publishers_by_names(self, names: Set[str], session: Session) -> List[Publishers]:
        if not names:
            return []
        return session.query(Publishers).filter(Publishers.name.in_(names)).all()

    def bulk_create_publishers(self, data_list: List[dict], session: Session) -> List[Publishers]:
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
                INSERT INTO publishers (name, bgg_url)
                VALUES (:name, :bgg_url)
                ON CONFLICT (name) DO UPDATE
                SET bgg_url = CASE
                    WHEN publishers.bgg_url IS NULL AND EXCLUDED.bgg_url IS NOT NULL
                    THEN EXCLUDED.bgg_url
                    ELSE publishers.bgg_url
                END
            """),
            rows
        )
        return session.query(Publishers).filter(Publishers.name.in_(names)).all()

    def get_all_name_to_id_mapping(self, session: Session) -> Dict[str, int]:
        rows = session.query(Publishers.name, Publishers.id).all()
        return {name: id_ for name, id_ in rows}

    def get_by_name(self, name: str, session: Session) -> Optional[Publishers]:
        return session.query(Publishers).filter(Publishers.name == name).first()