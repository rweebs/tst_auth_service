from sqlalchemy.orm import Session
from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.sql.expression import delete

from sql_app import database
from . import models, schemas
from datetime import datetime, timedelta
from typing import Optional
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext

SECRET_KEY = "7049df34ffff4ea67ada6caa17b5d37941ec527c25588062afbb605d74cd2f8e"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def authenticate_user(db: Session, email: str, password: str):
    user = get_user(db, email)
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_user(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def delete_user(db: Session, email: str):
    db.query(models.User).filter(models.User.email == email).delete()
    return db.commit()


def update_user(db: Session, email: str, data: schemas.UserUpdate):
    dict_data = dict(data)
    current_user = get_user(db, email=email)
    for key in list(dict_data):
        if dict_data[key] is None:
            del dict_data[key]
    db.query(models.User).filter(models.User.email == email).update(
        dict_data, synchronize_session="fetch")
    db.commit()
    db.refresh(current_user)
    return current_user


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()


def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(email=user.email, password=hashed_password, username=user.username,
                          tanggal_lahir=user.tanggal_lahir, alamat=user.alamat, no_telp=user.no_telp, status=user.status)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def init_user(db: Session):
    hashed_password = get_password_hash("asdf")
    db_user = models.User(email="asdf", password=hashed_password, username="asdf",
                          tanggal_lahir=datetime.now(), alamat="asdf", no_telp="asdf")
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("username")
        email: str = payload.get("email")
        if username is None:
            raise credentials_exception
        token_data = schemas.TokenData(username=username, email=email)
    except JWTError:
        raise credentials_exception
    user = get_user(db, email=token_data.email)
    # user = schemas.User(id=user_model.id, username=user_model.username, email=user_model.email,
    #                     tanggal_lahir=user_model.tanggal_lahir, alamat=user_model.alamat, no_telp=user_model.no_telp, status=user_model.status)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: schemas.User = Depends(get_current_user)):
    return current_user
