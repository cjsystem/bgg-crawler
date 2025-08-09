# db/base/db_mapper_base.py
from typing import Generic, TypeVar, Type, List, Optional
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# base.pyの内容を移動
class Base(DeclarativeBase):
    pass

# データベース接続も一緒に管理
DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_session():
    """セッション取得のヘルパー関数"""
    return SessionLocal()

T = TypeVar('T')


class DBMapperBase(Generic[T]):
    def __init__(self, model: Type[T]):
        self.model = model

    def get_session(self):
        """共通のセッション取得"""
        return get_session()

    def create(self, **kwargs) -> T:
        """データを作成"""
        session = self.get_session()
        try:
            db_obj = self.model(**kwargs)
            session.add(db_obj)
            session.commit()
            session.refresh(db_obj)
            return db_obj
        finally:
            session.close()

    def get_by_id(self, id: int) -> Optional[T]:
        """IDでデータを取得"""
        session = self.get_session()
        try:
            return session.query(self.model).filter(self.model.id == id).first()
        finally:
            session.close()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """全データを取得（ページング付き）"""
        session = self.get_session()
        try:
            return session.query(self.model).offset(skip).limit(limit).all()
        finally:
            session.close()

    def update(self, id: int, **kwargs) -> Optional[T]:
        """データを更新"""
        session = self.get_session()
        try:
            db_obj = session.query(self.model).filter(self.model.id == id).first()
            if db_obj:
                for key, value in kwargs.items():
                    if hasattr(db_obj, key):
                        setattr(db_obj, key, value)
                session.commit()
                session.refresh(db_obj)
                return db_obj
            return None
        finally:
            session.close()

    def delete(self, id: int) -> bool:
        """データを削除"""
        session = self.get_session()
        try:
            db_obj = session.query(self.model).filter(self.model.id == id).first()
            if db_obj:
                session.delete(db_obj)
                session.commit()
                return True
            return False
        finally:
            session.close()

    def filter_by(self, **kwargs) -> List[T]:
        """条件でフィルタリング"""
        session = self.get_session()
        try:
            query = session.query(self.model)
            for key, value in kwargs.items():
                if hasattr(self.model, key):
                    query = query.filter(getattr(self.model, key) == value)
            return query.all()
        finally:
            session.close()

    def count(self) -> int:
        """レコード数を取得"""
        session = self.get_session()
        try:
            return session.query(self.model).count()
        finally:
            session.close()