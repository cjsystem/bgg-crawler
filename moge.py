# -*- coding: utf-8 -*-
# ファイル例: scripts/verify_parse_game_selenium.py

import logging
import sys
from typing import Optional

# 既存モジュールのパスはプロジェクト構成に合わせて調整してください
from adapter.service.bgg_game_parser_service_impl import (
    BGGGameParserServiceImpl,
    BGGParseException,
    BGGFetchException,
)
from infra.http.selenium_http_client import SeleniumHttpClient


def _to_names(seq) -> list[str]:
    if not seq:
        return []
    names = []
    for x in seq:
        name = getattr(x, "name", None)
        if not name:
            name = str(x)
        names.append(name)
    return names


def main():
    logging.basicConfig(
        level=logging.INFO,  # さらに詳しく見る場合は DEBUG に
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )
    logger = logging.getLogger("parse_game_check_selenium")

    target_bgg_id = 224517
    user_agent = "BGGGameCrawler/1.0 (+contact: <contact@example.com>)"

    # 重要: SeleniumHttpClient を使用
    # - headless=False: 初回デバッグ時は画面を見られるように
    # - save_html=True: 取得したHTMLを保存（output ディレクトリ）
    # - timeout を少し長め、追加待機は実装側で指定されるのでここでは設定不要
    with SeleniumHttpClient(
        headless=False,
        timeout=20,
        user_agent=user_agent,
        save_html=True,
        output_dir="output",
    ) as http_client:
        service = BGGGameParserServiceImpl(
            http_client=http_client,
            timeout=30,
            user_agent=user_agent,
        )

        try:
            logger.info(f"parse_game({target_bgg_id}) を実行します")
            game = service.parse_game(target_bgg_id)
        except (BGGFetchException, BGGParseException) as e:
            logger.error(f"パースに失敗しました: {e}")
            sys.exit(2)
        except Exception as e:
            logger.exception(f"想定外のエラーが発生しました: {e}")
            sys.exit(3)

        if game is None:
            logger.error("Game が None でした（取得に失敗）")
            sys.exit(1)

        # 取得結果の表示
        print("=== Parsed Game ===")
        print(f"bgg_id: {getattr(game, 'bgg_id', None)}")
        print(f"primary_name: {getattr(game, 'primary_name', None)}")
        print(f"japanese_name: {getattr(game, 'japanese_name', None)}")
        print(f"year_released: {getattr(game, 'year_released', None)}")
        print(f"min_players: {getattr(game, 'min_players', None)}")
        print(f"max_players: {getattr(game, 'max_players', None)}")
        print(f"min_playtime: {getattr(game, 'min_playtime', None)}")
        print(f"max_playtime: {getattr(game, 'max_playtime', None)}")
        print(f"min_age: {getattr(game, 'min_age', None)}")
        print(f"avg_rating: {getattr(game, 'avg_rating', None)}")
        print(f"ratings_count: {getattr(game, 'ratings_count', None)}")
        print(f"comments_count: {getattr(game, 'comments_count', None)}")
        print(f"weight: {getattr(game, 'weight', None)}")
        print(f"rank_overall: {getattr(game, 'rank_overall', None)}")

        designers = _to_names(getattr(game, "designers", []))
        artists = _to_names(getattr(game, "artists", []))
        publishers = _to_names(getattr(game, "publishers", []))
        categories = _to_names(getattr(game, "categories", []))
        mechanics = _to_names(getattr(game, "mechanics", []))

        print(f"designers({len(designers)}): {', '.join(designers[:5])}{' ...' if len(designers) > 5 else ''}")
        print(f"artists({len(artists)}): {', '.join(artists[:5])}{' ...' if len(artists) > 5 else ''}")
        print(f"publishers({len(publishers)}): {', '.join(publishers[:5])}{' ...' if len(publishers) > 5 else ''}")
        print(f"categories({len(categories)}): {', '.join(categories[:5])}{' ...' if len(categories) > 5 else ''}")
        print(f"mechanics({len(mechanics)}): {', '.join(mechanics[:5])}{' ...' if len(mechanics) > 5 else ''}")

        print("\n完了: parse_game の実行に成功しました。")
        print("HTMLは output ディレクトリに保存されています（save_html=True の場合）。")
        print(game)


if __name__ == "__main__":
    main()