"""
scripts/seed_categories.py

Seed initial job categories for Jobt AI Career Coach.

Run with:
    python scripts/seed_categories.py
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import AsyncSessionLocal
from app.models.job_category import JobCategory
from app.models.question_template import QuestionTemplate, DifficultyLevel
from datetime import datetime

# ==================== CATEGORY DATA ====================

CATEGORIES = [
    {
        "name": "Software Engineer",
        "description": "Backend, frontend, and full-stack software development roles. Covers programming, system design, algorithms, and software architecture.",
        "industry": "Technology",
        "questions": [
            {
                "text": "Tell me about yourself and your background in software development.",
                "difficulty": DifficultyLevel.BEGINNER,
                "keywords": ["experience", "projects", "technologies", "education"],
                "ideal_length": 150
            },
            {
                "text": "Describe a challenging technical problem you solved recently. What was your approach?",
                "difficulty": DifficultyLevel.INTERMEDIATE,
                "keywords": ["problem-solving", "technical", "solution", "approach"],
                "ideal_length": 200
            },
            {
                "text": "How do you approach system design for scalable applications?",
                "difficulty": DifficultyLevel.ADVANCED,
                "keywords": ["scalability", "architecture", "performance", "design patterns"],
                "ideal_length": 250
            },
            {
                "text": "Explain a situation where you had to debug a complex issue in production.",
                "difficulty": DifficultyLevel.INTERMEDIATE,
                "keywords": ["debugging", "production", "troubleshooting", "monitoring"],
                "ideal_length": 180
            },
            {
                "text": "How do you stay updated with new technologies and best practices?",
                "difficulty": DifficultyLevel.BEGINNER,
                "keywords": ["learning", "growth", "community", "resources"],
                "ideal_length": 120
            }
        ]
    },
    {
        "name": "Product Manager",
        "description": "Product strategy, roadmap planning, stakeholder management, and cross-functional leadership in technology companies.",
        "industry": "Technology",
        "questions": [
            {
                "text": "Walk me through how you would prioritize features for a product roadmap.",
                "difficulty": DifficultyLevel.INTERMEDIATE,
                "keywords": ["prioritization", "roadmap", "stakeholders", "metrics"],
                "ideal_length": 200
            },
            {
                "text": "Tell me about a time you had to make a difficult product decision with incomplete data.",
                "difficulty": DifficultyLevel.ADVANCED,
                "keywords": ["decision-making", "uncertainty", "data", "trade-offs"],
                "ideal_length": 220
            },
            {
                "text": "How do you handle disagreements between engineering and design teams?",
                "difficulty": DifficultyLevel.INTERMEDIATE,
                "keywords": ["conflict resolution", "collaboration", "communication"],
                "ideal_length": 180
            },
            {
                "text": "What metrics would you track for a B2B SaaS product?",
                "difficulty": DifficultyLevel.INTERMEDIATE,
                "keywords": ["metrics", "analytics", "KPIs", "SaaS"],
                "ideal_length": 150
            }
        ]
    },
    {
        "name": "Data Analyst",
        "description": "Data analysis, business intelligence, SQL, data visualization, and insight generation for business decision-making.",
        "industry": "Technology",
        "questions": [
            {
                "text": "Describe your experience with SQL and database querying.",
                "difficulty": DifficultyLevel.BEGINNER,
                "keywords": ["SQL", "queries", "database", "joins"],
                "ideal_length": 150
            },
            {
                "text": "Walk me through how you would analyze a sudden drop in user engagement.",
                "difficulty": DifficultyLevel.INTERMEDIATE,
                "keywords": ["analysis", "metrics", "investigation", "insights"],
                "ideal_length": 200
            },
            {
                "text": "How do you ensure data quality and accuracy in your analyses?",
                "difficulty": DifficultyLevel.INTERMEDIATE,
                "keywords": ["data quality", "validation", "accuracy", "processes"],
                "ideal_length": 180
            }
        ]
    },
    {
        "name": "Sales Representative",
        "description": "B2B and B2C sales roles including prospecting, relationship building, negotiation, and closing deals.",
        "industry": "Sales",
        "questions": [
            {
                "text": "Tell me about your sales experience and your most successful deal.",
                "difficulty": DifficultyLevel.BEGINNER,
                "keywords": ["experience", "success", "achievement", "metrics"],
                "ideal_length": 150
            },
            {
                "text": "How do you handle objections from potential customers?",
                "difficulty": DifficultyLevel.INTERMEDIATE,
                "keywords": ["objections", "persuasion", "value proposition"],
                "ideal_length": 180
            },
            {
                "text": "Describe your approach to building and managing a sales pipeline.",
                "difficulty": DifficultyLevel.INTERMEDIATE,
                "keywords": ["pipeline", "prospecting", "organization", "CRM"],
                "ideal_length": 170
            }
        ]
    },
    {
        "name": "Marketing Manager",
        "description": "Digital marketing, campaign management, brand strategy, content marketing, and growth marketing roles.",
        "industry": "Marketing",
        "questions": [
            {
                "text": "What marketing channels have you had the most success with and why?",
                "difficulty": DifficultyLevel.BEGINNER,
                "keywords": ["channels", "campaigns", "results", "ROI"],
                "ideal_length": 150
            },
            {
                "text": "How do you measure the success of a marketing campaign?",
                "difficulty": DifficultyLevel.INTERMEDIATE,
                "keywords": ["metrics", "KPIs", "attribution", "analytics"],
                "ideal_length": 180
            },
            {
                "text": "Tell me about a campaign that didn't perform well. What did you learn?",
                "difficulty": DifficultyLevel.INTERMEDIATE,
                "keywords": ["failure", "learning", "optimization", "testing"],
                "ideal_length": 200
            }
        ]
    },
    {
        "name": "Customer Success Manager",
        "description": "Customer relationship management, onboarding, retention, upselling, and ensuring customer satisfaction in SaaS companies.",
        "industry": "Technology",
        "questions": [
            {
                "text": "How do you approach onboarding new customers?",
                "difficulty": DifficultyLevel.BEGINNER,
                "keywords": ["onboarding", "training", "adoption", "success"],
                "ideal_length": 150
            },
            {
                "text": "Describe a time you turned around a dissatisfied customer.",
                "difficulty": DifficultyLevel.INTERMEDIATE,
                "keywords": ["customer service", "problem-solving", "satisfaction"],
                "ideal_length": 200
            }
        ]
    },
    {
        "name": "UI/UX Designer",
        "description": "User interface and user experience design, wireframing, prototyping, user research, and design systems.",
        "industry": "Technology",
        "questions": [
            {
                "text": "Walk me through your design process from concept to final product.",
                "difficulty": DifficultyLevel.INTERMEDIATE,
                "keywords": ["design process", "research", "iteration", "testing"],
                "ideal_length": 200
            },
            {
                "text": "How do you handle feedback that conflicts with your design decisions?",
                "difficulty": DifficultyLevel.INTERMEDIATE,
                "keywords": ["feedback", "collaboration", "compromise", "advocacy"],
                "ideal_length": 180
            }
        ]
    },
    {
        "name": "Project Manager",
        "description": "Project planning, execution, stakeholder management, risk management, and team coordination across various industries.",
        "industry": "Management",
        "questions": [
            {
                "text": "How do you handle a project that's falling behind schedule?",
                "difficulty": DifficultyLevel.INTERMEDIATE,
                "keywords": ["project management", "deadlines", "prioritization"],
                "ideal_length": 180
            },
            {
                "text": "Describe your experience with Agile or other project management methodologies.",
                "difficulty": DifficultyLevel.BEGINNER,
                "keywords": ["agile", "scrum", "methodology", "process"],
                "ideal_length": 150
            }
        ]
    },
    {
        "name": "Human Resources Manager",
        "description": "Recruitment, employee relations, performance management, HR policies, and organizational development.",
        "industry": "Human Resources",
        "questions": [
            {
                "text": "How do you approach difficult conversations with employees?",
                "difficulty": DifficultyLevel.INTERMEDIATE,
                "keywords": ["communication", "conflict resolution", "empathy"],
                "ideal_length": 180
            },
            {
                "text": "What strategies do you use to improve employee retention?",
                "difficulty": DifficultyLevel.INTERMEDIATE,
                "keywords": ["retention", "engagement", "culture", "development"],
                "ideal_length": 200
            }
        ]
    },
    {
        "name": "Financial Analyst",
        "description": "Financial modeling, forecasting, budgeting, investment analysis, and financial reporting for businesses.",
        "industry": "Finance",
        "questions": [
            {
                "text": "Explain how you would build a financial model for a new business.",
                "difficulty": DifficultyLevel.ADVANCED,
                "keywords": ["financial modeling", "assumptions", "projections"],
                "ideal_length": 220
            },
            {
                "text": "How do you stay informed about market trends and economic indicators?",
                "difficulty": DifficultyLevel.BEGINNER,
                "keywords": ["research", "trends", "analysis", "sources"],
                "ideal_length": 140
            }
        ]
    }
]


# ==================== SEED FUNCTIONS ====================

async def seed_categories():
    """Seed job categories with questions"""
    async with AsyncSessionLocal() as db:
        print("=" * 70)
        print("🌱 Starting database seeding for Job Categories")
        print("=" * 70)

        categories_created = 0
        questions_created = 0

        for cat_data in CATEGORIES:
            # Check if category already exists
            from sqlalchemy import select
            result = await db.execute(
                select(JobCategory).where(JobCategory.name == cat_data['name'])
            )
            existing = result.scalar_one_or_none()

            if existing:
                print(f"⏭  Category already exists: {cat_data['name']}")
                continue

            # Create category
            category = JobCategory(
                name=cat_data['name'],
                description=cat_data['description'],
                industry=cat_data['industry'],
                is_active=True,
                typical_questions_count=len(cat_data.get('questions', []))
            )
            db.add(category)
            await db.flush()  # Get category ID

            categories_created += 1
            print(f"✓ Created category: {category.name}")

            # Add questions if provided
            if 'questions' in cat_data:
                for q_data in cat_data['questions']:
                    question = QuestionTemplate(
                        category_id=category.id,
                        question_text=q_data['text'],
                        difficulty=q_data['difficulty'],
                        expected_keywords=q_data.get('keywords', []),
                        ideal_response_length=q_data.get('ideal_length', 150),
                        is_active=True,
                        usage_count=0
                    )
                    db.add(question)
                    questions_created += 1

                print(f"  └─ Added {len(cat_data['questions'])} questions")

        # Commit all changes
        await db.commit()

        print("=" * 70)
        print(f"✅ Seeding completed successfully!")
        print(f"   Categories created: {categories_created}")
        print(f"   Questions created: {questions_created}")
        print("=" * 70)

        # Show summary
        result = await db.execute(select(JobCategory))
        all_categories = result.scalars().all()

        print("\n📊 Current Categories in Database:")
        print("-" * 70)
        for cat in all_categories:
            print(f"   • {cat.name:<30} ({cat.industry:<20}) - {cat.typical_questions_count} questions")
        print("-" * 70)


async def clear_categories():
    """Clear all categories and questions (use with caution!)"""
    async with AsyncSessionLocal() as db:
        print("⚠️  WARNING: This will delete ALL categories and questions!")
        confirm = input("Type 'DELETE' to confirm: ")

        if confirm != "DELETE":
            print("❌ Cancelled")
            return

        # Delete all questions
        from sqlalchemy import delete
        await db.execute(delete(QuestionTemplate))

        # Delete all categories
        await db.execute(delete(JobCategory))

        await db.commit()
        print("✓ All categories and questions deleted")


# ==================== MAIN ====================

async def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(description="Seed job categories")
    parser.add_argument(
        '--clear',
        action='store_true',
        help='Clear all existing categories before seeding'
    )
    args = parser.parse_args()

    try:
        if args.clear:
            await clear_categories()

        await seed_categories()

    except Exception as e:
        print(f"\n❌ Seeding failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())