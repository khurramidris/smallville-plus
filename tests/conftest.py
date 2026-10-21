import pytest

from smallville.config import Config
from smallville.engine.simulation import bootstrap
from smallville.llm.gateway import Gateway
from smallville.llm.mock import MockLLM
from smallville.world.maps import SmallvilleMap
from smallville.world.models import change
from smallville.world.store import WorldState


@pytest.fixture
def town():
    return SmallvilleMap()


@pytest.fixture
def setup_world(tmp_path, town):
    world = WorldState(tmp_path / "run")
    config = Config()
    bootstrap(world, town, config)
    agents = world.agents()
    for agent in agents:
        agent.pending = None
        agent.busy_until = 0
        agent.activity = "wait"
    world.log.append(0, "test_ready", changes=[change("agents", a.id, a) for a in agents])
    gateway = Gateway(tmp_path / "gateway", config, MockLLM())
    yield world, config, gateway
    gateway.close()
    world.close()
