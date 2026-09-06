from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .post import Post


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column()
    posts: Mapped[list["Post"]] = relationship(back_populates="author")


class AdminUser(User):
    role: Mapped[str] = mapped_column(default="admin")
