from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from app.core.database import get_session
from app.models.user import User
from app.core.security import get_current_admin_user
from app.services.admin_service import AdminService
from app.schemas.admin import (
    AdminLoginRequest, AdminLoginResponse, AdminPasswordReset,
    UserCount, UserDetail, AdminUserUpdate, AdminStats
)
from typing import Dict, Any, List

router = APIRouter(prefix="/admin", tags=["admin"])

# Admin router endpoints

@router.post("/login", response_model=AdminLoginResponse)
def admin_login(login_data: AdminLoginRequest, session: Session = Depends(get_session)):
    """
    Admin-specific login endpoint with enhanced security validation.
    Only users with admin privileges can authenticate through this endpoint.
    """
    return AdminService.authenticate_admin(login_data.username, login_data.password, session)

@router.get("/stats", response_model=AdminStats)
def get_admin_stats(
    current_user: User = Depends(get_current_admin_user),
    session: Session = Depends(get_session)
):
    """
    Get comprehensive system statistics for admin dashboard.
    """
    return AdminService.get_system_stats(session)

@router.get("/users", response_model=List[UserDetail])
def get_all_users_detailed(
    current_user: User = Depends(get_current_admin_user),
    session: Session = Depends(get_session)
):
    """
    Get detailed information about all users including their data counts.
    """
    return AdminService.get_all_users_detailed(session)

@router.get("/users/{user_id}", response_model=UserDetail)
def get_user_detailed(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    session: Session = Depends(get_session)
):
    """
    Get detailed information about a specific user.
    """
    return AdminService.get_user_detailed(user_id, session)

@router.put("/users/{user_id}")
def update_user_admin(
    user_id: int,
    data: AdminUserUpdate,
    current_user: User = Depends(get_current_admin_user),
    session: Session = Depends(get_session)
):
    """
    Update user information as an admin.
    """
    return AdminService.update_user_admin(user_id, data, session)

@router.get("/users/{user_id}/data", response_model=Dict[str, Any])
def get_user_data(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    session: Session = Depends(get_session)
):
    """
    Get all data associated with a specific user.
    """
    return AdminService.get_user_data(user_id, session)

@router.post("/users/{user_id}/reset-password")
def admin_reset_user_password(
    user_id: int,
    reset_data: AdminPasswordReset,
    current_user: User = Depends(get_current_admin_user),
    session: Session = Depends(get_session)
):
    """
    Reset a user's password as an admin.
    """
    message = AdminService.reset_user_password(user_id, reset_data.new_password, session)
    return {"message": message}

@router.delete("/users/{user_id}")
def delete_user_admin(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    session: Session = Depends(get_session)
):
    """
    Delete a user and all their associated data.
    """
    message = AdminService.delete_user_admin(user_id, current_user.id, session)
    return {"message": message}

@router.delete("/users/truncate-all")
def truncate_all_users(
    current_user: User = Depends(get_current_admin_user),
    session: Session = Depends(get_session)
):
    """
    ⚠️ DANGER: Delete ALL users and ALL related data.
    Only use for development/testing purposes.
    Requires admin privileges.
    """
    message = AdminService.truncate_all_users(session)
    return {"message": message} 