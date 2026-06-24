from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, relationship

from src.infra.postgres.models.base import Base

if TYPE_CHECKING:
    from src.infra.postgres.models.book import Book


class Author(Base):
    __tablename__ = "authors"

    name: Mapped[str]
    books: Mapped[list["Book"]] = relationship(
        secondary="m2m_books_authors",
        back_populates="authors",
    )
