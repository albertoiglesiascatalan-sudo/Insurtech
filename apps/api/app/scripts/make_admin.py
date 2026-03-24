"""Promote a user to admin role."""
import asyncio
import argparse
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.user import User


async def make_admin(email: str):
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if not user:
            print(f"User {email} not found. Register first at http://localhost:3000/login")
            return
        user.is_admin = True
        await db.commit()
        print(f"✓ {email} is now an admin. Go to http://localhost:3000/admin")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", required=True)
    args = parser.parse_args()
    asyncio.run(make_admin(args.email))
