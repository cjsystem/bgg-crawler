-- =========================================
-- BGGボードゲーム情報管理システム
-- Board Game Geek データベーススキーマ
-- =========================================

-- =========================================
-- 1. メインのゲームテーブル
-- =========================================
CREATE TABLE IF NOT EXISTS games (
    id SERIAL PRIMARY KEY,
    bgg_id INTEGER UNIQUE NOT NULL,                     -- BGGでのゲーム一意ID
    primary_name VARCHAR(255) NOT NULL,                 -- ゲームの主要名（英語）
    japanese_name VARCHAR(255),                         -- ゲームの日本語名
    year_released INTEGER,                              -- リリース年
    image_url TEXT,                                     -- ゲーム画像URL

    -- 評価関連
    avg_rating DECIMAL(4,2),                            -- 平均評価（0.00-10.00）
    ratings_count INTEGER,                              -- 評価数
    comments_count INTEGER,                             -- コメント数

    -- プレイ情報
    min_players INTEGER,                                -- 最小プレイヤー数
    max_players INTEGER,                                -- 最大プレイヤー数
    min_playtime INTEGER,                               -- 最小プレイ時間（分）
    max_playtime INTEGER,                               -- 最大プレイ時間（分）
    min_age INTEGER,                                    -- 推奨最小年齢
    weight DECIMAL(4,2),                                -- ゲーム複雑さ（0.00-5.00）

    -- ランキング
    rank_overall INTEGER,                               -- BGG総合ランキング

    -- メタデータ
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ゲームテーブルのインデックス
CREATE INDEX IF NOT EXISTS idx_games_bgg_id ON games(bgg_id);
CREATE INDEX IF NOT EXISTS idx_games_rating ON games(avg_rating);
CREATE INDEX IF NOT EXISTS idx_games_rank ON games(rank_overall);
CREATE INDEX IF NOT EXISTS idx_games_players ON games(min_players, max_players);
CREATE INDEX IF NOT EXISTS idx_games_name ON games(primary_name);

-- =========================================
-- 2. ジャンル関連テーブル
-- =========================================
CREATE TABLE IF NOT EXISTS genres (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,                  -- ジャンル名（Overall, Strategy等）
    bgg_url TEXT,                                       -- BGGジャンルページURL
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ゲーム×ジャンル別ランキング
CREATE TABLE IF NOT EXISTS game_genre_ranks (
    id SERIAL PRIMARY KEY,
    game_id INTEGER NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    genre_id INTEGER NOT NULL REFERENCES genres(id) ON DELETE CASCADE,
    rank_in_genre INTEGER,                              -- そのジャンル内でのランク
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(game_id, genre_id)                           -- 同じゲーム・同じジャンルの重複防止
);

CREATE INDEX IF NOT EXISTS idx_game_genre_ranks_game ON game_genre_ranks(game_id);
CREATE INDEX IF NOT EXISTS idx_game_genre_ranks_genre ON game_genre_ranks(genre_id);
CREATE INDEX IF NOT EXISTS idx_game_genre_ranks_rank ON game_genre_ranks(rank_in_genre);

-- =========================================
-- 3. ベストプレイヤー人数テーブル
-- =========================================
CREATE TABLE IF NOT EXISTS game_best_player_counts (
    id SERIAL PRIMARY KEY,
    game_id INTEGER NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    player_count INTEGER NOT NULL,                      -- ベストとされるプレイヤー数
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(game_id, player_count)                       -- 同じゲーム・同じ人数の重複防止
);

CREATE INDEX IF NOT EXISTS idx_best_players_game_id ON game_best_player_counts(game_id);
CREATE INDEX IF NOT EXISTS idx_best_players_count ON game_best_player_counts(player_count);

-- =========================================
-- 4. 受賞・ノミネート履歴テーブル
-- =========================================
CREATE TABLE IF NOT EXISTS awards (
    id SERIAL PRIMARY KEY,
    award_name VARCHAR(255) NOT NULL,                   -- 賞の名前
    award_year INTEGER NOT NULL,                        -- 受賞年
    award_type VARCHAR(20) NOT NULL,                    -- Winner, Nominee, Finalist等
    award_category VARCHAR(255),                        -- 賞のカテゴリ（修正：追加）
    bgg_url TEXT,                                       -- BGG受賞ページURL
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(award_name, award_year, award_type, award_category)  -- 重複防止
);

-- ゲーム×受賞の中間テーブル
CREATE TABLE IF NOT EXISTS game_awards (
    game_id INTEGER NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    award_id INTEGER NOT NULL REFERENCES awards(id) ON DELETE CASCADE,
    PRIMARY KEY (game_id, award_id)
);

CREATE INDEX IF NOT EXISTS idx_awards_name ON awards(award_name);
CREATE INDEX IF NOT EXISTS idx_awards_year ON awards(award_year);
CREATE INDEX IF NOT EXISTS idx_awards_type ON awards(award_type);
CREATE INDEX IF NOT EXISTS idx_game_awards_game ON game_awards(game_id);
CREATE INDEX IF NOT EXISTS idx_game_awards_award ON game_awards(award_id);

-- =========================================
-- 5. デザイナー関連
-- =========================================
CREATE TABLE IF NOT EXISTS designers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,                  -- デザイナー名
    bgg_url TEXT,                                       -- BGGデザイナーページURL
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ゲーム×デザイナーの中間テーブル
CREATE TABLE IF NOT EXISTS game_designers (
    game_id INTEGER NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    designer_id INTEGER NOT NULL REFERENCES designers(id) ON DELETE CASCADE,
    PRIMARY KEY (game_id, designer_id)
);

CREATE INDEX IF NOT EXISTS idx_game_designers_game ON game_designers(game_id);
CREATE INDEX IF NOT EXISTS idx_game_designers_designer ON game_designers(designer_id);

-- =========================================
-- 6. アーティスト関連
-- =========================================
CREATE TABLE IF NOT EXISTS artists (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,                  -- アーティスト名
    bgg_url TEXT,                                       -- BGGアーティストページURL
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ゲーム×アーティストの中間テーブル
CREATE TABLE IF NOT EXISTS game_artists (
    game_id INTEGER NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    artist_id INTEGER NOT NULL REFERENCES artists(id) ON DELETE CASCADE,
    PRIMARY KEY (game_id, artist_id)
);

CREATE INDEX IF NOT EXISTS idx_game_artists_game ON game_artists(game_id);
CREATE INDEX IF NOT EXISTS idx_game_artists_artist ON game_artists(artist_id);

-- =========================================
-- 7. パブリッシャー関連
-- =========================================
CREATE TABLE IF NOT EXISTS publishers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,                  -- 出版社名
    bgg_url TEXT,                                       -- BGG出版社ページURL
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ゲーム×パブリッシャーの中間テーブル
CREATE TABLE IF NOT EXISTS game_publishers (
    game_id INTEGER NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    publisher_id INTEGER NOT NULL REFERENCES publishers(id) ON DELETE CASCADE,
    PRIMARY KEY (game_id, publisher_id)
);

CREATE INDEX IF NOT EXISTS idx_game_publishers_game ON game_publishers(game_id);
CREATE INDEX IF NOT EXISTS idx_game_publishers_publisher ON game_publishers(publisher_id);

-- =========================================
-- 8. メカニクス関連
-- =========================================
CREATE TABLE IF NOT EXISTS mechanics (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,                  -- メカニクス名
    bgg_url TEXT,                                       -- BGGメカニクスページURL
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ゲーム×メカニクスの中間テーブル
CREATE TABLE IF NOT EXISTS game_mechanics (
    game_id INTEGER NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    mechanic_id INTEGER NOT NULL REFERENCES mechanics(id) ON DELETE CASCADE,
    PRIMARY KEY (game_id, mechanic_id)
);

CREATE INDEX IF NOT EXISTS idx_game_mechanics_game ON game_mechanics(game_id);
CREATE INDEX IF NOT EXISTS idx_game_mechanics_mechanic ON game_mechanics(mechanic_id);

-- =========================================
-- 9. カテゴリ関連
-- =========================================
CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,                  -- カテゴリ名
    bgg_url TEXT,                                       -- BGGカテゴリページURL
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ゲーム×カテゴリの中間テーブル
CREATE TABLE IF NOT EXISTS game_categories (
    game_id INTEGER NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    PRIMARY KEY (game_id, category_id)
);

CREATE INDEX IF NOT EXISTS idx_game_categories_game ON game_categories(game_id);
CREATE INDEX IF NOT EXISTS idx_game_categories_category ON game_categories(category_id);

-- =========================================
-- 10. クローリング管理テーブル
-- =========================================

-- 特定パース対象ゲーム管理テーブル
CREATE TABLE IF NOT EXISTS target_games (
    bgg_id INTEGER PRIMARY KEY,        -- 主キーにする
    memo VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 既にUNIQUEやインデックスを作っている場合は不要です
-- UNIQUE(bgg_id) は不要（PRIMARY KEYが一意制約とインデックスを内包）
-- CREATE INDEX idx_target_games_bgg_id ON target_games(bgg_id); も不要

-- バッチ処理の進捗管理テーブル
CREATE TABLE IF NOT EXISTS crawl_progress (
    id SERIAL PRIMARY KEY,
    batch_id VARCHAR(50) UNIQUE NOT NULL,               -- バッチ実行ID
    batch_type VARCHAR(20) DEFAULT 'manual',            -- ranking, target, manual等
    total_games INTEGER NOT NULL DEFAULT 0,             -- 処理対象ゲーム総数
    processed_games INTEGER DEFAULT 0,                  -- 処理完了ゲーム数
    failed_games INTEGER DEFAULT 0,                     -- 処理失敗ゲーム数
    success_rate DECIMAL(5,2) GENERATED ALWAYS AS (     -- 成功率（計算列）
        CASE
            WHEN total_games > 0 THEN
                ROUND((processed_games::DECIMAL / total_games * 100), 2)
            ELSE 0
        END
    ) STORED,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,     -- バッチ開始時刻
    completed_at TIMESTAMP NULL,                        -- バッチ完了時刻
    error_message TEXT,                                 -- エラーメッセージ（追加）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- クローリング管理テーブルのインデックス
CREATE INDEX IF NOT EXISTS idx_crawl_progress_batch_id ON crawl_progress(batch_id);
CREATE INDEX IF NOT EXISTS idx_crawl_progress_started_at ON crawl_progress(started_at);

-- =========================================
-- 初期データ投入（サンプル）
-- =========================================

-- 基本ジャンルの追加
INSERT INTO genres (name, bgg_url) VALUES
('Overall', 'https://boardgamegeek.com/browse/boardgame?sort=rank&rankobjecttype=subtype&rankobjectid=1'),
('Strategy', 'https://boardgamegeek.com/strategygames/browse/boardgame?sort=rank'),
('Family', 'https://boardgamegeek.com/familygames/browse/boardgame?sort=rank'),
('Thematic', 'https://boardgamegeek.com/thematicgames/browse/boardgame?sort=rank'),
('War', 'https://boardgamegeek.com/wargames/browse/boardgame?sort=rank'),
('Abstract', 'https://boardgamegeek.com/abstracts/browse/boardgame?sort=rank'),
('Customizable', 'https://boardgamegeek.com/cgs/browse/boardgame?sort=rank'),
('Children', 'https://boardgamegeek.com/childrensgames/browse/boardgame?sort=rank'),
('Party', 'https://boardgamegeek.com/partygames/browse/boardgame?sort=rank')
ON CONFLICT (name) DO NOTHING;