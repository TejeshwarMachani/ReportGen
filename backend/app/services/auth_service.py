import json
import bcrypt
import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.organization import Organization
from app.models.user import User
from app.core.config import settings


class AuthService:
    @staticmethod
    def hash_password(password: str) -> str:
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        try:
            return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
        except Exception:
            return False

    @staticmethod
    def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
        return encoded_jwt

    @staticmethod
    def decode_token(token: str) -> dict:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )

    @staticmethod
    async def register(db: Session, email: str, password: str, full_name: str, org_name: str):
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        # Reuse an existing org with the same slug, otherwise create a new one
        slug = org_name.lower().replace(" ", "-")
        org = db.query(Organization).filter(Organization.slug == slug).first()
        if not org:
            org = Organization(name=org_name, slug=slug, plan="free")
            db.add(org)
            db.commit()
            db.refresh(org)

        # Create user in the org
        hashed_pw = AuthService.hash_password(password)
        user = User(
            email=email,
            password_hash=hashed_pw,
            full_name=full_name,
            role="owner",
            org_id=org.id,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Create access token
        access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = AuthService.create_access_token(
            data={"sub": user.email, "user_id": user.id, "org_id": user.org_id},
            expires_delta=access_token_expires,
        )

        return {
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
                "org_id": user.org_id,
            },
            "access_token": access_token,
            "refresh_token": AuthService.create_refresh_token(user.id),
        }

    @staticmethod
    async def refresh_access_token(db: Session, refresh_token: str) -> str:
        """Issue a new access token from a valid refresh token."""
        payload = AuthService.decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )
        user = db.query(User).filter(User.id == payload.get("sub")).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )
        return AuthService.create_access_token(
            data={"sub": user.email, "user_id": user.id, "org_id": user.org_id},
        )

    @staticmethod
    def create_refresh_token(user_id: str) -> str:
        return AuthService.create_access_token(
            data={"sub": user_id, "type": "refresh"},
            expires_delta=timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS),
        )

    @staticmethod
    async def login(db: Session, email: str, password: str):
        user = db.query(User).filter(User.email == email).first()
        if not user or not AuthService.verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = AuthService.create_access_token(
            data={"sub": user.email, "user_id": user.id, "org_id": user.org_id},
            expires_delta=access_token_expires,
        )

        return {
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
                "org_id": user.org_id,
            },
            "access_token": access_token,
            "refresh_token": AuthService.create_refresh_token(user.id),
        }