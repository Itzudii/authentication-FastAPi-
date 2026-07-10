from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from fastapi import Depends , HTTPException
import secrets
import hashlib

from core.config import (
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
#OauthSetup
oauth2_schema = OAuth2PasswordBearer(tokenUrl="login")

#pASSWORD hASHING SETUP
pwd_context = CryptContext(schemes=["sha256_crypt"],deprecated="auto")


# ------------------------
# Helper
# ------------------------
#Hash Password
def hash_password(password:str):
    return pwd_context.hash(password)

#verify Password
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def generate_otp() -> str:
    return "".join(str(secrets.randbelow(10)) for _ in range(6))

def hash_otp(otp:str)->str:
    return hashlib.sha256(str(otp).encode()).hexdigest()
# ------------------------
# token
# ------------------------
#Create Token
def create_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=int(ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({
        "exp":expire,
        "type":"access"
    })
    token = jwt.encode(to_encode,SECRET_KEY,algorithm=ALGORITHM)

    return token


def verify_access_token(token: str = Depends(oauth2_schema)) -> dict:
    """
    Verify and decode a JWT access token.
    Raises jwt.InvalidTokenError if invalid.
    """
    
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        if payload.get("type") != "access":
            raise jwt.InvalidTokenError("Invalid token type")

        return payload
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )