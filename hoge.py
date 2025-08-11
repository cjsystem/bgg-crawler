# python
#!/usr/bin/env python3
import argparse
from decimal import Decimal
from typing import List, Dict, Any

from infra.db.base.db import session_scope
from infra.db.games_repository_impl import GamesRepositoryImpl

# 確認用（読み出し/名称解決など）
from infra.db.mapper.artists_mapper import ArtistsMapper
from infra.db.mapper.base_game_link_mapper import GameDesignersLinkMapper, GameArtistsLinkMapper, \
    GamePublishersLinkMapper, GameCategoriesLinkMapper, GameMechanicsLinkMapper, GameAwardsLinkMapper
from infra.db.mapper.designers_mapper import DesignersMapper
from infra.db.mapper.publishers_mapper import PublishersMapper
from infra.db.mapper.categories_mapper import CategoriesMapper
from infra.db.mapper.mechanics_mapper import MechanicsMapper
from infra.db.mapper.game_genre_ranks_mapper import GameGenreRanksMapper
from infra.db.mapper.game_best_player_counts_mapper import GameBestPlayerCountsMapper

# ORMモデル（行の中身確認用）
from infra.db.models import Games as GamesRow

# ドメインエンティティ
from domain.game import Game
from domain.artist import Artist
from domain.designer import Designer
from domain.publisher import Publisher
from domain.category import Category
from domain.mechanic import Mechanic
from domain.award import Award
from domain.genre import Genre
from domain.game_genre_rank import GameGenreRank


def _print_header(title: str) -> None:
    print(f"\n=== {title} ===")


def build_game_list() -> List[Game]:
    """動作確認用の Game エンティティ一覧を構築"""
    g1 = Game(
        bgg_id=3001001,
        primary_name="Repo Verify Game 1",
        japanese_name="リポジトリ検証ゲーム1",
        year_released=2020,
        image_url="https://example.com/g1.png",
        avg_rating=Decimal("8.1"),
        ratings_count=12345,
        comments_count=2345,
        min_players=1,
        max_players=4,
        min_playtime=30,
        max_playtime=60,
        min_age=10,
        weight=Decimal("2.50"),
        rank_overall=150,
        designers=[
            Designer(name="Designer A", bgg_url="https://example.com/designer/a"),
            Designer(name="Designer B", bgg_url=None),
        ],
        artists=[
            Artist(name="Artist A", bgg_url=None),
            Artist(name="Artist B", bgg_url="https://example.com/artist/b"),
        ],
        publishers=[
            Publisher(name="Foo Publishing", bgg_url="https://example.com/pub/foo"),
        ],
        categories=[
            Category(name="Card Game", bgg_url=None),
            Category(name="Strategy Game", bgg_url="https://example.com/cat/strategy"),
        ],
        mechanics=[
            Mechanic(name="Deck Building", bgg_url="https://example.com/mech/deck"),
        ],
        awards=[
            Award(
                award_name="Spiel des Jahres",
                award_year=2020,
                award_type="Winner",
                bgg_url="https://example.com/awards/sdj-2020",
            )
        ],
        genre_ranks=[
            GameGenreRank(genre=Genre(name="Strategy", bgg_url="https://example.com/genre/strategy"), rank_in_genre=45)
        ],
        best_player_counts=[2, 3],
    )

    g2 = Game(
        bgg_id=3001002,
        primary_name="Repo Verify Game 2",
        japanese_name=None,
        year_released=2021,
        image_url=None,
        avg_rating=Decimal("7.4"),
        ratings_count=4567,
        comments_count=890,
        min_players=2,
        max_players=5,
        min_playtime=45,
        max_playtime=90,
        min_age=12,
        weight=Decimal("3.20"),
        rank_overall=300,
        designers=[
            Designer(name="Designer B", bgg_url=None),
            Designer(name="Designer C", bgg_url="https://example.com/designer/c"),
        ],
        artists=[
            Artist(name="Artist B", bgg_url="https://example.com/artist/b")
        ],
        publishers=[
            Publisher(name="Bar Publishing", bgg_url=None)
        ],
        categories=[
            Category(name="Strategy Game", bgg_url="https://example.com/cat/strategy")
        ],
        mechanics=[
            Mechanic(name="Area Control", bgg_url=None)
        ],
        awards=[
            Award(
                award_name="Kennerspiel des Jahres",
                award_year=2021,
                award_type="Nominee",
                bgg_url=None,
            )
        ],
        genre_ranks=[
            GameGenreRank(genre=Genre(name="Family", bgg_url="https://example.com/genre/family"), rank_in_genre=120)
        ],
        best_player_counts=[3, 4, 5],
    )

    return [g1, g2]


def verify_persisted_data(bgg_id_to_game_id: Dict[int, int]) -> None:
    """DBに保存された内容をダンプして軽く検証"""
    designers = DesignersMapper()
    artists = ArtistsMapper()
    publishers = PublishersMapper()
    categories = CategoriesMapper()
    mechanics = MechanicsMapper()
    genre_ranks = GameGenreRanksMapper()
    best_players = GameBestPlayerCountsMapper()

    link_designers = GameDesignersLinkMapper()
    link_artists = GameArtistsLinkMapper()
    link_publishers = GamePublishersLinkMapper()
    link_categories = GameCategoriesLinkMapper()
    link_mechanics = GameMechanicsLinkMapper()
    # awards のリンクはID列表示に留める
    link_awards = GameAwardsLinkMapper()

    with session_scope() as session:
        # name -> id を逆引き用に id -> name へ
        def invert(d: Dict[str, int]) -> Dict[int, str]:
            return {v: k for k, v in d.items()}

        id_to_designer = invert(designers.get_all_name_to_id_mapping(session))
        id_to_artist = invert(artists.get_all_name_to_id_mapping(session))
        id_to_publisher = invert(publishers.get_all_name_to_id_mapping(session))
        id_to_category = invert(categories.get_all_name_to_id_mapping(session))
        id_to_mechanic = invert(mechanics.get_all_name_to_id_mapping(session))

        for bgg_id, gid in bgg_id_to_game_id.items():
            _print_header(f"Verify game bgg_id={bgg_id}, id={gid}")

            # gamesの非リレーション列を表示
            row: GamesRow = session.query(GamesRow).filter(GamesRow.id == gid).first()
            if row:
                print(f"- primary_name={row.primary_name}, year={row.year_released}, rating={row.avg_rating}, players={row.min_players}-{row.max_players}, rank={row.rank_overall}")

            # 紐付け（名称に変換して表示）
            d_ids = link_designers.get_entity_ids_for_game(gid, session)
            a_ids = link_artists.get_entity_ids_for_game(gid, session)
            p_ids = link_publishers.get_entity_ids_for_game(gid, session)
            c_ids = link_categories.get_entity_ids_for_game(gid, session)
            m_ids = link_mechanics.get_entity_ids_for_game(gid, session)
            w_ids = link_awards.get_entity_ids_for_game(gid, session)

            print(f"- designers: {[id_to_designer.get(i, i) for i in d_ids]}")
            print(f"- artists:   {[id_to_artist.get(i, i) for i in a_ids]}")
            print(f"- publishers:{[id_to_publisher.get(i, i) for i in p_ids]}")
            print(f"- categories:{[id_to_category.get(i, i) for i in c_ids]}")
            print(f"- mechanics: {[id_to_mechanic.get(i, i) for i in m_ids]}")
            print(f"- awards(ids): {w_ids}")

            # ジャンルランク
            ranks = genre_ranks.get_genre_ranks_by_game(gid, session)
            print(f"- genre_ranks: {ranks}")

            # ベストプレイヤー数
            counts = best_players.list_counts_by_game(gid, session)
            print(f"- best_player_counts: {counts}")


def main() -> None:
    parser = argparse.ArgumentParser(description="GamesRepositoryImpl 動作確認スクリプト")
    args = parser.parse_args()

    repo = GamesRepositoryImpl()
    game_list = build_game_list()

    print("開始: bulk_create_games")
    bgg_id_to_game_id = repo.bulk_create_games(game_list)
    print("完了: bulk_create_games")

    _print_header("bgg_id -> game.id マッピング")
    for bgg_id, gid in bgg_id_to_game_id.items():
        print(f"- {bgg_id} -> {gid}")

    verify_persisted_data(bgg_id_to_game_id)

    print("\n✅ GamesRepositoryImpl の動作確認が完了しました。")


if __name__ == "__main__":
    main()