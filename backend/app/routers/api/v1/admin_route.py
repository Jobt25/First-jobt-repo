"""
app/routers/api/v1/admin_route.py

Admin endpoints for system management.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Dict, Any

from app.core.database import get_db
from app.core.oauth2 import get_current_admin
from app.models.user import User
from app.services.admin_service import AdminService
from app.schemas.admin_schema import (
    AdminDashboardStats, 
    UserManagementResponse,
    UpdateUserStatusRequest
)
from app.schemas.common_schema import PaginatedResponse

router = APIRouter(prefix="/admin", tags=["Admin"])


# ==================== USER MANAGEMENT ====================

@router.get("/users", response_model=PaginatedResponse[UserManagementResponse])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: str = Query(None, min_length=2),
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    List users with pagination and search.
    
    Access: Admin only.
    """
    service = AdminService(db)
    result = await service.list_users(skip=skip, limit=limit, search=search)
    return result


@router.get("/users/{user_id}", response_model=UserManagementResponse)
async def get_user_details(
    user_id: UUID,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed user information.
    
    Access: Admin only.
    """
    service = AdminService(db)
    user = await service.get_user_details(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


@router.patch("/users/{user_id}/status", response_model=UserManagementResponse)
async def update_user_status(
    user_id: UUID,
    status_data: UpdateUserStatusRequest,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Activate or deactivate a user account.
    
    Access: Admin only.
    """
    # Prevent self-ban
    if str(user_id) == str(current_admin.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own status"
        )
        
    service = AdminService(db)
    updated_user = await service.update_user_status(user_id, status_data.is_active)
    
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
        
    return updated_user


# ==================== SYSTEM ANALYTICS ====================

@router.get("/stats", response_model=AdminDashboardStats)
async def get_dashboard_stats(
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Get system-wide statistics for the admin dashboard.
    
    Access: Admin only.
    """
    service = AdminService(db)
    return await service.get_dashboard_stats()
