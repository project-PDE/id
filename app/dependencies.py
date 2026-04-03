from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select

from app.core.security import decode_token
from app.db import get_session
from app.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )

    try:
        payload = decode_token(token)
    except Exception as exc:
        raise credentials_exception from exc

    if payload.get("type") != "access":
        raise credentials_exception

    user_id = payload.get("uid")
    if user_id is None:
        raise credentials_exception

    user = session.exec(select(User).where(User.id == user_id)).first()
    if not user:
        raise credentials_exception

    return user
