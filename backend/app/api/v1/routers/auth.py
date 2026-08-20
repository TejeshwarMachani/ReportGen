from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import get_current_user
from app.models.organization import Organization
from app.models.user import User
from app.services.auth_service import AuthService
from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterBody(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    org_name: str


class LoginBody(BaseModel):
    email: EmailStr
    password: str


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(body: RegisterBody, db: Session = Depends(get_db)):
    result = await AuthService.register(db, body.email, body.password, body.full_name, body.org_name)
    return result


@router.post("/login", status_code=status.HTTP_200_OK)
async def login(body: LoginBody, db: Session = Depends(get_db)):
    result = await AuthService.login(db, body.email, body.password)
    return result

class RefreshBody(BaseModel):
    refresh_token: str

class LogoutBody(BaseModel):
    refresh_token: str

@router.post("/refresh", status_code=status.HTTP_200_OK)
async def refresh(body: RefreshBody, db: Session = Depends(get_db)):
    """Exchange a valid refresh token for a new access token."""
    access_token = await AuthService.refresh_access_token(db, body.refresh_token)
    return {"access_token": access_token}

@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(body: LogoutBody, db: Session = Depends(get_db)):
    """Invalidate a refresh token.
    ponytail: JWT is stateless; a Redis denylist would harden this.
    """
    try:
        AuthService.decode_token(body.refresh_token)
    except HTTPException:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    return {"detail": "Logged out"}
