
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ..config import Config


def create_db_context():
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI,
                           pool_pre_ping=True, pool_size=1, max_overflow=-1, echo=False)
    session_local = sessionmaker(
        autocommit=False, autoflush=False, bind=engine)
    return engine, session_local
