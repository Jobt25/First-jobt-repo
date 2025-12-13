"""
app/services/category_service.py

Business logic for job category management.

Handles:
- CRUD operations for job categories
- Category validation
- Statistics aggregation
- Active/inactive filtering
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from typing import Optional, List
from uuid import UUID
import logging

from ..models.job_category import JobCategory
from ..models.question_template import QuestionTemplate
from ..models.interview_session import InterviewSession
from ..schemas.job_category_schema import (
    JobCategoryCreate,
    JobCategoryUpdate,
    JobCategoryResponse,
    JobCategoryDetail
)

logger = logging.getLogger(__name__)


class CategoryService:
    """Service class for job category operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ==================== RETRIEVE OPERATIONS ====================

    async def list_categories(
            self,
            industry: Optional[str] = None,
            is_active: Optional[bool] = True,
            skip: int = 0,
            limit: int = 100
    ) -> List[JobCategory]:
        """
        List job categories with optional filtering.

        Args:
            industry: Filter by industry (e.g., "Technology")
            is_active: Filter by active status (default: True)
            skip: Number of records to skip (pagination)
            limit: Maximum number of records to return

        Returns:
            List of JobCategory objects
        """
        query = select(JobCategory)

        # Apply filters
        filters = []
        if industry is not None:
            filters.append(JobCategory.industry == industry)
        if is_active is not None:
            filters.append(JobCategory.is_active == is_active)

        if filters:
            query = query.where(and_(*filters))

        # Apply pagination
        query = query.offset(skip).limit(limit).order_by(JobCategory.name)

        result = await self.db.execute(query)
        categories = result.scalars().all()

        logger.info(
            f"Listed {len(categories)} categories "
            f"(industry={industry}, is_active={is_active})"
        )

        return categories

    async def get_category_by_id(self, category_id: UUID) -> JobCategory:
        """
        Get single category by ID.

        Args:
            category_id: Category UUID

        Returns:
            JobCategory object

        Raises:
            HTTPException: If category not found
        """
        result = await self.db.execute(
            select(JobCategory).where(JobCategory.id == category_id)
        )
        category = result.scalar_one_or_none()

        if not category:
            logger.warning(f"Category not found: {category_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job category with ID {category_id} not found"
            )

        return category

    async def get_category_by_name(self, name: str) -> Optional[JobCategory]:
        """
        Get category by name (case-insensitive).

        Args:
            name: Category name

        Returns:
            JobCategory object or None
        """
        result = await self.db.execute(
            select(JobCategory).where(
                func.lower(JobCategory.name) == name.lower()
            )
        )
        return result.scalar_one_or_none()

    async def get_category_detail(self, category_id: UUID) -> dict:
        """
        Get category with detailed statistics.

        Includes:
        - Total interviews conducted
        - Average completion rate
        - Average interview score

        Args:
            category_id: Category UUID

        Returns:
            Dictionary with category details and statistics
        """
        category = await self.get_category_by_id(category_id)

        # Get interview statistics
        stats_query = select(
            func.count(InterviewSession.id).label('total_interviews'),
            func.count(
                InterviewSession.id
            ).filter(
                InterviewSession.status == 'completed'
            ).label('completed_interviews'),
        ).where(
            InterviewSession.category_id == category_id
        )

        result = await self.db.execute(stats_query)
        stats = result.one_or_none()

        total_interviews = stats[0] if stats else 0
        completed_interviews = stats[1] if stats else 0

        # Calculate completion rate
        completion_rate = None
        if total_interviews > 0:
            completion_rate = (completed_interviews / total_interviews) * 100

        # Get average score from feedback
        avg_score_query = select(
            func.avg(InterviewSession.id)  # Placeholder - will join feedback table
        ).where(
            InterviewSession.category_id == category_id,
            InterviewSession.status == 'completed'
        )
        # TODO: Join with feedback table when implementing feedback service

        return {
            "category": category,
            "total_interviews": total_interviews,
            "completed_interviews": completed_interviews,
            "completion_rate": completion_rate,
            "avg_score": None  # Will be populated from feedback table
        }

    async def get_industries(self) -> List[str]:
        """
        Get list of unique industries.

        Returns:
            List of industry names
        """
        result = await self.db.execute(
            select(JobCategory.industry)
            .distinct()
            .where(JobCategory.industry.isnot(None))
            .order_by(JobCategory.industry)
        )
        industries = [row[0] for row in result.all()]
        return industries

    # ==================== CREATE OPERATIONS ====================

    async def create_category(
            self,
            category_data: JobCategoryCreate
    ) -> JobCategory:
        """
        Create a new job category.

        Args:
            category_data: Category creation data

        Returns:
            Created JobCategory object

        Raises:
            HTTPException: If category name already exists
        """
        # Check if category name already exists
        existing = await self.get_category_by_name(category_data.name)
        if existing:
            logger.warning(f"Duplicate category name: {category_data.name}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category '{category_data.name}' already exists"
            )

        # Create category
        category = JobCategory(
            name=category_data.name,
            description=category_data.description,
            industry=category_data.industry,
            is_active=True,
            typical_questions_count=0
        )

        self.db.add(category)
        await self.db.commit()
        await self.db.refresh(category)

        logger.info(f"✓ Created category: {category.name} (ID: {category.id})")

        return category

    # ==================== UPDATE OPERATIONS ====================

    async def update_category(
            self,
            category_id: UUID,
            update_data: JobCategoryUpdate
    ) -> JobCategory:
        """
        Update existing job category.

        Args:
            category_id: Category UUID
            update_data: Fields to update

        Returns:
            Updated JobCategory object

        Raises:
            HTTPException: If category not found or name conflict
        """
        # Get existing category
        category = await self.get_category_by_id(category_id)

        # Check for name conflict if name is being updated
        if update_data.name and update_data.name != category.name:
            existing = await self.get_category_by_name(update_data.name)
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Category '{update_data.name}' already exists"
                )

        # Update fields (only non-None values)
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(category, field, value)

        await self.db.commit()
        await self.db.refresh(category)

        logger.info(f"✓ Updated category: {category.name} (ID: {category_id})")

        return category

    # ==================== DELETE OPERATIONS ====================

    async def delete_category(
            self,
            category_id: UUID,
            soft_delete: bool = True
    ) -> dict:
        """
        Delete job category (soft or hard delete).

        Soft delete: Set is_active = False (default, recommended)
        Hard delete: Permanently remove from database

        Args:
            category_id: Category UUID
            soft_delete: If True, soft delete; if False, hard delete

        Returns:
            Dictionary with deletion confirmation

        Raises:
            HTTPException: If category not found or has dependencies
        """
        category = await self.get_category_by_id(category_id)

        if soft_delete:
            # Soft delete: just deactivate
            category.is_active = False
            await self.db.commit()

            logger.info(f"✓ Soft deleted category: {category.name} (ID: {category_id})")

            return {
                "message": "Category deactivated successfully",
                "category_id": str(category_id),
                "category_name": category.name,
                "deleted": False,
                "deactivated": True
            }
        else:
            # Hard delete: check for dependencies
            # Check if category has questions
            questions_query = select(func.count(QuestionTemplate.id)).where(
                QuestionTemplate.category_id == category_id
            )
            result = await self.db.execute(questions_query)
            questions_count = result.scalar()

            # Check if category has interviews
            interviews_query = select(func.count(InterviewSession.id)).where(
                InterviewSession.category_id == category_id
            )
            result = await self.db.execute(interviews_query)
            interviews_count = result.scalar()

            if questions_count > 0 or interviews_count > 0:
                logger.warning(
                    f"Cannot hard delete category {category_id}: "
                    f"has {questions_count} questions and {interviews_count} interviews"
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Cannot delete category '{category.name}' because it has "
                        f"{questions_count} question(s) and {interviews_count} interview(s). "
                        "Consider soft delete (deactivation) instead."
                    )
                )

            # Safe to hard delete
            await self.db.delete(category)
            await self.db.commit()

            logger.info(f"✓ Hard deleted category: {category.name} (ID: {category_id})")

            return {
                "message": "Category permanently deleted",
                "category_id": str(category_id),
                "category_name": category.name,
                "deleted": True,
                "deactivated": False
            }

    # ==================== STATISTICS ====================

    async def get_category_stats(self) -> dict:
        """
        Get overall category statistics.

        Returns:
            Dictionary with aggregate statistics
        """
        # Total categories
        total_query = select(func.count(JobCategory.id))
        total_result = await self.db.execute(total_query)
        total_categories = total_result.scalar()

        # Active categories
        active_query = select(func.count(JobCategory.id)).where(
            JobCategory.is_active == True
        )
        active_result = await self.db.execute(active_query)
        active_categories = active_result.scalar()

        # Categories by industry
        industry_query = select(
            JobCategory.industry,
            func.count(JobCategory.id).label('count')
        ).where(
            JobCategory.is_active == True
        ).group_by(
            JobCategory.industry
        ).order_by(
            func.count(JobCategory.id).desc()
        )
        industry_result = await self.db.execute(industry_query)
        industries = [
            {"industry": row[0] or "Uncategorized", "count": row[1]}
            for row in industry_result.all()
        ]

        return {
            "total_categories": total_categories,
            "active_categories": active_categories,
            "inactive_categories": total_categories - active_categories,
            "categories_by_industry": industries
        }

    # ==================== UTILITY METHODS ====================

    async def update_question_count(self, category_id: UUID) -> None:
        """
        Update the typical_questions_count for a category.

        Called after questions are added/removed.

        Args:
            category_id: Category UUID
        """
        # Count active questions
        count_query = select(func.count(QuestionTemplate.id)).where(
            QuestionTemplate.category_id == category_id,
            QuestionTemplate.is_active == True
        )
        result = await self.db.execute(count_query)
        count = result.scalar()

        # Update category
        await self.db.execute(
            update(JobCategory)
            .where(JobCategory.id == category_id)
            .values(typical_questions_count=count)
        )
        await self.db.commit()

        logger.debug(f"Updated question count for category {category_id}: {count}")