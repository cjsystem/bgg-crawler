# python
# infra/db/mapper/genres_mapper.py
from typing import List, Optional, Dict, Set
from sqlalchemy import text
from sqlalchemy.orm import Session

from infra.db.models import Genres, Games


class GenresMapper:
    """ジャンル用マッパー（外部提供のSessionを利用）"""

    def __init__(self) -> None:
        pass

    def search_by_name(self, name_part: str, session: Session) -> List[Genres]:
        return (
            session.query(Genres)
            .filter(Genres.name.like(f"%{name_part}%"))
            .all()
        )

    def get_games_by_genre(self, genre_id: int, session: Session) -> List[Games]:
        genre = session.query(Genres).filter(Genres.id == genre_id).first()
        return list(genre.game) if genre else []

    def link_to_game(self, genre_id: int, game_id: int, session: Session) -> bool:
        genre = session.query(Genres).filter(Genres.id == genre_id).first()
        game = session.query(Games).filter(Games.id == game_id).first()
        if genre and game:
            if game not in genre.game:
                genre.game.append(game)
            return True
        return False

    def unlink_from_game(self, genre_id: int, game_id: int, session: Session) -> bool:
        genre = session.query(Genres).filter(Genres.id == genre_id).first()
        game = session.query(Games).filter(Games.id == game_id).first()
        if genre and game and game in genre.game:
            genre.game.remove(game)
            return True
        return False

    def get_genres_by_names(self, names: Set[str], session: Session) -> List[Genres]:
        if not names:
            return []
        return session.query(Genres).filter(Genres.name.in_(names)).all()

    def bulk_create_genres(self, data_list: List[dict], session: Session) -> List[Genres]:
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
                INSERT INTO genres (name, bgg_url)
                VALUES (:name, :bgg_url)
                ON CONFLICT (name) DO UPDATE
                SET bgg_url = CASE
                    WHEN genres.bgg_url IS NULL AND EXCLUDED.bgg_url IS NOT NULL
                    THEN EXCLUDED.bgg_url
                    ELSE genres.bgg_url
                END
            """),
            rows
        )
        return session.query(Genres).filter(Genres.name.in_(names)).all()

    def get_all_name_to_id_mapping(self, session: Session) -> Dict[str, int]:
        rows = session.query(Genres.name, Genres.id).all()
        return {name: id_ for name, id_ in rows}

    def get_by_name(self, name: str, session: Session) -> Optional[Genres]:
        return session.query(Genres).filter(Genres.name == name).first()