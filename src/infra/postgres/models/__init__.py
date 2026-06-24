from src.infra.postgres.models.author import Author
from src.infra.postgres.models.book import Book, M2MBooksAuthors

__all__ = [
    "Author",
    "Book",
    "M2MBooksAuthors",
]
