-- =========================================
-- 1. メインのゲームテーブル
-- =========================================
CREATE TABLE IF NOT EXISTS games (
    id SERIAL PRIMARY KEY,
    bgg_id INTEGER UNIQUE NOT NULL,
    primary_name VARCHAR(255) NOT NULL,
    japanese_name VARCHAR(255),
    year_released INTEGER,
    image_url TEXT,

    -- 評価関連
    avg_rating DECIMAL(3,2),
    ratings_count INTEGER,
    comments_count INTEGER,

    -- プレイ情報
    min_players INTEGER,
    max_players INTEGER,
    -- best_player_count は削除（別テーブルで管理）
    min_playtime INTEGER,
    max_playtime INTEGER,
    min_age INTEGER,
    weight DECIMAL(3,2),

    -- ランキング
    rank_overall INTEGER,

    -- メタデータ
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- インデックス作成
CREATE INDEX IF NOT EXISTS idx_games_bgg_id ON games(bgg_id);
CREATE INDEX IF NOT EXISTS idx_games_rating ON games(avg_rating);
CREATE INDEX IF NOT EXISTS idx_games_rank ON games(rank_overall);
CREATE INDEX IF NOT EXISTS idx_games_players ON games(min_players, max_players);

-- =========================================
-- 2. ジャンル関連テーブル（新規追加）
-- =========================================
CREATE TABLE IF NOT EXISTS genres (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS game_genre_ranks (
    id SERIAL PRIMARY KEY,
    game_id INTEGER NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    genre_id INTEGER NOT NULL REFERENCES genres(id) ON DELETE CASCADE,
    rank_in_genre INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(game_id, genre_id)  -- 同じゲーム・同じジャンルの重複防止
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
    player_count INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(game_id, player_count)  -- 同じゲーム・同じ人数の重複防止
);

CREATE INDEX IF NOT EXISTS idx_best_players_game_id ON game_best_player_counts(game_id);
CREATE INDEX IF NOT EXISTS idx_best_players_count ON game_best_player_counts(player_count);

-- =========================================
-- 4. 受賞・ノミネート履歴テーブル
-- =========================================
CREATE TABLE IF NOT EXISTS awards (
    id SERIAL PRIMARY KEY,
    award_name VARCHAR(255) NOT NULL,
    award_year INTEGER NOT NULL,
    award_type VARCHAR(20) NOT NULL,
    award_category VARCHAR(255),
    bgg_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(award_name, award_year, award_type, award_category)  -- 重複防止
);

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
    name VARCHAR(255) UNIQUE NOT NULL,
    bgg_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

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
    name VARCHAR(255) UNIQUE NOT NULL,
    bgg_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

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
    name VARCHAR(255) UNIQUE NOT NULL,
    bgg_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

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
    name VARCHAR(255) UNIQUE NOT NULL,
    bgg_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

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
    name VARCHAR(255) UNIQUE NOT NULL,
    bgg_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS game_categories (
    game_id INTEGER NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    PRIMARY KEY (game_id, category_id)
);

CREATE INDEX IF NOT EXISTS idx_game_categories_game ON game_categories(game_id);
CREATE INDEX IF NOT EXISTS idx_game_categories_category ON game_categories(category_id);