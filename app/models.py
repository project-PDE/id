from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    username: str = Field(index=True, unique=True)
    password_hash: str
    is_active: bool = True
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=False), nullable=False),
    )


class RefreshToken(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    jti: str = Field(default_factory=lambda: str(uuid4()), index=True, unique=True)
    user_id: int = Field(index=True, foreign_key="user.id")
    expires_at: datetime = Field(sa_column=Column(DateTime(timezone=False), nullable=False))
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=False), nullable=False),
    )
    revoked_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=False), nullable=True),
    )
