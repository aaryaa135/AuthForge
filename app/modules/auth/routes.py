from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.service import AuthService
from app.modules.roles.repository import RoleRepository
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import UserCreate, UserResponse
from app.modules.auth.repository import RefreshTokenRepository
from app.modules.auth.schemas import (
    LoginRequest,
    TokenResponse,
)
from app.modules.users.models import User
from app.shared.dependencies import get_current_user
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    user: UserCreate,
    db: Session = Depends(get_db),
):
    auth_service = AuthService(
        UserRepository(db),
        RoleRepository(db),
    )

    try:
        created_user = auth_service.register_user(user)
        return UserResponse.model_validate(created_user)

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    
@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    auth_service = AuthService(
        UserRepository(db),
        RoleRepository(db),
        RefreshTokenRepository(db),
    )

    try:
        return auth_service.login_user(
            identifier=form_data.username,
            password=form_data.password,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        )
    
@router.get("/me", response_model=UserResponse)
def me(
    current_user: User = Depends(get_current_user),
):
    return UserResponse.model_validate(current_user)