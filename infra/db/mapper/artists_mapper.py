# crud_artists.py
from ..base.db_mapper_base import DBMapperBase
from typing import List, Optional

from ..models import Artists, Games


class ArtistsMapper(DBMapperBase[Artists]):
    def __init__(self):
        super().__init__(Artists)

    def create_artist(self, name: str) -> Artists:
        """アーティストを作成"""
        return self.create(name=name)

    def get_by_name(self, name: str) -> Optional[Artists]:
        """名前でアーティストを検索"""
        artists = self.filter_by(name=name)
        return artists[0] if artists else None

    def search_by_name(self, name_part: str) -> List[Artists]:
        """名前の部分一致でアーティストを検索"""
        session = self.get_session()
        try:
            return session.query(Artists).filter(
                Artists.name.like(f"%{name_part}%")
            ).all()
        finally:
            session.close()

    def get_games_by_artist(self, artist_id: int) -> List[Games]:
        """アーティストが関わったゲームを取得"""
        session = self.get_session()
        try:
            artist = session.query(Artists).filter(Artists.id == artist_id).first()
            if artist:
                return list(artist.game)
            return []
        finally:
            session.close()

    def link_to_game(self, artist_id: int, game_id: int) -> bool:
        """アーティストをゲームに関連付け"""
        session = self.get_session()
        try:
            artist = session.query(Artists).filter(Artists.id == artist_id).first()
            game = session.query(Games).filter(Games.id == game_id).first()

            if artist and game:
                if game not in artist.game:
                    artist.game.append(game)
                    session.commit()
                return True
            return False
        finally:
            session.close()

    def unlink_from_game(self, artist_id: int, game_id: int) -> bool:
        """アーティストとゲームの関連を削除"""
        session = self.get_session()
        try:
            artist = session.query(Artists).filter(Artists.id == artist_id).first()
            game = session.query(Games).filter(Games.id == game_id).first()

            if artist and game and game in artist.game:
                artist.game.remove(game)
                session.commit()
                return True
            return False
        finally:
            session.close()