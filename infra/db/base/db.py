# python
# infra/db/base/db.py
import os
from contextlib import contextmanager
from typing import Iterator, Optional

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

load_dotenv()

def _normalize_db_url(url: Optional[str]) -> str:
    if not url:
        raise RuntimeError("DATABASE_URL is not set")
    # postgres:// → postgresql:// に変換（古い形式の互換）
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url

DATABASE_URL = _normalize_db_url(os.getenv("DATABASE_URL"))

# 必要に応じてパラメータ調整
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,          # 死んだ接続の自動検知
    future=True,                 # 2.0スタイル
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,      # commit後にも属性参照しやすく
    future=True,
)

def get_session() -> Session:
    """都度使い切りのSessionを返す（明示close推奨）"""
    return SessionLocal()

@contextmanager
def session_scope() -> Iterator[Session]:
    """簡易的なトランザクション境界（小規模ユース用）
    複数マッパーをまたぐ場合は、サービス層で begin() を直接使うのがおすすめ
    """
    session = get_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()