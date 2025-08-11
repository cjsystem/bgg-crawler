-- =========================================
-- データベースリセット用DROP文
-- 注意: 全データが削除されます！
-- =========================================

-- 実行前に確認用
-- SELECT 'データベースをリセットします。続行しますか？' as warning;

-- 外部キー制約があるため、逆順でDROP
DROP TABLE IF EXISTS game_categories CASCADE;
DROP TABLE IF EXISTS game_mechanics CASCADE;
DROP TABLE IF EXISTS game_publishers CASCADE;
DROP TABLE IF EXISTS game_artists CASCADE;
DROP TABLE IF EXISTS game_designers CASCADE;
DROP TABLE IF EXISTS game_awards CASCADE;
DROP TABLE IF EXISTS game_genre_ranks CASCADE;
DROP TABLE IF EXISTS game_best_player_counts CASCADE;

-- マスターテーブル
DROP TABLE IF EXISTS categories CASCADE;
DROP TABLE IF EXISTS mechanics CASCADE;
DROP TABLE IF EXISTS publishers CASCADE;
DROP TABLE IF EXISTS artists CASCADE;
DROP TABLE IF EXISTS designers CASCADE;
DROP TABLE IF EXISTS awards CASCADE;
DROP TABLE IF EXISTS genres CASCADE;

-- メインテーブル
DROP TABLE IF EXISTS games CASCADE;

-- 管理テーブル
DROP TABLE IF EXISTS target_games CASCADE;
DROP TABLE IF EXISTS crawl_progress CASCADE;

-- シーケンスもリセット（念のため）
DROP SEQUENCE IF EXISTS games_id_seq CASCADE;
DROP SEQUENCE IF EXISTS genres_id_seq CASCADE;
DROP SEQUENCE IF EXISTS designers_id_seq CASCADE;
DROP SEQUENCE IF EXISTS artists_id_seq CASCADE;
DROP SEQUENCE IF EXISTS publishers_id_seq CASCADE;
DROP SEQUENCE IF EXISTS mechanics_id_seq CASCADE;
DROP SEQUENCE IF EXISTS categories_id_seq CASCADE;
DROP SEQUENCE IF EXISTS awards_id_seq CASCADE;
DROP SEQUENCE IF EXISTS target_games_id_seq CASCADE;
DROP SEQUENCE IF EXISTS crawl_progress_id_seq CASCADE;

-- =========================================
-- ここから既存のCREATE文が続く
-- =========================================