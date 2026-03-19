"""Test script for load_logs function."""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel, select

from app.etl import load_items, load_logs
from app.models.item import ItemRecord
from app.models.learner import Learner
from app.models.interaction import InteractionLog
from app.settings import settings


def get_database_url() -> str:
    return (
        f"postgresql+asyncpg://{settings.db_user}:{settings.db_password}"
        f"@{settings.db_host}:{settings.db_port}/{settings.db_name}"
    )


async def main():
    # Use PostgreSQL from Docker
    engine = create_async_engine(get_database_url(), echo=False)
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    
    print("Testing load_logs()...")
    
    # Sample data from API
    items = [
        {"lab": "lab-01", "task": None, "title": "Introduction to Python", "type": "lab"},
        {"lab": "lab-01", "task": "task-01", "title": "Variables and Types", "type": "task"},
    ]
    
    logs = [
        {
            "id": 1001,
            "student_id": "student-001",
            "group": "IKB-201",
            "lab": "lab-01",
            "task": "task-01",
            "score": 85.5,
            "passed": 3,
            "total": 4,
            "submitted_at": "2025-03-15T10:30:00Z",
        },
        {
            "id": 1002,
            "student_id": "student-002",
            "group": "IKB-202",
            "lab": "lab-01",
            "task": None,
            "score": 100.0,
            "passed": 5,
            "total": 5,
            "submitted_at": "2025-03-16T14:00:00Z",
        },
        {
            "id": 1003,
            "student_id": "student-001",
            "group": "IKB-201",
            "lab": "lab-01",
            "task": "task-01",
            "score": 95.0,
            "passed": 4,
            "total": 4,
            "submitted_at": "2025-03-17T09:00:00Z",
        },
    ]
    
    async with AsyncSession(engine) as session:
        # Step 1: Load items first
        print("\n1. Loading items...")
        items_count = await load_items(items, session)
        print(f"   ✓ Создано {items_count} items")
        
        # Step 2: Load logs
        print("\n2. Loading logs...")
        logs_count = await load_logs(logs, items, session)
        print(f"   ✓ Создано {logs_count} взаимодействий")
        
        # Step 3: Verify learners
        print("\n3. Checking learners...")
        stmt = select(Learner)
        result = await session.exec(stmt)
        learners = result.all()
        print(f"   Всего студентов: {len(learners)}")
        for l in learners:
            print(f"   - ID={l.id}, external_id={l.external_id}, group={l.student_group}")
        
        # Step 4: Verify interaction logs
        print("\n4. Checking interaction logs...")
        stmt = select(InteractionLog).order_by(InteractionLog.created_at)
        result = await session.exec(stmt)
        interactions = result.all()
        print(f"   Всего записей: {len(interactions)}")
        for i in interactions:
            print(f"   - ID={i.id}, learner_id={i.learner_id}, item_id={i.item_id}, "
                  f"score={i.score}, passed={i.checks_passed}/{i.checks_total}")
        
        # Step 5: Idempotency test
        print("\n5. Testing idempotency (loading same logs again)...")
        logs_count2 = await load_logs(logs, items, session)
        print(f"   ✓ Создано {logs_count2} записей (ожидалось 0)")
        
        if logs_count2 == 0:
            print("   ✓ Idempotency check passed!")
        else:
            print("   ✗ Idempotency check failed!")


if __name__ == "__main__":
    asyncio.run(main())
