from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from layer5_ground_truth.services.freshness_monitor import (
    FRESHNESS_ADVISORY_LOCK_KEY,
    FreshnessMonitor,
    run_freshness_check_with_leader_lock,
)


@pytest.mark.asyncio
async def test_leader_lock_skips_when_lock_not_acquired(db: AsyncSession) -> None:
    monitor = FreshnessMonitor()
    monitor.check_and_mark_stale = AsyncMock(return_value={"checked": 1, "marked_stale": 1})

    db.bind.dialect.name = "postgresql"
    db.execute = AsyncMock()
    db.execute.return_value.scalar.return_value = False

    result = await run_freshness_check_with_leader_lock(db, monitor)

    assert result is None
    monitor.check_and_mark_stale.assert_not_awaited()
    db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_leader_lock_runs_and_unlocks(db: AsyncSession) -> None:
    monitor = FreshnessMonitor()
    expected = {"checked": 2, "marked_stale": 2}
    monitor.check_and_mark_stale = AsyncMock(return_value=expected)

    db.bind.dialect.name = "postgresql"
    first_result = AsyncMock()
    first_result.scalar.return_value = True
    db.execute = AsyncMock(side_effect=[first_result, AsyncMock()])

    result = await run_freshness_check_with_leader_lock(db, monitor)

    assert result == expected
    monitor.check_and_mark_stale.assert_awaited_once()
    assert db.execute.await_count == 2

    first_query = str(db.execute.await_args_list[0].args[0])
    second_query = str(db.execute.await_args_list[1].args[0])
    assert "pg_try_advisory_lock" in first_query
    assert str(FRESHNESS_ADVISORY_LOCK_KEY) in first_query
    assert "pg_advisory_unlock" in second_query


@pytest.mark.asyncio
async def test_non_postgres_runs_without_lock(db: AsyncSession) -> None:
    monitor = FreshnessMonitor()
    expected = {"checked": 3, "marked_stale": 1}
    monitor.check_and_mark_stale = AsyncMock(return_value=expected)

    db.bind.dialect.name = "sqlite"
    db.execute = AsyncMock()

    result = await run_freshness_check_with_leader_lock(db, monitor)

    assert result == expected
    monitor.check_and_mark_stale.assert_awaited_once()
    db.execute.assert_not_called()
