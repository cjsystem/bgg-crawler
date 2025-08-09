from typing import List, Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKeyConstraint, Index, Integer, Numeric, PrimaryKeyConstraint, String, Table, Text, UniqueConstraint, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
import datetime
import decimal

class Base(DeclarativeBase):
    pass


class Artists(Base):
    __tablename__ = 'artists'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='artists_pkey'),
        UniqueConstraint('name', name='artists_name_key')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    game: Mapped[List['Games']] = relationship('Games', secondary='game_artists', back_populates='artist')


class Categories(Base):
    __tablename__ = 'categories'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='categories_pkey'),
        UniqueConstraint('name', name='categories_name_key')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    game_count: Mapped[Optional[int]] = mapped_column(Integer, server_default=text('0'))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    game: Mapped[List['Games']] = relationship('Games', secondary='game_categories', back_populates='category')


class Designers(Base):
    __tablename__ = 'designers'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='designers_pkey'),
        UniqueConstraint('name', name='designers_name_key')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    game_designers: Mapped[List['GameDesigners']] = relationship('GameDesigners', back_populates='designer')


class Games(Base):
    __tablename__ = 'games'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='games_pkey'),
        UniqueConstraint('bgg_id', name='games_bgg_id_key'),
        Index('idx_games_bgg_id', 'bgg_id'),
        Index('idx_games_players', 'min_players', 'max_players'),
        Index('idx_games_rank', 'rank_overall'),
        Index('idx_games_rating', 'avg_rating')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    bgg_id: Mapped[int] = mapped_column(Integer)
    primary_name: Mapped[str] = mapped_column(String(255))
    japanese_name: Mapped[Optional[str]] = mapped_column(String(255))
    year_released: Mapped[Optional[int]] = mapped_column(Integer)
    image_url: Mapped[Optional[str]] = mapped_column(Text)
    avg_rating: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(3, 2))
    ratings_count: Mapped[Optional[int]] = mapped_column(Integer)
    comments_count: Mapped[Optional[int]] = mapped_column(Integer)
    min_players: Mapped[Optional[int]] = mapped_column(Integer)
    max_players: Mapped[Optional[int]] = mapped_column(Integer)
    min_playtime: Mapped[Optional[int]] = mapped_column(Integer)
    max_playtime: Mapped[Optional[int]] = mapped_column(Integer)
    min_age: Mapped[Optional[int]] = mapped_column(Integer)
    weight: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(3, 2))
    rank_overall: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    artist: Mapped[List['Artists']] = relationship('Artists', secondary='game_artists', back_populates='game')
    category: Mapped[List['Categories']] = relationship('Categories', secondary='game_categories', back_populates='game')
    mechanic: Mapped[List['Mechanics']] = relationship('Mechanics', secondary='game_mechanics', back_populates='game')
    publisher: Mapped[List['Publishers']] = relationship('Publishers', secondary='game_publishers', back_populates='game')
    game_awards: Mapped[List['GameAwards']] = relationship('GameAwards', back_populates='game')
    game_best_player_counts: Mapped[List['GameBestPlayerCounts']] = relationship('GameBestPlayerCounts', back_populates='game')
    game_designers: Mapped[List['GameDesigners']] = relationship('GameDesigners', back_populates='game')
    game_genre_ranks: Mapped[List['GameGenreRanks']] = relationship('GameGenreRanks', back_populates='game')


class Genres(Base):
    __tablename__ = 'genres'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='genres_pkey'),
        UniqueConstraint('name', name='genres_name_key')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    game_genre_ranks: Mapped[List['GameGenreRanks']] = relationship('GameGenreRanks', back_populates='genre')


class Mechanics(Base):
    __tablename__ = 'mechanics'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='mechanics_pkey'),
        UniqueConstraint('name', name='mechanics_name_key')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    game_count: Mapped[Optional[int]] = mapped_column(Integer, server_default=text('0'))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    game: Mapped[List['Games']] = relationship('Games', secondary='game_mechanics', back_populates='mechanic')


class Publishers(Base):
    __tablename__ = 'publishers'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='publishers_pkey'),
        UniqueConstraint('name', name='publishers_name_key')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    game: Mapped[List['Games']] = relationship('Games', secondary='game_publishers', back_populates='publisher')


t_game_artists = Table(
    'game_artists', Base.metadata,
    Column('game_id', Integer, primary_key=True, nullable=False),
    Column('artist_id', Integer, primary_key=True, nullable=False),
    ForeignKeyConstraint(['artist_id'], ['artists.id'], ondelete='CASCADE', name='game_artists_artist_id_fkey'),
    ForeignKeyConstraint(['game_id'], ['games.id'], ondelete='CASCADE', name='game_artists_game_id_fkey'),
    PrimaryKeyConstraint('game_id', 'artist_id', name='game_artists_pkey'),
    Index('idx_game_artists_artist', 'artist_id'),
    Index('idx_game_artists_game', 'game_id')
)


class GameAwards(Base):
    __tablename__ = 'game_awards'
    __table_args__ = (
        ForeignKeyConstraint(['game_id'], ['games.id'], ondelete='CASCADE', name='game_awards_game_id_fkey'),
        PrimaryKeyConstraint('id', name='game_awards_pkey'),
        Index('idx_awards_game_id', 'game_id'),
        Index('idx_awards_name', 'award_name'),
        Index('idx_awards_type', 'award_type'),
        Index('idx_awards_year', 'award_year')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    game_id: Mapped[int] = mapped_column(Integer)
    award_name: Mapped[str] = mapped_column(String(255))
    award_year: Mapped[int] = mapped_column(Integer)
    award_type: Mapped[str] = mapped_column(String(20))
    award_category: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    game: Mapped['Games'] = relationship('Games', back_populates='game_awards')


class GameBestPlayerCounts(Base):
    __tablename__ = 'game_best_player_counts'
    __table_args__ = (
        ForeignKeyConstraint(['game_id'], ['games.id'], ondelete='CASCADE', name='game_best_player_counts_game_id_fkey'),
        PrimaryKeyConstraint('id', name='game_best_player_counts_pkey'),
        UniqueConstraint('game_id', 'player_count', name='game_best_player_counts_game_id_player_count_key'),
        Index('idx_best_players_count', 'player_count'),
        Index('idx_best_players_game_id', 'game_id')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    game_id: Mapped[int] = mapped_column(Integer)
    player_count: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    game: Mapped['Games'] = relationship('Games', back_populates='game_best_player_counts')


t_game_categories = Table(
    'game_categories', Base.metadata,
    Column('game_id', Integer, primary_key=True, nullable=False),
    Column('category_id', Integer, primary_key=True, nullable=False),
    ForeignKeyConstraint(['category_id'], ['categories.id'], ondelete='CASCADE', name='game_categories_category_id_fkey'),
    ForeignKeyConstraint(['game_id'], ['games.id'], ondelete='CASCADE', name='game_categories_game_id_fkey'),
    PrimaryKeyConstraint('game_id', 'category_id', name='game_categories_pkey'),
    Index('idx_game_categories_category', 'category_id'),
    Index('idx_game_categories_game', 'game_id')
)


class GameDesigners(Base):
    __tablename__ = 'game_designers'
    __table_args__ = (
        ForeignKeyConstraint(['designer_id'], ['designers.id'], ondelete='CASCADE', name='game_designers_designer_id_fkey'),
        ForeignKeyConstraint(['game_id'], ['games.id'], ondelete='CASCADE', name='game_designers_game_id_fkey'),
        PrimaryKeyConstraint('game_id', 'designer_id', name='game_designers_pkey'),
        Index('idx_game_designers_designer', 'designer_id'),
        Index('idx_game_designers_game', 'game_id')
    )

    game_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    designer_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    is_solo: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('false'))

    designer: Mapped['Designers'] = relationship('Designers', back_populates='game_designers')
    game: Mapped['Games'] = relationship('Games', back_populates='game_designers')


class GameGenreRanks(Base):
    __tablename__ = 'game_genre_ranks'
    __table_args__ = (
        ForeignKeyConstraint(['game_id'], ['games.id'], ondelete='CASCADE', name='game_genre_ranks_game_id_fkey'),
        ForeignKeyConstraint(['genre_id'], ['genres.id'], ondelete='CASCADE', name='game_genre_ranks_genre_id_fkey'),
        PrimaryKeyConstraint('id', name='game_genre_ranks_pkey'),
        UniqueConstraint('game_id', 'genre_id', name='game_genre_ranks_game_id_genre_id_key'),
        Index('idx_game_genre_ranks_game', 'game_id'),
        Index('idx_game_genre_ranks_genre', 'genre_id'),
        Index('idx_game_genre_ranks_rank', 'rank_in_genre')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    game_id: Mapped[int] = mapped_column(Integer)
    genre_id: Mapped[int] = mapped_column(Integer)
    rank_in_genre: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    game: Mapped['Games'] = relationship('Games', back_populates='game_genre_ranks')
    genre: Mapped['Genres'] = relationship('Genres', back_populates='game_genre_ranks')


t_game_mechanics = Table(
    'game_mechanics', Base.metadata,
    Column('game_id', Integer, primary_key=True, nullable=False),
    Column('mechanic_id', Integer, primary_key=True, nullable=False),
    ForeignKeyConstraint(['game_id'], ['games.id'], ondelete='CASCADE', name='game_mechanics_game_id_fkey'),
    ForeignKeyConstraint(['mechanic_id'], ['mechanics.id'], ondelete='CASCADE', name='game_mechanics_mechanic_id_fkey'),
    PrimaryKeyConstraint('game_id', 'mechanic_id', name='game_mechanics_pkey'),
    Index('idx_game_mechanics_game', 'game_id'),
    Index('idx_game_mechanics_mechanic', 'mechanic_id')
)


t_game_publishers = Table(
    'game_publishers', Base.metadata,
    Column('game_id', Integer, primary_key=True, nullable=False),
    Column('publisher_id', Integer, primary_key=True, nullable=False),
    ForeignKeyConstraint(['game_id'], ['games.id'], ondelete='CASCADE', name='game_publishers_game_id_fkey'),
    ForeignKeyConstraint(['publisher_id'], ['publishers.id'], ondelete='CASCADE', name='game_publishers_publisher_id_fkey'),
    PrimaryKeyConstraint('game_id', 'publisher_id', name='game_publishers_pkey'),
    Index('idx_game_publishers_game', 'game_id'),
    Index('idx_game_publishers_publisher', 'publisher_id')
)
