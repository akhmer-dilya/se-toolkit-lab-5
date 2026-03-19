"""Test script for load_items function."""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel

from app.etl import load_items
from app.models.item import ItemRecord
from app.settings import settings


def get_database_url() -> str:
    return (
        f"postgresql+asyncpg://{settings.db_user}:{settings.db_password}"
        f"@{settings.db_host}:{settings.db_port}/{settings.db_name}"
    )


async def main():
    # Use PostgreSQL from Docker
    engine = create_async_engine(get_database_url(), echo=True)
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    
    print("Testing load_items()...")
    
    # Sample data from API
    items = [
        {"lab": "lab-01", "task": None, "title": "Introduction to Python", "type": "lab"},
        {"lab": "lab-01", "task": "task-01", "title": "Variables and Types", "type": "task"},
        {"lab": "lab-01", "task": "task-02", "title": "Control Flow", "type": "task"},
        {"lab": "lab-02", "task": None, "title": "Data Structures", "type": "lab"},
        {"lab": "lab-02", "task": "task-01", "title": "Lists and Tuples", "type": "task"},
    ]
    
    async with AsyncSession(engine) as session:
        # Test 1: Load items
        print("\n1. Loading items...")
        count = await load_items(items, session)
        print(f"   ✓ Создано {count} новых записей")
        
        # Test 2: Verify items in database
        print("\n2. Checking database contents...")
        from sqlmodel import select
        
        stmt = select(ItemRecord).order_by(ItemRecord.id)
        result = await session.exec(stmt)
        records = result.all()
        
        print(f"   Всего записей в БД: {len(records)}")
        for rec in records:
            print(f"   - ID={rec.id}, type={rec.type}, title={rec.title}, parent_id={rec.parent_id}")
        
        # Test 3: Idempotency - load again, should create 0 items
        print("\n3. Testing idempotency (loading same items again)...")
        count2 = await load_items(items, session)
        print(f"   ✓ Создано {count2} новых записей (ожидалось 0)")
        
        if count2 == 0:
            print("   ✓ Idempotency check passed!")
        else:
            print("   ✗ Idempotency check failed!")


if __name__ == "__main__":
    asyncio.run(main())
