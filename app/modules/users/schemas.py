from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

class UserCreate(BaseModel):
    """
    Request schema for user registration.
    """

    email: EmailStr

    username: str = Field(
        min_length=3,
        max_length=30,
    )

    password: str = Field(
        min_length=8,
        max_length=128,
    )


class UserResponse(BaseModel):
    """
    Response schema returned after registration.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    username: str
    is_active: bool
    is_verified: bool
    role_id: UUID
    created_at: datetime

class UserResponse(BaseModel):
    id: UUID
    email: str
    username: str
    role: str
    is_active: bool
    created_at: datetime

class UpdateUserRoleRequest(BaseModel):
    role: str

class UpdateUserStatusRequest(BaseModel):
    is_active: bool