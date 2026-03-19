"""Test script for fetch_logs function."""

import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.etl import fetch_logs


async def main():
    print("Testing fetch_logs()...")
    
    # Test 1: Fetch all logs (since=None)
    print("\n1. Fetch all logs (since=None):")
    try:
        logs = await fetch_logs(since=None)
        print(f"   ✓ Получено {len(logs)} логов")
        if logs:
            print(f"   Первый лог: {logs[0]}")
    except Exception as e:
        print(f"   ✗ Ошибка: {e}")
    
    # Test 2: Fetch logs since a specific timestamp
    print("\n2. Fetch logs since 2025-01-01:")
    try:
        since = datetime(2025, 1, 1, tzinfo=timezone.utc)
        logs = await fetch_logs(since=since)
        print(f"   ✓ Получено {len(logs)} логов")
        if logs:
            print(f"   Первый лог: {logs[0]}")
    except Exception as e:
        print(f"   ✗ Ошибка: {e}")


if __name__ == "__main__":
    asyncio.run(main())
