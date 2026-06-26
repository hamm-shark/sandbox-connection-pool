from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Enum as SQLEnum, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infra.postgres.models.base import Base
from src.main.enums import BookStatus

if TYPE_CHECKING:
    from src.infra.postgres.models.author import Author


class Book(Base):
    __tablename__ = "books"

    title: Mapped[str]
    genre: Mapped[str]

    status: Mapped[BookStatus] = mapped_column(
        SQLEnum(
            BookStatus,
            name="book_status",
            values_callable=lambda enum: [e.value for e in enum],
        ),
        nullable=False,
    )

    authors: Mapped[list["Author"]] = relationship(
        secondary="m2m_books_authors",
        back_populates="books",
        lazy="selectin",
    )

    __table_args__ = (Index("ix_books_status_id", "status", "id"),)


class M2MBooksAuthors(Base):
    __tablename__ = "m2m_books_authors"

    book_id: Mapped[UUID] = mapped_column(ForeignKey("books.id"))
    author_id: Mapped[UUID] = mapped_column(ForeignKey("authors.id"))
