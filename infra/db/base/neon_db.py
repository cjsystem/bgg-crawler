import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()


class NeonDB:
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable is not set")

    def get_connection(self):
        """データベース接続を取得"""
        try:
            conn = psycopg2.connect(
                self.database_url,
                cursor_factory=RealDictCursor  # 結果を辞書形式で取得
            )
            return conn
        except psycopg2.Error as e:
            print(f"データベース接続エラー: {e}")
            raise

    def execute_query(self, query, params=None):
        """クエリを実行（SELECT用）"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()

    def execute_command(self, command, params=None):
        """コマンドを実行（INSERT/UPDATE/DELETE用）"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(command, params)
                conn.commit()
                return cursor.rowcount


# 使用例
if __name__ == "__main__":
    db = NeonDB()

    # 接続テスト
    try:
        with db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT version();")
                version = cursor.fetchone()
                print(f"PostgreSQL バージョン: {version['version']}")
                print("✅ データベース接続成功！")
    except Exception as e:
        print(f"❌ 接続エラー: {e}")