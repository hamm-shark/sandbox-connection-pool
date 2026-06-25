from enum import StrEnum


class BookStatus(StrEnum):
    DRAFT = "draft"
    CREATED = "created"
    PROCESSING = "processing"
    READY = "ready"
    RETRY = "retry"
    FAILED = "failed"
    ARCHIVED = "archived"

    @classmethod
    def successful(cls) -> tuple["BookStatus", ...]:
        return (
            cls.CREATED,
            cls.PROCESSING,
            cls.READY,
        )

    @classmethod
    def failed(cls) -> tuple["BookStatus", ...]:
        return (
            cls.FAILED,
            cls.DRAFT,
            cls.RETRY,
        )
