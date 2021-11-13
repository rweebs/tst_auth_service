from typing import List
from fastapi import Depends, FastAPI, HTTPException, status
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from . import crud, models, schemas
from .database import get_db, engine
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

models.Base.metadata.create_all(bind=engine)
app = FastAPI()
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Dependency
description = """
Nama    : Rahmat Wibowo\n
NIM     : 18219040\n
"""
tags_metadata = [
    {
        "name": "authentication",
        "description": "Authentication endpoint",
    },
    {
        "name": "user",
        "description": "User endpoint",
    }
]

app = FastAPI(title="Sadajiwa Auth",
              description=description, openapi_tags=tags_metadata)


@app.post("/token", response_model=schemas.Token, tags=["authentication"])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = crud.create_access_token(
        data={"username": user.username, "email": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me/", response_model=schemas.User, tags=["user"])
async def read_users_me(current_user: schemas.User = Depends(crud.get_current_user)):
    return current_user


@app.post("/users/", response_model=schemas.User, tags=["user"])
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)


@app.get("/users/", response_model=List[schemas.User], tags=["user"])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: schemas.User = Depends(crud.get_current_active_user)):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users


@app.delete("/users/", tags=["user"])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: schemas.User = Depends(crud.get_current_active_user)):
    users = crud.delete_user(db, current_user.email)
    return {"message": "user deleted successfully"}


@app.patch("/users/", tags=["user"])
def update_user(data: schemas.UserUpdate, skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: schemas.User = Depends(crud.get_current_active_user)):
    users = crud.update_user(db, current_user.email, data)
    return users


@app.get("/users/{email}", response_model=schemas.User, tags=["user"])
def read_user(email: str, db: Session = Depends(get_db), current_user: schemas.User = Depends(crud.get_current_active_user)):
    db_user = crud.get_user(db, email)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user
