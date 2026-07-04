from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db import Base
from db import Base

# ------------------------
# USER
# ------------------------
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    email: Mapped[str] = mapped_column(
        String,
        unique=True,
        index=True
    )

    password: Mapped[str] = mapped_column(String)

    verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False
    )



# ------------------------
# OTP
# ------------------------



class OTP(Base):
    __tablename__ = "otp_codes"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )

    otp_hash: Mapped[str] = mapped_column(
        String(255)
    )

    purpose: Mapped[str] = mapped_column(
        String(30)
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
    nullable=False
    )

    used: Mapped[bool] = mapped_column(
        Boolean,
        default=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    nullable=False
    )

    user = relationship("User")

