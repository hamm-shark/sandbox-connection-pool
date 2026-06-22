from enum import StrEnum


class BookStatus(StrEnum):
    DRAFT = "draft"
    CREATED = "created"
    PROCESSING = "processing"
    READY = "ready"
    RETRY = "retry"
    FAILED = "failed"
    ARCHIVED = "archived"
