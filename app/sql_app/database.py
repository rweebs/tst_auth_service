from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_USER = "root"
DATABASE_PASSWORD = "root"
DATABASE_URI = "db"
DATABASE_NAME = "tst"
SQLALCHEMY_DATABASE_URL = f"mysql://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_URI}:3306/{DATABASE_NAME}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
