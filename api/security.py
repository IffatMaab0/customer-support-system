import os
from datetime import datetime, timedelta, timezone

import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from database import get_db
from models import Agent, Customer

from pwdlib import PasswordHash


load_dotenv()

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = "HS256"

password_hash = PasswordHash.recommended()

oauth2_scheme = HTTPBearer()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)


def create_access_token(
    user_id: str,
    role: str
) -> str:

    expiration = (
        datetime.now(timezone.utc)
        + timedelta(minutes=30)
    )

    payload = {
        "sub": user_id,
        "role": role,
        "exp": expiration
    }

    return jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM
    )


def get_current_identity(
    credentials=Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM]
        )

        user_id = payload.get("sub")
        role = payload.get("role")

        if not user_id or not role:
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication token"
            )

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token"
        )

    if role == "customer":

        user = (
            db.query(Customer)
            .filter(Customer.id == user_id)
            .first()
        )

        if not user or not user.is_active:
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication token"
            )

        return user

    if role in ["agent", "manager", "admin"]:

        user = (
            db.query(Agent)
            .filter(Agent.id == user_id)
            .first()
        )

        if not user:
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication token"
            )

        return user

    raise HTTPException(
        status_code=401,
        detail="Invalid authentication token"
    )


def get_current_staff(
    current_user=Depends(get_current_identity)
):
    if not isinstance(current_user, Agent):
        raise HTTPException(
            status_code=403,
            detail="Staff access required"
        )

    return current_user


def get_current_manager(
    current_user: Agent = Depends(get_current_staff)
):
    if current_user.role not in ["admin", "manager"]:
        raise HTTPException(
            status_code=403,
            detail="Manager access required"
        )

    return current_user