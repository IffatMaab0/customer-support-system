
import os
from datetime import datetime, timedelta, timezone

import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from database import get_db
from models import Agent

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
    agent_id: str,
    role: str
) -> str:

    expiration = (
        datetime.now(timezone.utc)
        + timedelta(minutes=30)
    )

    payload = {
        "sub": agent_id,
        "role": role,
        "exp": expiration
    }

    return jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM
    )


def get_current_agent(
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

        agent_id = payload.get("sub")

        if not agent_id:
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication token"
            )

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token"
        )

    agent = (
        db.query(Agent)
        .filter(Agent.id == agent_id)
        .first()
    )

    if not agent:
        raise HTTPException(
            status_code=401,
            detail="Agent not found"
        )

    return agent


def get_current_admin(
    current_agent: Agent = Depends(get_current_agent)
):
    if current_agent.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )

    return current_agent
