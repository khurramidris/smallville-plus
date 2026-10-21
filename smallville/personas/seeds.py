import csv
import hashlib
import json
import re

from smallville.agents.memory import remember
from smallville.world.maps import DATA, MapProvider, slug
from smallville.world.models import Agent, Persona

ALIASES = {"Abigail Chan": "Abigail Chen", "Haily Johnson": "Hailey Johnson"}
STYLES = (
    "brief and blunt",
    "warm but impatient",
    "dry and understated",
    "curious and informal",
    "careful and reserved",
    "animated and opinionated",
)


def first_person(text: str, name: str) -> str:
    text = text.replace(name + " is ", "I am ").replace(name + " has ", "I have ")
    text = text.replace(name + "'s", "my").replace(name, "I")
    text = re.sub(r"\b[Yy]ou are\b", "I am", text)
    text = re.sub(r"\b[Yy]our\b", "my", text)
    return re.sub(r"\b[Yy]ou\b", "I", text)


def load_agents(town: MapProvider, seed: int = 42) -> list[Agent]:
    sources = [json.loads(p.read_text()) for p in sorted((DATA / "seeds").glob("*.json"))]
    with (DATA / "the_ville/agent_history_init_n25.csv").open() as file:
        whispers = {r["Name"]: r["Whisper"] for r in csv.DictReader(file)}
    agents = []
    public = [loc.id for loc in town.locations.values() if not loc.private]
    for index, source in enumerate(sources):
        name = source["name"]
        home = slug(source["living_area"].split(":")[1])
        if home not in town.locations:
            raise ValueError(f"unknown seed home {home}")
        learned = source["learned"]
        work = home
        if name == "Isabella Rodriguez":
            work = "hobbs_cafe"
        elif name == "Arthur Burton":
            work = "the_rose_and_crown_pub"
        elif name in ("John Lin", "Tom Moreno"):
            work = "the_willows_market_and_pharmacy"
        elif name == "Carmen Ortiz":
            work = "harvey_oak_supply_store"
        elif "college" in learned.lower() or name in ("Mei Lin", "Giorgio Rossi"):
            work = "oak_hill_college"
        elif name == "Sam Moore":
            work = "johnson_park"
        number = int(hashlib.sha256(f"{seed}:{name}".encode()).hexdigest()[:8], 16)
        persona = Persona(
            name=name,
            age=source["age"],
            home=home,
            workplace=work,
            description=first_person(learned, name),
            traits=source["innate"],
            lifestyle=first_person(source["lifestyle"], name),
            speech_style=STYLES[index % len(STYLES)],
            tier="deep" if index % 5 == 0 else "standard",
            temperature=round(0.4 + (number % 80) / 100, 2),
            sociability=round(0.15 + (number % 80) / 100, 2),
            opinion=round((number % 201 - 100) / 100, 2),
            known_locations=sorted(set([home, work, *public])),
        )
        agent = Agent(id=slug(name), persona=persona, location=home)
        text = whispers.get(name, "")
        for old, new in ALIASES.items():
            text = text.replace(old, new)
        # Original household/relationship seeds, no town-wide contact directory.
        for other in sources:
            if other["name"] != name and other["name"] in text:
                identifier = slug(other["name"])
                agent.contacts.append(identifier)
                agent.relationships[identifier] = (
                    -0.2 if (other["name"] == "Sam Moore" and name == "Tom Moreno") else 0.25
                )
        for description in (source["currently"], source["daily_plan_req"], text):
            if description:
                remember(agent, 0, first_person(description, name), "original_seed", 0.9, "seed")
        agent.needs.social = 45 + number % 40
        agent.needs.fun = 45 + number % 35
        agents.append(agent)
    if len(agents) != 25:
        raise ValueError("Phase 1 requires exactly the original 25 residents")
    return agents
