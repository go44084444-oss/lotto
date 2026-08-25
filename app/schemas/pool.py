from pydantic import BaseModel


class RegeneratePoolIn(BaseModel):
    reset_assignments: bool = False


class RegeneratePoolOut(BaseModel):
    survivor_count: int
    assignments_reset: bool
