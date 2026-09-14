from datetime import datetime, timedelta, timezone
import jwt
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from config import (
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
    JWT_ALGORITHM,
    JWT_SECRET_KEY,
)
from api.auth.models import UserInDB, User
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

password_hash = PasswordHash.recommended()

def hash_password(password: str) -> str:
    return password_hash.hash(password)

def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    return password_hash.verify(plain_password, hashed_password)

def create_access_token(
    subject: str,
    expires_delta: timedelta | None = None,
) -> str:
    if expires_delta is None:
        expires_delta = timedelta(
            minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )
    expire = datetime.now(timezone.utc) + expires_delta

    payload = {
        "sub": subject,
        "exp": expire,
    }

    return jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )

def decode_access_token(token: str) -> str | None:
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
        )

        username = payload.get("sub")
        if not username:
            return None
        
        return username

    except InvalidTokenError:
        return None

# test

mock_users_db = {
    "raguser": UserInDB(
        username="raguser",
        hashed_password=(
            "$argon2id$v=19$m=65536,t=3,p=4$SiBfiU1TR/V4t02OTZ+17w$K2QnDoxQT4sptOdBsR8scJ4UA8hqtZXvK3QOUnZjblI"
        ),
        disabled=False,
    )
}

# Authentication logic
def get_user(username: str) -> UserInDB | None:
    return mock_users_db.get(username)

def authenticate_user(
    username: str,
    password: str,
) -> UserInDB | None:
    user = get_user(username)

    if user is None:
        return None

    if not verify_password(password, user.hashed_password):
        return None

    if user.disabled:
        return None
    
    return user

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login"
)

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)]
) -> User:

    credentials_exception=HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={
            "WWW-Authenticate": "Bearer",
        },
    )

    username=decode_access_token(token)

    if username is None:
        raise credentials_exception
    
    user=get_user(username)

    if user is None:
        raise credentials_exception
    
    if user.disabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    return User(
        username=user.username,
        disabled=user.disabled,
    )
    




