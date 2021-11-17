from typing import List
from fastapi import Depends, FastAPI, HTTPException, status
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sql_app import crud, models, schemas
from .database import get_db, engine
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import re

models.Base.metadata.create_all(bind=engine)
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

app = FastAPI(title="Sadajiwa Auth", openapi_url="/api/v1/openapi.json",
              description=description, openapi_tags=tags_metadata, docs_url="/api/docs", redoc_url="/api/redoc")
origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/token", response_model=schemas.Token, tags=["authentication"])
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


@app.get("/api/users/me/", response_model=schemas.User, tags=["user"])
async def read_users_me(current_user: schemas.User = Depends(crud.get_current_user)):
    return current_user


@app.post("/api/users/", response_model=schemas.User, tags=["user"])
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    request = dict(user)
    for key, value in request.items():
        if value == "":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="All fields are required")
    regex_email = "^(\w|\.|\_|\-)+[@](\w|\_|\-|\.)+[.]\w{2,3}$"
    if not re.search(regex_email, user.email):
        raise HTTPException(status_code=404, detail="Email not valid")
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)


@app.get("/api/users/", response_model=List[schemas.User], tags=["user"])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: schemas.User = Depends(crud.get_current_active_user)):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users


@app.delete("/api/users/", tags=["user"])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: schemas.User = Depends(crud.get_current_active_user)):
    users = crud.delete_user(db, current_user.email)
    return {"message": "user deleted successfully"}


@app.patch("/api/users/", tags=["user"])
def update_user(data: schemas.UserUpdate, skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: schemas.User = Depends(crud.get_current_active_user)):
    users = crud.update_user(db, current_user.email, data)
    return users


@app.get("/api/users/{email}", response_model=schemas.User, tags=["user"])
def read_user(email: str, db: Session = Depends(get_db), current_user: schemas.User = Depends(crud.get_current_active_user)):
    db_user = crud.get_user(db, email)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.get("/api")
def root(db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email="asdf")
    if db_user is None:
        db_user = crud.init_user(db)
    return RedirectResponse("/api/docs")
