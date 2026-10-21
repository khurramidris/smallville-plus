from __future__ import annotations

import csv
import json
import math
import re
import xml.etree.ElementTree as ET
from collections import deque
from pathlib import Path
from typing import Protocol

from smallville.world.models import Location

DATA = Path(__file__).resolve().parents[1] / "data"


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


class MapProvider(Protocol):
    locations: dict[str, Location]

    def travel_minutes(self, start: str, end: str) -> int: ...
    def route(self, start: str, end: str) -> list[tuple[int, int]]: ...
    def view(self) -> dict: ...


class SmallvilleMap:
    """Tile-derived location graph; replace this provider without changing minds.

    A tile is modeled as one metre and movement at 10 tiles/minute, intentionally
    slow enough to expose travel conflicts in a compact research map. Capacities,
    addresses and hours are authored assumptions. No texture files are required.
    """

    def __init__(self, root: Path | None = None, extra_locations: list[Location] | None = None):
        root = root or DATA / "the_ville"
        tiled = ET.parse(root / "visuals/the_ville.tmx").getroot()
        self.width, self.height = int(tiled.attrib["width"]), int(tiled.attrib["height"])
        meta = json.loads((root / "matrix/maze_meta_info.json").read_text())
        if (self.width, self.height) != (meta["maze_width"], meta["maze_height"]):
            raise ValueError("Tiled dimensions disagree with matrix dimensions")

        def matrix(name):
            with (root / f"matrix/maze/{name}_maze.csv").open() as file:
                values = [int(v) for row in csv.reader(file) for v in row]
            if len(values) != self.width * self.height:
                raise ValueError("incorrect tile matrix size")
            return values

        self.collisions = matrix("collision")
        sectors = matrix("sector")
        # Some rooms contain isolated floor islands. Choose each location's
        # representative in the town's main walkable component, not its bedroom.
        remaining = {i for i, value in enumerate(self.collisions) if value == 0}
        components = []
        while remaining:
            queue = deque([min(remaining)])
            component = set(queue)
            remaining.difference_update(component)
            while queue:
                i = queue.popleft()
                x, y = i % self.width, i // self.width
                for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                    neighbor = ny * self.width + nx
                    if 0 <= nx < self.width and 0 <= ny < self.height and neighbor in remaining:
                        component.add(neighbor)
                        remaining.remove(neighbor)
                        queue.append(neighbor)
            components.append(component)
        # The largest component is decorative space outside the perimeter.
        # The town component is the one connecting the most named sectors.
        accessible = max(components, key=lambda c: (len({sectors[i] for i in c} - {0}), len(c)))
        self.locations: dict[str, Location] = {}
        self.sector_ids = sectors
        with (root / "matrix/special_blocks/sector_blocks.csv").open() as file:
            names = {int(row[0]): row[2].strip() for row in csv.reader(file)}
        for code, name in names.items():
            cells = [
                (i % self.width, i // self.width)
                for i, value in enumerate(sectors)
                if value == code and i in accessible
            ]
            if not cells:
                raise ValueError(f"no accessible tiles for {name}")
            cx = sum(x for x, _ in cells) / len(cells)
            cy = sum(y for _, y in cells) / len(cells)
            x, y = min(cells, key=lambda xy: (abs(xy[0] - cx) + abs(xy[1] - cy), xy))
            private = any(
                word in name.lower() for word in ("house", "apartment", "co-living", "dorm")
            )
            opens, closes = 0, 1440
            if "Cafe" in name:
                opens, closes = 480, 1200
            elif "Pub" in name:
                opens, closes = 960, 1380
            elif "Market" in name or "Store" in name:
                opens, closes = 540, 1020
            elif "College" in name and not private:
                opens, closes = 420, 1320
            identifier = slug(name)
            self.locations[identifier] = Location(
                id=identifier,
                name=name,
                address=f"{len(self.locations) + 1} Smallville Lane",
                x=x,
                y=y,
                private=private,
                capacity=8 if private else 40,
                opens=opens,
                closes=closes,
            )
        for location in extra_locations or []:
            i = location.y * self.width + location.x
            if (
                location.id in self.locations
                or not 0 <= location.x < self.width
                or not 0 <= location.y < self.height
                or i not in accessible
            ):
                raise ValueError("invalid or inaccessible map overlay location")
            self.locations[location.id] = location
        self._paths: dict[tuple[str, str], list[tuple[int, int]]] = {}

    def route(self, start: str, end: str) -> list[tuple[int, int]]:
        key = (start, end)
        if key in self._paths:
            return self._paths[key][:]
        origin, destination = self.locations[start], self.locations[end]
        source, goal = (origin.x, origin.y), (destination.x, destination.y)
        parents = {source: None}
        queue = deque([source])
        while queue:
            cell = queue.popleft()
            if cell == goal:
                break
            x, y = cell
            for nxt in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                nx, ny = nxt
                if (
                    0 <= nx < self.width
                    and 0 <= ny < self.height
                    and not self.collisions[ny * self.width + nx]
                    and nxt not in parents
                ):
                    parents[nxt] = cell
                    queue.append(nxt)
        if goal not in parents:
            raise ValueError(f"no walkable route from {start} to {end}")
        path = [goal]
        while parents[path[-1]] is not None:
            path.append(parents[path[-1]])
        path.reverse()
        self._paths[key] = path
        self._paths[(end, start)] = path[::-1]
        return path[:]

    def travel_minutes(self, start: str, end: str) -> int:
        if start == end:
            return 0
        return max(1, math.ceil((len(self.route(start, end)) - 1) / 10))

    def view(self) -> dict:
        return {
            "width": self.width,
            "height": self.height,
            "blocked": [i for i, value in enumerate(self.collisions) if value],
            "locations": [loc.model_dump(mode="json") for loc in self.locations.values()],
        }
