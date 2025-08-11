# infra/db/mapper/artists_mapper.py
from typing import List, Optional, Dict, Set
from sqlalchemy import text
from sqlalchemy.orm import Session

from infra.db.models import Artists, Games


class ArtistsMapper:
    """アーティスト用マッパー（外部提供のSessionを利用）"""

    def __init__(self) -> None:
        # 特に状態は持たない（必要ならDIで設定を受け取る）
        pass

    def search_by_name(self, name_part: str, session: Session) -> List[Artists]:
        """名前の部分一致でアーティストを検索"""
        return (
            session.query(Artists)
            .filter(Artists.name.like(f"%{name_part}%"))
            .all()
        )

    def get_games_by_artist(self, artist_id: int, session: Session) -> List[Games]:
        """アーティストが関わったゲームを取得"""
        artist = session.query(Artists).filter(Artists.id == artist_id).first()
        return list(artist.game) if artist else []

    def link_to_game(self, artist_id: int, game_id: int, session: Session) -> bool:
        """アーティストをゲームに関連付け（commitは呼び出し側）"""
        artist = session.query(Artists).filter(Artists.id == artist_id).first()
        game = session.query(Games).filter(Games.id == game_id).first()
        if artist and game:
            if game not in artist.game:
                artist.game.append(game)
                # 呼び出し側でcommit
            return True
        return False

    def unlink_from_game(self, artist_id: int, game_id: int, session: Session) -> bool:
        """アーティストとゲームの関連を削除（commitは呼び出し側）"""
        artist = session.query(Artists).filter(Artists.id == artist_id).first()
        game = session.query(Games).filter(Games.id == game_id).first()
        if artist and game and game in artist.game:
            artist.game.remove(game)
            # 呼び出し側でcommit
            return True
        return False

    def get_artists_by_names(self, names: Set[str], session: Session) -> List[Artists]:
        """名前のセットで複数アーティストを取得"""
        if not names:
            return []
        return session.query(Artists).filter(Artists.name.in_(names)).all()

    def bulk_create_artists(self, artist_data_list: List[dict], session: Session) -> List[Artists]:
        """複数アーティストを一括作成（UPSERT）し、作成/更新後のレコードを返却
        - ここではcommitは行わない（呼び出し側でまとめて行う）
        """
        if not artist_data_list:
            return []

        # name重複を排除しつつ最後のbgg_urlを採用
        dedup: Dict[str, dict] = {}
        for row in artist_data_list:
            name = row.get('name')
            if not name:
                continue
            dedup[name] = {'name': name, 'bgg_url': row.get('bgg_url')}

        rows = list(dedup.values())
        names = set(dedup.keys())

        # ON CONFLICTでbgg_urlがNULLの場合のみ更新
        session.execute(
            text("""
                 INSERT INTO artists (name, bgg_url)
                 VALUES (:name, :bgg_url)
                 ON CONFLICT (name) DO UPDATE
                 SET bgg_url = CASE
                     WHEN artists.bgg_url IS NULL AND EXCLUDED.bgg_url IS NOT NULL
                     THEN EXCLUDED.bgg_url
                     ELSE artists.bgg_url
                 END
            """),
            rows
        )

        # 返却用にSELECT（expire/close/commitはしない）
        return session.query(Artists).filter(Artists.name.in_(names)).all()

    def get_all_name_to_id_mapping(self, session: Session) -> Dict[str, int]:
        """全アーティストの name → id マッピングを取得"""
        rows = session.query(Artists.name, Artists.id).all()
        return {name: id_ for name, id_ in rows}

    # 追加で使う可能性のあるヘルパー
    def get_by_name(self, name: str, session: Session) -> Optional[Artists]:
        """名前で単一アーティストを取得"""
        return session.query(Artists).filter(Artists.name == name).first()