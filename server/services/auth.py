import bcrypt
from jose import jwt, JWTError
from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta, timezone

from entities.dto import User
from services.user_database import UsersDatabase

# --- Configuration ---
SECRET_KEY = "your-super-secret-key"  # In production, load from environment variables
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

# --- Database ---
users_db = UsersDatabase()

class PasswordManager:
    """Handles password hashing and verification."""
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Hashes a password using bcrypt and returns a string."""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verifies a plain password against a hashed one."""
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

class TokenManager:
    """Handles JWT token creation and decoding."""
    @staticmethod
    def create_access_token(data: dict, expires_delta: timedelta | None = None):
        """Creates a new access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    @staticmethod
    def decode_token(token: str) -> dict | None:
        """Decodes a token and returns its payload."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError:
            return None

# --- Dependency to get current user ---
def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    Dependency to get the current user from a token.
    Raises HTTPException 401 if the token is invalid or the user is not found.
    """
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = TokenManager.decode_token(token)
    if payload is None:
        raise credentials_exception
    
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception
    
    user = users_db.get_user(username)
    if user is None:
        raise credentials_exception
        
    # The DTOs User and UserInDB are compatible for this purpose
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency to get the current *active* user.
    Raises HTTPException 400 if the user is inactive.
    """
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user