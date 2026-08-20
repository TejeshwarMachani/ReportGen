from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.organization import Organization
from app.models.user import User
from app.services.auth_service import AuthService
from app.auth import get_current_user
from pydantic import BaseModel, Field


router = APIRouter(prefix="/orgs", tags=["organizations"])


class InviteBody(BaseModel):
    email: str
    role: str = Field(default="member", pattern="(owner|admin|member|viewer)")


@router.get("/me")
async def get_current_org(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    org = db.query(Organization).filter(Organization.id == current_user.org_id).first()
    if not org:
        raise HTTPException(status_code=status.HTTP_404, detail="Organization not found")
    return {"id": org.id, "name": org.name, "plan": org.plan}


@router.get("/members")
async def list_members(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    members = db.query(User).filter(User.org_id == current_user.org_id).all()
    return [
        {
            "id": m.id,
            "email": m.email,
            "full_name": m.full_name,
            "role": m.role,
        }
        for m in members
    ]


@router.post("/invite")
async def invite_member(
    body: InviteBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Check if user exists with this email
    existing = db.query(User).filter(User.email == body.email).first()
    if existing:
        if existing.org_id:
            # Already in an org - need to handle differently
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already belongs to an organization",
            )
        # Attach to current org
        existing.org_id = current_user.org_id
        db.commit()
        return {"detail": "Invite accepted, user added to org"}

    # Create new user in the current org (no password - invite-only for now)
    user = User(
        email=body.email,
        password_hash="",
        full_name=body.email.split("@")[0],
        role=body.role,
        org_id=current_user.org_id,
    )
    db.add(user)
    db.commit()
    return {"detail": "Invite accepted, user added to org"}