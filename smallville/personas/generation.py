"""Seed-anchored life histories; generated additions remain explicitly fictional."""

from __future__ import annotations

import hashlib
import json

from smallville.personas.seeds import STYLES, load_agents
from smallville.world.maps import DATA, MapProvider, slug
from smallville.world.models import Agent, Location, Persona

GSS_REVISION = "96854071ef4c2d79c93144c973c7820722d52bab"


def source_population(
    town: MapProvider, count: int, seed: int
) -> tuple[list[Agent], list[Location]]:
    if not 25 <= count <= 100:
        raise ValueError("Phase 2 supports 25 through 100 residents")
    agents = load_agents(town, seed)
    for agent in agents:
        agent.persona = Persona.model_validate(
            agent.persona.model_dump()
            | {
                "facts": {
                    "name": agent.persona.name,
                    "age": agent.persona.age,
                    "home": agent.persona.home,
                    "workplace": agent.persona.workplace,
                    "home_address": town.locations[agent.persona.home].address,
                    "current_goal": agent.memories[0].text
                    if agent.memories
                    else "Keep my own routines",
                },
                "provenance": {"source": "generative_agents", "biography": "fictional expansion"},
            }
        )
    records = sorted((DATA / "gss").glob("*.json"))
    if len(records) < count - 25:
        raise ValueError("not enough licensed GSS demographic seed records")
    locations = []
    path = town.route("johnson_park", "hobbs_cafe")
    entrances = [path[max(0, len(path) * n // 4)] for n in (1, 2, 3)]
    buildings = ("North Terrace", "East Court", "South Mews")
    for index, file in enumerate(records[: count - 25]):
        record = json.loads(file.read_text())
        name = f"{record['first_name']} {record['last_name']}"
        identifier = slug(name) + "_" + file.stem[:6]
        building = index % 3
        unit = index // 3 + 1
        home = f"{slug(buildings[building])}_{unit:03d}"
        x, y = entrances[building]
        locations.append(
            Location(
                id=home,
                name=f"{buildings[building]} · Apt {unit}",
                address=f"{building + 1} Terrace Lane, Apt {unit}",
                x=x,
                y=y,
                private=True,
                capacity=4,
            )
        )
        work_status = record["work_status"]
        workplaces = [
            "oak_hill_college",
            "the_willows_market_and_pharmacy",
            "harvey_oak_supply_store",
            home,
        ]
        workplace = workplaces[index % len(workplaces)]
        if work_status.lower() in (
            "retired",
            "unemployed, laid off, looking for work",
            "keeping house",
        ):
            workplace = home
        if "school" in work_status.lower():
            workplace = "oak_hill_college"
        facts = {
            k: v
            for k, v in record.items()
            if k not in ("first_name", "last_name", "street_address", "city", "state")
        }
        facts.update(
            name=name,
            age=record["age"],
            home=home,
            workplace=workplace,
            previous_city=record["city"],
            previous_state=record["state"],
            home_address=locations[-1].address,
        )
        number = int(hashlib.sha256(f"{seed}:{file.stem}".encode()).hexdigest()[:8], 16)
        persona = Persona(
            name=name,
            age=record["age"],
            home=home,
            workplace=workplace,
            description=f"I moved to Smallville from {record['city']}. My work status is {work_status}.",
            traits=("reserved, methodical" if number % 2 else "outspoken, curious"),
            lifestyle="I balance my own routines, responsibilities and private time.",
            speech_style=STYLES[index % len(STYLES)],
            tier="deep" if index % 5 == 0 else "standard",
            temperature=0.4 + number % 80 / 100,
            sociability=0.15 + number % 80 / 100,
            opinion=(number % 201 - 100) / 100,
            known_locations=sorted(
                {home, workplace, *[loc.id for loc in town.locations.values() if not loc.private]}
            ),
            facts=facts,
            provenance={
                "source": "genagents_public_gss_demographics",
                "source_id": file.stem,
                "revision": GSS_REVISION,
                "license": "MIT",
                "biography": "fictional expansion; not a real interview",
            },
        )
        agents.append(Agent(id=identifier, persona=persona, location=home))
    return agents, locations


def mock_life_history(context: dict, seed: int) -> dict:
    facts = context["facts"]
    age, name = int(facts["age"]), facts["name"]
    number = int(hashlib.sha256(f"{seed}:{context['subject']}".encode()).hexdigest()[:8], 16)
    interests = ("gardening", "drawing", "cooking", "reading", "walking", "music", "photography")
    hobby = interests[number % len(interests)]
    second = interests[(number + 3) % len(interests)]
    origin = facts.get("previous_city", "the area around Smallville")
    education = facts.get("highest_degree_received", "my own training and experience")
    work_status = facts.get("work_status", "the work and routines I already remember")
    address = facts.get("home_address", facts["home"])
    values = (
        "privacy",
        "curiosity",
        "independence",
        "fairness",
        "stability",
        "craftsmanship",
        "family",
        "community",
    )
    return {
        "narrative": (
            f"My name is {name}. I am {age} years old. "
            f"I grew up with memories of {origin}, and learned to make my own decisions. "
            f"My education includes {education}. My present work status is {work_status}. "
            "As a child I learned the difference between things I could choose and obligations "
            "I had to meet. In my teens I began forming interests outside my immediate family. "
            "Early adulthood brought new responsibilities and some changes of direction; I "
            "remember needing to balance practical demands with the things I wanted for myself. "
            f"I live at {address} and organize my responsibilities around {facts['workplace']}. "
            f"I make time for {hobby} and {second}, though my responsibilities sometimes get in the way. "
            "I do not agree with everyone I know. Some relationships take effort, and I keep parts "
            "of my life private. My friendships have changed as my routines changed, and I do "
            "not feel equally close to everyone in my address book. I sometimes decline plans "
            "because I need to finish something or have a quiet evening. I want steadier routines "
            "without giving up my own interests, and I try to notice when my plans are unrealistic."
        ),
        "events": [
            {
                "age": min(age, 4),
                "description": "I remember learning routines and responsibilities while growing up.",
            },
            {
                "age": min(age, 10),
                "description": "I began making room for my own interests outside my daily obligations.",
            },
            {
                "age": min(age, 16),
                "description": "I was learning how family circumstances and other people's expectations affected my choices.",
            },
            {
                "age": min(age, 18),
                "description": "I began making more independent choices about learning and daily life.",
            },
            {
                "age": (age + min(age, 18)) // 2,
                "description": "I revised some plans as practical responsibilities and relationships changed.",
            },
            {
                "age": age,
                "description": f"I now organize my daily life around my home at {facts['home']}.",
            },
        ],
        "interests": [hobby, second],
        "values": [
            values[number % len(values)],
            values[(number + 3) % len(values)],
            "keeping commitments",
        ],
        "goals": [
            facts.get("current_goal", "Settle into my own routines in Smallville"),
            f"Make regular time for {hobby}",
            "Balance responsibilities with personal relationships",
        ],
    }


def biography_is_compatible(raw: dict, persona: Persona):
    import re

    narrative = raw.get("narrative", "")
    if not isinstance(narrative, str) or not narrative.startswith(
        "My name is " + persona.name + "."
    ):
        raise ValueError("biography must begin with the person's own name")
    ages = re.findall(r"\bI am (\d+) years old\b", narrative)
    if ages != [str(persona.age)]:
        raise ValueError("biography must state the locked current age exactly once")
    if re.search(
        r"\b(?:I am|I'm) (?:an? )?(?:AI|assistant|simulated|simulation)\b", narrative, re.I
    ):
        raise ValueError("biography must describe an ordinary person's life")
