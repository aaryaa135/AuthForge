from pydantic import BaseModel


class SuccessResponse(BaseModel):
    message: str
    data: dict | None = None


class ErrorResponse(BaseModel):
    detail: str
