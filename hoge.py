# python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TargetGamesMapper + db.py の動作確認スクリプト

テスト内容:
1) テストデータの投入（target_games に数件 INSERT）
2) list_all / list_all_bgg_ids の動作確認
3) get_by_bgg_id の動作確認
4) クリーンアップ（任意）
"""

import os
import sys
import random
from datetime import datetime
from typing import List

from dotenv import load_dotenv

# 必要なコンポーネントをインポート
from infra.db.base.db import SessionLocal
from infra.db.mapper.target_games_mapper import TargetGamesMapper
from infra.db.models import TargetGames


def check_environment() -> bool:
    """環境と依存の確認"""
    print("=== 環境設定確認 ===")
    load_dotenv()

    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL が未設定です")
        return False
    print(f"✓ DATABASE_URL: {database_url[:50]}...")

    try:
        import sqlalchemy
        print(f"✓ SQLAlchemy: {sqlalchemy.__version__}")
    except Exception as e:
        print(f"❌ SQLAlchemy が見つかりません: {e}")
        return False

    return True


def print_separator(title: str):
    print("\n" + "=" * 70)
    print(f" {title} ")
    print("=" * 70)


def gen_test_bgg_ids(n: int = 3) -> List[int]:
    """重複を避けるため大きめのランダムBGG IDを生成"""
    ids = set()
    while len(ids) < n:
        ids.add(random.randint(900000, 999999))
    return list(ids)


def main():
    print("TargetGamesMapper + db.py 動作確認")
    print(f"Python: {sys.version}")

    if not check_environment():
        return

    mapper = TargetGamesMapper()
    test_ids = gen_test_bgg_ids(4)

    # 1セッション・1トランザクションで処理
    session = SessionLocal()
    try:
        with session.begin():
            print_separator("1) 事前クリーンアップ（同一BGG IDを削除）")
            session.query(TargetGames).filter(TargetGames.bgg_id.in_(test_ids)).delete(synchronize_session=False)
            print(f"✓ 既存のテスト対象行を削除（BGG IDs: {test_ids}）")

            print_separator("2) テストデータ投入")
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            rows = [
                TargetGames(bgg_id=test_ids[0], memo=f"inserted at {now} #1"),
                TargetGames(bgg_id=test_ids[1], memo=f"inserted at {now} #2"),
                TargetGames(bgg_id=test_ids[2], memo=f"inserted at {now} #3"),
                TargetGames(bgg_id=test_ids[3], memo=None),
            ]
            session.add_all(rows)
            # commitは with session.begin() に任せる
            print(f"✓ 挿入行数: {len(rows)}")

            print_separator("3) list_all の確認")
            all_rows = mapper.list_all(session=session)
            print(f"✓ 取得件数: {len(all_rows)}")
            # 直近投入分を表示（created_at昇順のため末尾にあるとは限らないためフィルタ）
            for r in filter(lambda x: x.bgg_id in test_ids, all_rows):
                print(f"  - BGG ID={r.bgg_id}, memo={r.memo}, created_at={r.created_at}")

            print_separator("4) list_all_bgg_ids の確認")
            bgg_ids = mapper.list_all_bgg_ids(session=session)
            print(f"✓ BGG ID総数: {len(bgg_ids)}")
            contained = [x for x in test_ids if x in bgg_ids]
            print(f"✓ テスト挿入分が含まれる件数: {len(contained)}/{len(test_ids)}")
            for x in contained:
                print(f"  - 含まれる: {x}")

            print_separator("5) get_by_bgg_id の確認")
            target_id = test_ids[0]
            row = mapper.get_by_bgg_id(target_id, session=session)
            if row:
                print(f"✓ BGG ID={target_id} を取得: memo={row.memo}, created_at={row.created_at}")
            else:
                print(f"❌ BGG ID={target_id} が取得できませんでした")

        print_separator("6) コミット完了")
        print("✓ トランザクションが正常にコミットされました")

    except Exception as e:
        print(f"❌ エラー: {e}")
        # with session.begin() 内の例外は自動でrollbackされます
    finally:
        session.close()

    # 別セッションで再確認＆クリーンアップ選択
    session2 = SessionLocal()
    try:
        with session2.begin():
            print_separator("7) 別セッションで再確認")
            again = session2.query(TargetGames).filter(TargetGames.bgg_id.in_(test_ids)).all()
            print(f"✓ 残存テスト行: {len(again)}")
            for r in again:
                print(f"  - BGG ID={r.bgg_id}, memo={r.memo}, created_at={r.created_at}")

            print_separator("8) クリーンアップ（任意）")
            choice = input("テストデータを削除しますか？ (y/N): ").strip().lower()
            if choice in ("y", "yes"):
                deleted = session2.query(TargetGames).filter(TargetGames.bgg_id.in_(test_ids)) \
                    .delete(synchronize_session=False)
                print(f"✓ 削除件数: {deleted}")
            else:
                print("テストデータは保持します。")
    finally:
        session2.close()

    print_separator("完了")
    print("🎉 すべての確認が完了しました")


if __name__ == "__main__":
    main()