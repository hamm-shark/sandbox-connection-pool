from pydantic import BaseModel


class ClintCallSession(BaseModel):
    session_nums: int | None = None
