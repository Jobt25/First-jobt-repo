"""
app/routers/api/v1/categories_route.py

Job category management endpoints.

Public endpoints:
- GET /categories - List all active categories
- GET /categories/{id} - Get category details

Admin-only endpoints:
- POST /categories - Create category
- PUT /categories/{id} - Update category
- DELETE /categories/{id} - Delete category
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from uuid import UUID
import logging

from app.core.database import get_db
from app.core.oauth2 import get_current_user, get_current_admin
from app.models.user import User
from app.services.category_service import CategoryService
from app.schemas.job_category_schema import (
    JobCategoryCreate,
    JobCategoryUpdate,
    JobCategoryResponse,
    JobCategoryDetail
)
from app.schemas.common_schema import MessageResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/categories", tags=["Job Categories"])


# ==================== PUBLIC ENDPOINTS ====================

@router.get("", response_model=List[JobCategoryResponse])
async def list_categories(
        industry: Optional[str] = Query(None, description="Filter by industry"),
        is_active: Optional[bool] = Query(True, description="Filter by active status"),
        skip: int = Query(0, ge=0, description="Number of records to skip"),
        limit: int = Query(100, ge=1, le=100, description="Maximum records to return"),
        db: AsyncSession = Depends(get_db)
):
    """
    List all job categories.

    **Public endpoint** - No authentication required.

    Query Parameters:
    - industry: Filter by industry (e.g., "Technology", "Healthcare")
    - is_active: Show only active/inactive categories (default: True)
    - skip: Pagination offset (default: 0)
    - limit: Maximum results (default: 100, max: 100)

    Returns:
    - List of job categories with basic information

    Example:
    ```
    GET /api/v1/categories?industry=Technology&limit=20
    ```
    """
    service = CategoryService(db)
    categories = await service.list_categories(
        industry=industry,
        is_active=is_active,
        skip=skip,
        limit=limit
    )

    return [JobCategoryResponse.model_validate(cat) for cat in categories]


@router.get("/industries", response_model=List[str])
async def list_industries(
        db: AsyncSession = Depends(get_db)
):
    """
    Get list of all unique industries.

    **Public endpoint** - No authentication required.

    Useful for frontend dropdowns and filtering.

    Returns:
    - List of industry names

    Example Response:
    ```json
    ["Technology", "Healthcare", "Finance", "Marketing", "Sales"]
    ```
    """
    service = CategoryService(db)
    industries = await service.get_industries()
    return industries


@router.get("/stats")
async def get_category_statistics(
        db: AsyncSession = Depends(get_db)
):
    """
    Get aggregate statistics about job categories.

    **Public endpoint** - No authentication required.

    Returns:
    - Total categories count
    - Active vs inactive breakdown
    - Categories grouped by industry

    Useful for analytics dashboards.
    """
    service = CategoryService(db)
    stats = await service.get_category_stats()
    return stats


@router.get("/{category_id}", response_model=JobCategoryResponse)
async def get_category(
        category_id: UUID,
        db: AsyncSession = Depends(get_db)
):
    """
    Get detailed information about a specific job category.

    **Public endpoint** - No authentication required.

    Path Parameters:
    - category_id: UUID of the job category

    Returns:
    - Complete category information including:
      - Name, description, industry
      - Question count
      - Active status
      - Creation/update timestamps

    Raises:
    - 404: Category not found
    """
    service = CategoryService(db)
    category = await service.get_category_by_id(category_id)
    return JobCategoryResponse.model_validate(category)


@router.get("/{category_id}/detail", response_model=JobCategoryDetail)
async def get_category_detail(
        category_id: UUID,
        db: AsyncSession = Depends(get_db)
):
    """
    Get category with detailed statistics.

    **Public endpoint** - No authentication required.

    Includes:
    - All basic category information
    - Total interviews conducted
    - Completion rate
    - Average interview scores (when feedback implemented)

    Path Parameters:
    - category_id: UUID of the job category

    Raises:
    - 404: Category not found
    """
    service = CategoryService(db)
    detail = await service.get_category_detail(category_id)

    return JobCategoryDetail(
        **JobCategoryResponse.model_validate(detail['category']).model_dump(),
        total_interviews=detail['total_interviews'],
        avg_completion_rate=detail['completion_rate'],
        avg_score=detail['avg_score']
    )


# ==================== ADMIN ENDPOINTS ====================

@router.post("", response_model=JobCategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
        category_data: JobCategoryCreate,
        admin: User = Depends(get_current_admin),
        db: AsyncSession = Depends(get_db)
):
    """
    Create a new job category.

    **Admin only** - Requires admin authentication.

    Request Body:
    ```json
    {
        "name": "Data Scientist",
        "description": "Machine learning and data analysis roles",
        "industry": "Technology"
    }
    ```

    Returns:
    - Created category with generated ID and timestamps

    Raises:
    - 400: Category name already exists
    - 401: Not authenticated
    - 403: Not admin

    Notes:
    - Category name must be unique (case-insensitive)
    - Category is created as active by default
    """
    logger.info(f"Admin {admin.email} creating category: {category_data.name}")

    service = CategoryService(db)
    category = await service.create_category(category_data)

    return JobCategoryResponse.model_validate(category)


@router.put("/{category_id}", response_model=JobCategoryResponse)
async def update_category(
        category_id: UUID,
        update_data: JobCategoryUpdate,
        admin: User = Depends(get_current_admin),
        db: AsyncSession = Depends(get_db)
):
    """
    Update an existing job category.

    **Admin only** - Requires admin authentication.

    Path Parameters:
    - category_id: UUID of the category to update

    Request Body (all fields optional):
    ```json
    {
        "name": "Senior Data Scientist",
        "description": "Updated description",
        "industry": "Technology",
        "is_active": true
    }
    ```

    Returns:
    - Updated category

    Raises:
    - 400: New name conflicts with existing category
    - 401: Not authenticated
    - 403: Not admin
    - 404: Category not found

    Notes:
    - Only provided fields will be updated
    - Name uniqueness is checked if name is updated
    """
    logger.info(f"Admin {admin.email} updating category: {category_id}")

    service = CategoryService(db)
    category = await service.update_category(category_id, update_data)

    return JobCategoryResponse.model_validate(category)


@router.delete("/{category_id}", response_model=MessageResponse)
async def delete_category(
        category_id: UUID,
        hard_delete: bool = Query(
            False,
            description="If true, permanently delete; if false, deactivate"
        ),
        admin: User = Depends(get_current_admin),
        db: AsyncSession = Depends(get_db)
):
    """
    Delete (deactivate or remove) a job category.

    **Admin only** - Requires admin authentication.

    Path Parameters:
    - category_id: UUID of the category to delete

    Query Parameters:
    - hard_delete:
      - false (default): Soft delete (deactivate, recommended)
      - true: Permanently delete from database

    Soft Delete (Recommended):
    - Sets is_active = False
    - Category remains in database for historical data
    - Can be reactivated later
    - Safe operation

    Hard Delete:
    - Permanently removes category from database
    - Only allowed if category has NO questions or interviews
    - Cannot be undone
    - Use with extreme caution

    Returns:
    - Confirmation message with deletion details

    Raises:
    - 400: Hard delete blocked due to dependencies
    - 401: Not authenticated
    - 403: Not admin
    - 404: Category not found

    Example:
    ```
    DELETE /api/v1/categories/{id}?hard_delete=false
    ```
    """
    logger.info(
        f"Admin {admin.email} deleting category {category_id} "
        f"(hard_delete={hard_delete})"
    )

    service = CategoryService(db)
    result = await service.delete_category(category_id, soft_delete=not hard_delete)

    return MessageResponse(
        message=result['message'],
        detail=f"Category: {result['category_name']}"
    )


@router.patch("/{category_id}/activate", response_model=JobCategoryResponse)
async def activate_category(
        category_id: UUID,
        admin: User = Depends(get_current_admin),
        db: AsyncSession = Depends(get_db)
):
    """
    Reactivate a deactivated category.

    **Admin only** - Requires admin authentication.

    Path Parameters:
    - category_id: UUID of the category to activate

    Returns:
    - Reactivated category

    Raises:
    - 401: Not authenticated
    - 403: Not admin
    - 404: Category not found

    Notes:
    - Sets is_active = True
    - Useful for restoring soft-deleted categories
    """
    logger.info(f"Admin {admin.email} activating category: {category_id}")

    service = CategoryService(db)
    update_data = JobCategoryUpdate(is_active=True)
    category = await service.update_category(category_id, update_data)

    return JobCategoryResponse.model_validate(category)


@router.patch("/{category_id}/deactivate", response_model=JobCategoryResponse)
async def deactivate_category(
        category_id: UUID,
        admin: User = Depends(get_current_admin),
        db: AsyncSession = Depends(get_db)
):
    """
    Deactivate a category (soft delete).

    **Admin only** - Requires admin authentication.

    Path Parameters:
    - category_id: UUID of the category to deactivate

    Returns:
    - Deactivated category

    Raises:
    - 401: Not authenticated
    - 403: Not admin
    - 404: Category not found

    Notes:
    - Same as soft delete
    - Sets is_active = False
    - Category remains in database
    - Can be reactivated with /activate endpoint
    """
    logger.info(f"Admin {admin.email} deactivating category: {category_id}")

    service = CategoryService(db)
    update_data = JobCategoryUpdate(is_active=False)
    category = await service.update_category(category_id, update_data)

    return JobCategoryResponse.model_validate(category)