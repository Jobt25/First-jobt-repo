"""
scripts/create_admin.py

Create a new admin user from the command line.

Usage:
    python scripts/create_admin.py --email admin@example.com --password SecretPass123! --name "Super Admin"

"""

import asyncio
import sys
import argparse
from pathlib import Path
from uuid import uuid4

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.core.security import get_password_hash
from sqlalchemy import select

async def create_admin(email: str, password: str, name: str):
    """Create a new admin user"""
    async with AsyncSessionLocal() as db:
        print("=" * 60)
        print("🛡️  Creating Admin User")
        print("=" * 60)

        # Check if user exists
        result = await db.execute(select(User).where(User.email == email))
        existing_user = result.scalar_one_or_none()

        if existing_user:
            print(f"❌ User with email '{email}' already exists.")
            return

        # Create admin user
        admin_user = User(
            id=uuid4(),
            email=email,
            hashed_password=get_password_hash(password),
            full_name=name,
            role="admin",  # This grants admin privileges
            is_active=True
        )

        db.add(admin_user)
        await db.commit()

        print(f"✅ Admin created successfully!")
        print(f"   Email: {email}")
        print(f"   Name:  {name}")
        print(f"   Role:  admin")
        print("=" * 60)

async def main():
    parser = argparse.ArgumentParser(description="Create a new admin user")
    parser.add_argument("--email", required=True, help="Admin email address")
    parser.add_argument("--password", required=True, help="Admin password")
    parser.add_argument("--name", default="Admin User", help="Admin full name")

    args = parser.parse_args()

    try:
        await create_admin(args.email, args.password, args.name)
    except Exception as e:
        print(f"❌ Error creating admin: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
