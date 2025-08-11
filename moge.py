#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TargetGamesMapperの動作確認用スクリプト

このスクリプトは以下の機能をテストします：
1. 環境設定の確認
2. データベース接続の確認
3. インスタンス作成
4. データの作成（create）
5. 全件取得（list_all）
6. BGG ID一覧取得（list_all_bgg_ids）
7. BGG IDによる検索（get_by_bgg_id）
"""

import sys
import os
from datetime import datetime
from typing import List
import traceback

# 環境変数の確認
from dotenv import load_dotenv

load_dotenv()


def check_environment():
    """環境設定を確認"""
    print("=== 環境設定確認 ===")

    # DATABASE_URLの確認
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URLが設定されていません")
        print("解決方法：")
        print("1. .envファイルにDATABASE_URLを設定してください")
        print("2. 例: DATABASE_URL=postgresql://username:password@host:port/database")
        return False

    print(f"✓ DATABASE_URL: {database_url[:50]}...")

    # psycopg2のインストール確認
    try:
        import psycopg2
        print(f"✓ psycopg2 version: {psycopg2.__version__}")
    except ImportError:
        print("❌ psycopg2がインストールされていません")
        print("解決方法：pip install psycopg2-binary")
        return False

    # SQLAlchemyのインストール確認
    try:
        import sqlalchemy
        print(f"✓ SQLAlchemy version: {sqlalchemy.__version__}")
    except ImportError:
        print("❌ SQLAlchemyがインストールされていません")
        print("解決方法：pip install sqlalchemy")
        return False

    return True


def test_database_connection():
    """データベース接続テスト（低レベル）"""
    print("\n=== データベース接続テスト ===")

    try:
        import psycopg2
        from urllib.parse import urlparse

        database_url = os.getenv('DATABASE_URL')
        result = urlparse(database_url)

        # psycopg2での直接接続テスト
        conn = psycopg2.connect(
            host=result.hostname,
            port=result.port,
            database=result.path[1:],  # 先頭の'/'を除去
            user=result.username,
            password=result.password
        )

        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✓ PostgreSQL接続成功: {version[0][:80]}...")

        cursor.close()
        conn.close()
        return True

    except Exception as e:
        print(f"❌ データベース接続エラー: {e}")
        return False


def test_sqlalchemy_connection():
    """SQLAlchemyでの接続テスト"""
    print("\n=== SQLAlchemy接続テスト ===")

    try:
        from sqlalchemy import create_engine, text

        database_url = os.getenv('DATABASE_URL')

        # PostgreSQL用のドライバを明示的に指定
        if database_url.startswith('postgres://'):
            # 古い形式を新しい形式に変換
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
            print("  DATABASE_URLを postgresql:// 形式に変換しました")

        engine = create_engine(database_url)

        # 接続テスト
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print(f"✓ SQLAlchemy接続成功: {version[:80]}...")

        return engine

    except Exception as e:
        print(f"❌ SQLAlchemy接続エラー: {e}")
        traceback.print_exc()
        return None


def print_separator(title: str):
    """セクション区切り線を印刷"""
    print("\n" + "=" * 50)
    print(f" {title} ")
    print("=" * 50)


def simple_database_test():
    """シンプルなデータベーステスト"""
    print_separator("シンプルなデータベーステスト")

    try:
        # 直接SQLAlchemyを使用してtarget_gamesテーブルを確認
        from sqlalchemy import create_engine, text

        database_url = os.getenv('DATABASE_URL')
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)

        engine = create_engine(database_url)

        with engine.connect() as conn:
            # テーブル存在確認
            result = conn.execute(text("""
                                       SELECT COUNT(*)
                                       FROM information_schema.tables
                                       WHERE table_name = 'target_games'
                                       """))
            table_exists = result.fetchone()[0] > 0

            if table_exists:
                print("✓ target_gamesテーブルが存在します")

                # レコード数確認
                result = conn.execute(text("SELECT COUNT(*) FROM target_games"))
                count = result.fetchone()[0]
                print(f"  現在のレコード数: {count}件")

                # 最初の5件を取得
                if count > 0:
                    result = conn.execute(text("""
                                               SELECT bgg_id, memo, created_at
                                               FROM target_games
                                               ORDER BY created_at ASC LIMIT 5
                                               """))

                    print("  最初の5件:")
                    for row in result:
                        print(f"    BGG ID: {row[0]}, メモ: {row[1] or '(なし)'}, 作成日時: {row[2]}")

            else:
                print("❌ target_gamesテーブルが存在しません")
                print("データベースのマイグレーションが必要かもしれません")
                return False

        return True

    except Exception as e:
        print(f"❌ データベーステストエラー: {e}")
        traceback.print_exc()
        return False


def test_with_fixed_import():
    """修正されたインポートでのテスト"""
    print_separator("TargetGamesMapperテスト")

    try:
        # データベースURLの修正（モジュールインポート前に実行）
        database_url = os.getenv('DATABASE_URL')
        if database_url and database_url.startswith('postgres://'):
            os.environ['DATABASE_URL'] = database_url.replace('postgres://', 'postgresql://', 1)
            print("  DATABASE_URLを修正しました")

        # インポートテスト
        try:
            from infra.db.mapper.target_games_mapper import TargetGamesMapper
            from infra.db.models import TargetGames
            print("✓ モジュールインポート成功")
        except Exception as import_error:
            print(f"❌ インポートエラー: {import_error}")
            traceback.print_exc()
            return False

        # マッパーインスタンス作成テスト
        try:
            mapper = TargetGamesMapper()
            print("✓ TargetGamesMapperインスタンス作成成功")
        except Exception as mapper_error:
            print(f"❌ マッパー作成エラー: {mapper_error}")
            traceback.print_exc()
            return False

        # 基本的な操作テスト
        try:
            # 全件取得テスト
            all_games = mapper.list_all()
            print(f"✓ 全件取得成功: {len(all_games)}件")

            # BGG ID一覧取得テスト
            all_bgg_ids = mapper.list_all_bgg_ids()
            print(f"✓ BGG ID一覧取得成功: {len(all_bgg_ids)}件")

            # 最初のいくつかを表示
            if all_bgg_ids:
                print(f"  最初の10件のBGG ID: {all_bgg_ids[:10]}")

            # 個別取得テスト（最初のBGG IDを使用）
            if all_bgg_ids:
                first_bgg_id = all_bgg_ids[0]
                game = mapper.get_by_bgg_id(first_bgg_id)
                if game:
                    print(f"✓ 個別取得成功: BGG ID {first_bgg_id}")
                    print(f"    メモ: {game.memo or '(なし)'}")
                    print(f"    作成日時: {game.created_at}")
                else:
                    print(f"❌ BGG ID {first_bgg_id} のデータが見つかりません")

            # 存在しないBGG IDでのテスト
            non_existent_game = mapper.get_by_bgg_id(999999)
            if non_existent_game is None:
                print("✓ 存在しないBGG IDに対して正しくNoneが返されました")
            else:
                print("❌ 存在しないBGG IDに対して予期しないデータが返されました")

            return True

        except Exception as operation_error:
            print(f"❌ 操作エラー: {operation_error}")
            traceback.print_exc()
            return False

    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        traceback.print_exc()
        return False


def main():
    """メイン関数"""
    print("TargetGamesMapper 動作確認スクリプト")
    print(f"実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Python version:", sys.version)

    # ステップ1: 環境設定確認
    if not check_environment():
        print("\n❌ 環境設定に問題があります。上記の解決方法を実行してください。")
        return

    # ステップ2: データベース接続確認
    if not test_database_connection():
        print("\n❌ データベース接続に問題があります。DATABASE_URLを確認してください。")
        return

    # ステップ3: SQLAlchemy接続確認
    engine = test_sqlalchemy_connection()
    if not engine:
        print("\n❌ SQLAlchemy接続に問題があります。")
        return

    # ステップ4: シンプルなデータベーステスト
    if not simple_database_test():
        print("\n❌ データベース操作に問題があります。")
        return

    # ステップ5: TargetGamesMapperテスト
    if test_with_fixed_import():
        print_separator("✅ すべてのテストが成功しました！")
        print("TargetGamesMapperは正常に動作しています。")
    else:
        print_separator("❌ 一部のテストが失敗しました")
        print("詳細なエラー情報を確認してください。")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n動作確認が中断されました。")
    except Exception as e:
        print(f"\n❌ スクリプト実行中に致命的なエラーが発生: {e}")
        traceback.print_exc()
        sys.exit(1)