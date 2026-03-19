"""Test script for sync function (full ETL pipeline)."""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel, select

from app.etl import sync
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
    
    print("Testing sync() — Full ETL Pipeline\n")
    print("=" * 50)
    
    async with AsyncSession(engine) as session:
        # Run sync
        print("\nЗапуск синхронизации...")
        try:
            result = await sync(session)
            print(f"\n✓ Синхронизация завершена!")
            print(f"  - Новые записи: {result['new_records']}")
            print(f"  - Всего записей: {result['total_records']}")
        except Exception as e:
            print(f"\n✗ Ошибка синхронизации: {e}")
            print(f"  (Возможно, неверные credentials для API)")
            return
        
        # Verify data
        print("\n" + "=" * 50)
        print("Проверка данных в БД:")
        
        # Count items
        from app.models.item import ItemRecord
        stmt = select(ItemRecord)
        result = await session.exec(stmt)
        items = result.all()
        print(f"  - Items (labs + tasks): {len(items)}")
        
        # Count learners
        from app.models.learner import Learner
        stmt = select(Learner)
        result = await session.exec(stmt)
        learners = result.all()
        print(f"  - Learners: {len(learners)}")
        
        # Count interactions
        stmt = select(InteractionLog)
        result = await session.exec(stmt)
        interactions = result.all()
        print(f"  - Interactions: {len(interactions)}")
        
        # Show sample data
        if interactions:
            print("\n" + "=" * 50)
            print("Последние 3 взаимодействия:")
            stmt = select(InteractionLog).order_by(InteractionLog.created_at.desc()).limit(3)
            result = await session.exec(stmt)
            for i, interaction in enumerate(result.all(), 1):
                print(f"  {i}. learner_id={interaction.learner_id}, "
                      f"item_id={interaction.item_id}, "
                      f"score={interaction.score}")


if __name__ == "__main__":
    asyncio.run(main())
