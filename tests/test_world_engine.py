import sqlite3

import pytest

from smallville.engine.clock import SimClock
from smallville.engine.scheduler import EventBus, Scheduler
from smallville.world.maps import SmallvilleMap
from smallville.world.models import change
from smallville.world.store import WorldState, replay


def test_map_routes_opening_and_swappable_contract():
    town = SmallvilleMap()
    assert len(town.locations) == 19
    assert town.locations["hobbs_cafe"].is_open(480)
    assert not town.locations["hobbs_cafe"].is_open(1200)
    for location in town.locations:
        path = town.route(location, "hobbs_cafe")
        assert all(not town.collisions[y * town.width + x] for x, y in path)
        assert town.travel_minutes(location, "hobbs_cafe") >= (location != "hobbs_cafe")
    assert len(town.view()["locations"]) == 19


def test_transaction_replay_immutability_and_recovery(tmp_path):
    world = WorldState(tmp_path / "a")
    assert world.db.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
    world.log.append(0, "created", changes=[change("objects", "ball", {"id": "ball"})])
    world.log.append(2, "moved", changes=[change("objects", "ball", {"id": "ball", "x": 4})])
    with pytest.raises(sqlite3.IntegrityError):
        world.db.execute("UPDATE events SET kind='forged'")
    world.db.rollback()
    with pytest.raises(sqlite3.IntegrityError):
        world.db.execute("DELETE FROM events")
    world.db.rollback()
    with pytest.raises(ValueError):
        world.log.append(1, "past")
    other = replay(world.log.path, tmp_path / "b")
    assert other.snapshot() == world.snapshot()
    assert other.log.path.read_bytes() == world.log.path.read_bytes()
    other.close()
    lines = world.log.path.read_bytes().splitlines(keepends=True)
    world.log.path.write_bytes(lines[0] + lines[1][:20])
    world.close()
    reopened = WorldState(tmp_path / "a")
    assert reopened.log.path.read_bytes() == b"".join(lines)
    reopened.close()


def test_tampered_export_and_replay_fail(tmp_path):
    world = WorldState(tmp_path / "a")
    world.log.append(0, "created")
    path = world.log.path
    world.close()
    path.write_text(path.read_text().replace("created", "changed"))
    with pytest.raises(ValueError, match="diverges"):
        WorldState(tmp_path / "a")
    with pytest.raises(ValueError, match="integrity"):
        replay(path, tmp_path / "b")


def test_clock_and_stable_condition_scheduling():
    clock = SimClock()
    clock.advance(90)
    assert clock.now.hour == 1 and clock.now.minute == 30
    with pytest.raises(ValueError):
        clock.advance(0)
    scheduler = Scheduler()
    scheduler.schedule(90, "decide", "a")
    scheduler.schedule(90, "complete", "b", priority=0)
    scheduler.when("wake", lambda: clock.minute == 90, "wake", "c")
    scheduler.check_conditions(90)
    scheduler.check_conditions(90)
    assert [scheduler.pop().kind for _ in range(3)] == ["complete", "decide", "wake"]
    assert not scheduler.queue


async def test_event_bus(tmp_path):
    world = WorldState(tmp_path)
    event = world.log.append(0, "test")
    bus, seen = EventBus(), []

    async def receive(e):
        seen.append(e.seq)

    bus.subscribe("test", receive)
    await bus.publish(event)
    assert seen == [1]
    world.close()
