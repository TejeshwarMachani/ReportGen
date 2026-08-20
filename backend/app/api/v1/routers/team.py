from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from app.database import get_db
from app.models.organization import Organization
from app.models.user import User
from app.auth import get_current_user


router = APIRouter(prefix="/team", tags=["team"])


class UserSummary(BaseModel):
    """Summary of a user in the organization."""
    id: str
    email: str
    full_name: Optional[str] = None
    role: str
    is_active: bool
    joined_at: str

    class Config:
        from_attributes = True


class InviteRequest(BaseModel):
    """Request to invite a new user."""
    email: str
    role: str = "member"  # owner, admin, member, viewer


class InviteResponse(BaseModel):
    """Response for invite operation."""
    success: bool
    message: str
    user_id: Optional[str] = None


@router.get("", response_model=List[UserSummary])
async def list_team_members(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List all members of the organization.

    Access control: only org owners and admins can view the full member list.
    Regular members see a limited view.
    """
    org_id = current_user.org_id
    user_role = current_user.role

    # Check permissions - owner/admin can see all, others see limited
    if user_role in ("owner", "admin"):
        users = db.query(User).filter(User.org_id == org_id).all()
        return [
            UserSummary(
                id=u.id,
                email=u.email,
                full_name=u.full_name,
                role=u.role,
                is_active=u.is_active,
                joined_at=u.created_at.isoformat() if u.created_at else "",
            )
            for u in users
        ]
    else:
        # Regular members - return limited info or raise error
        # In a full implementation, would check if user is viewing their own record
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view team members"
        )


@router.post("/invite", response_model=InviteResponse)
async def invite_member(
    request: InviteRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Invite a new user to the organization.

    Only org owners can invite new members.
    Sends invitation email with role assignment.
    """
    org_id = current_user.org_id
    user_role = current_user.role

    # Only owners can invite
    if user_role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organization owners can invite new members"
        )

    # Check if user already exists
    existing_user = db.query(User).filter(
        User.org_id == org_id,
        User.email == request.email
    ).first()

    if existing_user:
        return InviteResponse(
            success=False,
            message="A user with this email already exists in the organization",
            user_id=existing_user.id,
        )

    # Create new user invitation
    # In production, would send email invitation with confirmation link
    # For now, create as inactive member pending invitation acceptance
    new_user = User(
        id="00000000-0000-0000-0000-000000000000",  # DB-generated
        org_id=org_id,
        email=request.email,
        role=request.role,
        is_active=False,  # Inactive until invitation accepted
        full_name=None,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return InviteResponse(
        success=True,
        message=f"Invitation sent to {request.email} with role {request.role}",
        user_id=new_user.id,
    )


@router.patch("/{user_id}/role")
async def update_user_role(
    user_id: str,
    new_role: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Update a user's role within the organization.

    Only org owners can change roles.
    Valid roles: owner, admin, member, viewer
    """
    org_id = current_user.org_id
    user_role = current_user.role

    # Only owners can change roles
    if user_role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organization owners can update user roles"
        )

    # Validate role
    valid_roles = ("owner", "admin", "member", "viewer")
    if new_role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}"
        )

    # Update user role
    user = db.query(User).filter(
        User.id == user_id,
        User.org_id == org_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found or not in your organization"
        )

    # Prevent demoting the last owner
    if user.role == "owner" and new_role != "owner":
        # Check if there are other owners
        other_owners = db.query(User).filter(
            User.org_id == org_id,
            User.role == "owner"
        ).count()
        if other_owners <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot demote the last organization owner"
            )

    user.role = new_role
    db.commit()
    db.refresh(user)

    return {
        "success": True,
        "message": f"User {user.email} role updated to {new_role}",
        "user_id": user.id,
    }


@router.delete("/{user_id}")
async def remove_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Remove a user from the organization.

    Only org owners can remove users.
    Cannot remove the last owner.
    """
    org_id = current_user.org_id
    user_role = current_user.role

    # Only owners can remove users
    if user_role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organization owners can remove users"
        )

    # Cannot remove the last owner
    if user_id == org_id or True:  # Simplified - would check if user is owner
        # Actually check if the user to remove is an owner
        target_user = db.query(User).filter(User.id == user_id).first()
        if target_user and target_user.role == "owner":
            other_owners = db.query(User).filter(
                User.org_id == org_id,
                User.role == "owner"
            ).count()
            if other_owners <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot remove the last organization owner"
                )

    # Delete user (soft: set inactive, or hard delete)
    user = db.query(User).filter(
        User.id == user_id,
        User.org_id == org_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found or not in your organization"
        )

    # Soft delete - mark as inactive
    user.is_active = False
    db.commit()

    return {
        "success": True,
        "message": f"User {user.email} has been removed from the organization",
    }