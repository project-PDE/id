from datetime import datetime

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.db import get_session
from app.dependencies import get_current_user
from app.models import RefreshToken, User
from app.schemas import (
    RefreshRequest,
    TokenPairResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegisterRequest, session: Session = Depends(get_session)):
    existing_email = session.exec(select(User).where(User.email == payload.email)).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="Email уже зарегистрирован")

    existing_username = session.exec(select(User).where(User.username == payload.username)).first()
    if existing_username:
        raise HTTPException(status_code=400, detail="Имя пользователя уже занято")

    user = User(
        email=payload.email,
        username=payload.username,
        password_hash=get_password_hash(payload.password),
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@router.post("/login", response_model=TokenPairResponse)
def login(payload: UserLoginRequest, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == payload.email)).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Неверный email или пароль")

    if not isinstance(user.id, int) or isinstance(user.id, bool):
        raise HTTPException(status_code=500, detail="Неверный тип ID пользователя")

    access_token = create_access_token(subject=user.email, user_id=user.id)
    refresh_token, jti, expires_at = create_refresh_token(subject=user.email, user_id=user.id)

    refresh_row = RefreshToken(jti=jti, user_id=user.id, expires_at=expires_at)
    session.add(refresh_row)
    session.commit()

    return TokenPairResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenPairResponse)
def refresh_tokens(payload: RefreshRequest, session: Session = Depends(get_session)):
    try:
        decoded = decode_token(payload.refresh_token)
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail="Неверный refresh токен") from exc

    if decoded.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Неверный тип refresh токена")

    jti = decoded.get("jti")
    user_id = decoded.get("uid")
    if not jti or not user_id:
        raise HTTPException(status_code=401, detail="Неверное содержимое refresh токена")

    stored = session.exec(select(RefreshToken).where(RefreshToken.jti == jti)).first()
    if not stored or stored.revoked_at is not None or stored.expires_at < datetime.utcnow():
        raise HTTPException(status_code=401, detail="Недействительный или просроченный refresh токен")

    user = session.exec(select(User).where(User.id == user_id)).first()
    if not user:
        raise HTTPException(status_code=401, detail="Пользователь не найден")

    stored.revoked_at = datetime.utcnow()

    if not isinstance(user.id, int) or isinstance(user.id, bool):
        raise HTTPException(status_code=500, detail="Неверный тип ID пользователя")
    
    access_token = create_access_token(subject=user.email, user_id=user.id)
    new_refresh_token, new_jti, expires_at = create_refresh_token(subject=user.email, user_id=user.id)
    session.add(RefreshToken(jti=new_jti, user_id=user.id, expires_at=expires_at))

    session.add(stored)
    session.commit()

    return TokenPairResponse(access_token=access_token, refresh_token=new_refresh_token)


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return current_user
