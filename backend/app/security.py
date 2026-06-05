"""Security utilities for password hashing and JWT tokens."""
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import get_settings

settings = get_settings()

# Password hashing context using bcrypt
pwd_context: CryptContext = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,
)


def hash_password(plain_password: str) -> str:
    """
    Hash a plain text password using bcrypt.

    Args:
        plain_password: The password to hash.

    Returns:
        str: The hashed password.
    """
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        plain_password: The plain text password to verify.
        hashed_password: The hashed password to compare against.

    Returns:
        bool: True if password matches, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """
    Create a JWT access token.

    Args:
        data: The payload data to encode in the token.
        expires_delta: Optional expiration time delta.

    Returns:
        str: The encoded JWT token.
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    return encoded_jwt


def create_refresh_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """
    Create a JWT refresh token.

    Args:
        data: The payload data to encode in the token.
        expires_delta: Optional expiration time delta.

    Returns:
        str: The encoded JWT refresh token.
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    return encoded_jwt


def decode_token(token: str) -> dict[str, Any] | None:
    """
    Decode and validate a JWT token.

    Args:
        token: The JWT token to decode.

    Returns:
        dict | None: The decoded payload if valid, None otherwise.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        return payload
    except JWTError:
        return None


def verify_access_token(token: str) -> dict[str, Any] | None:
    """
    Verify an access token and return its payload.

    Args:
        token: The JWT access token to verify.

    Returns:
        dict | None: The payload if valid access token, None otherwise.
    """
    payload = decode_token(token)
    if payload and payload.get("type") == "access":
        return payload
    return None
