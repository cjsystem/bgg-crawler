from adapter.bgg_game_main_parser import BGGGameMainParser


def test_parse_html():
    """HTMLパーサーのテスト"""
    # HTMLファイルを読み込み
    with open('output/bgg_224517_20250809_232946.html', 'r', encoding='utf-8') as f:
        html_content = f.read()

    # パース実行
    game = BGGGameMainParser.parse_game_from_html(html_content, 224517)

    if game:
        print(f"ゲーム名: {game.primary_name}")
        print(f"リリース年: {game.year_released}")
        print(f"平均評価: {game.avg_rating}")
        print(f"評価数: {game.ratings_count}")
        print(f"コメント数: {game.comments_count}")
        print(f"プレイヤー数: {game.min_players}-{game.max_players}")
        print(f"プレイ時間: {game.min_playtime}-{game.max_playtime}")
        print(f"推奨年齢: {game.min_age}+")
        print(f"重量: {game.weight}")
        print(f"総合ランク: {game.rank_overall}")
        print(f"ベストプレイヤー数: {game.game_best_player_counts}")
        print(f"受賞数: {len(game.game_awards)}")
        print(f"ジャンルランク数: {len(game.game_genre_ranks)}")

        # 受賞情報の詳細
        for award in game.game_awards:
            print(f"  - {award.award_year} {award.award_name} ({award.award_type})")

        # ジャンルランク情報の詳細
        for genre_rank in game.game_genre_ranks:
            print(f"  - {genre_rank.genre.name}: {genre_rank.rank_in_genre}位")


if __name__ == "__main__":
    test_parse_html()