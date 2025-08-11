from adapter.service.bgg_game_parser_service_impl import BGGGameParserServiceImpl
from infra.http.selenium_http_client import SeleniumHttpClient


def test_parse_game_with_service():
    """BGGGameParserServiceImplを使ったテスト"""
    # HTTPクライアントを初期化
    with SeleniumHttpClient(headless=True, save_html=True) as http_client:
        # パーサーサービスを初期化
        parser_service = BGGGameParserServiceImpl(http_client)

        # テスト用のBGG ID
        test_bgg_id = 224517  # Brass: Birmingham

        print(f"BGG ID {test_bgg_id} を解析中...")

        # パース処理を実行
        #http_client.get_html("https://boardgamegeek.com/boardgame/224517/brass-birmingham/credits")

        # game = parser_service.parse_game(test_bgg_id)
        # print(game)
        ttt = parser_service.parse_ranking_ids(1)
        print(len(ttt))
        print(ttt)
        #
        # if game:
        #     print(f"\nゲーム名: {game.primary_name}")
        #     print(f"リリース年: {game.year_released}")
        #     print(f"平均評価: {game.avg_rating}")
        #     print(f"評価数: {game.ratings_count}")
        #     print(f"コメント数: {game.comments_count}")
        #     print(f"プレイヤー数: {game.min_players}-{game.max_players}")
        #     print(f"プレイ時間: {game.min_playtime}-{game.max_playtime}")
        #     print(f"推奨年齢: {game.min_age}+")
        #     print(f"重量: {game.weight}")
        #     print(f"総合ランク: {game.rank_overall}")
        #     print(f"ベストプレイヤー数: {game.game_best_player_counts}")
        #     print(f"受賞数: {len(game.game_awards)}")
        #     print(f"ジャンルランク数: {len(game.game_genre_ranks)}")
        #
        #     # 受賞情報の詳細
        #     print("\n受賞歴:")
        #     for award in game.game_awards:
        #         print(f"  - {award.award_year} {award.award_name} ({award.award_type})")
        #
        #     # ジャンルランク情報の詳細
        #     print("\nジャンルランク:")
        #     for genre_rank in game.game_genre_ranks:
        #         print(f"  - {genre_rank.genre.name}: {genre_rank.rank_in_genre}位")
        # else:
        #     print(f"❌ パースに失敗しました BGG ID: {test_bgg_id}")


if __name__ == "__main__":
    test_parse_game_with_service()