from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta

from services.auth import (
    PasswordManager,
    TokenManager,
    users_db,
    get_current_active_user,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from entities.dto import User

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

@router.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Provides a token for a user.
    """
    user = users_db.get_user(form_data.username)
    if not user or not PasswordManager.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = TokenManager.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """
    Returns the current logged-in user.
    """
    return current_user