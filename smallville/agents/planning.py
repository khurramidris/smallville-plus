"""Bounded future-plan repair; elapsed blocks are immutable history."""

from __future__ import annotations

from pydantic import Field, model_validator

from smallville.world.models import DailyPlan, Model, PlanBlock


class PlanPatch(Model):
    day: int = Field(ge=0)
    start: int = Field(ge=0, lt=1440)
    blocks: list[PlanBlock] = Field(min_length=1, max_length=32)

    @model_validator(mode="after")
    def contiguous_future(self):
        if self.blocks[0].start != self.start or self.blocks[-1].end != 1440:
            raise ValueError("plan patch must cover its declared start through midnight")
        for previous, current in zip(self.blocks, self.blocks[1:]):
            if previous.end != current.start:
                raise ValueError("plan patch blocks must be contiguous")
        return self


def merge_future(plan: DailyPlan, patch: PlanPatch) -> DailyPlan:
    if plan.day != patch.day:
        raise ValueError("plan patch day differs from current plan")
    prefix = []
    for block in plan.blocks:
        if block.end <= patch.start:
            prefix.append(block.model_copy(deep=True))
        elif block.start < patch.start:
            prefix.append(block.model_copy(update={"end": patch.start}, deep=True))
            break
        else:
            break
    return DailyPlan(day=plan.day, blocks=[*prefix, *patch.blocks])


def appointment_constraints(context: dict) -> tuple[list[dict], list[dict]]:
    """Select chronologically feasible appointments and expose deferred conflicts."""

    minute = context["minute"]
    day_start = minute // 1440 * 1440
    candidates = sorted(
        (
            event
            for event in context["calendar"]
            if minute < event["end"] <= day_start + 1440 and event["start"] >= minute
        ),
        key=lambda event: (event["start"], event["id"]),
    )
    accepted, deferred = [], []
    for event in candidates:
        if accepted:
            previous = accepted[-1]
            travel = context["travel_between"].get(previous["location"], {}).get(event["location"])
            earliest_departure = previous["end"]
        else:
            travel = context["travel_minutes"].get(event["location"])
            earliest_departure = minute
        if travel is None or earliest_departure + travel > event["start"]:
            deferred.append(event)
            continue
        accepted.append({**event, "depart": event["start"] - travel})
    return accepted, deferred


def _is_open(hours: dict, start: int, end: int) -> bool:
    opens, closes = hours["opens"], hours["closes"]
    if opens == 0 and closes == 1440:
        return True
    if opens < closes:
        return opens <= start and end <= closes
    return start >= opens or end <= closes


def deterministic_patch(context: dict) -> PlanPatch:
    """Repair known closures and appointments without inventing resources."""

    current = DailyPlan.model_validate(context["current_plan"])
    start = context["repair_from"]
    home = context["self"]["home"]
    accepted = context.get("repair_appointments", [])
    day_start = current.day * 1440
    appointments = []
    for event in accepted:
        appointments.append(
            {
                **event,
                "depart": max(start, event["depart"] - day_start),
                "local_end": event["end"] - day_start,
            }
        )
    boundaries = {start, 1440}
    for block in current.blocks:
        if start < block.start < 1440:
            boundaries.add(block.start)
        if start < block.end < 1440:
            boundaries.add(block.end)
    for event in appointments:
        boundaries.update((event["depart"], event["local_end"]))
    points = sorted(boundaries)
    blocks = []
    for left, right in zip(points, points[1:]):
        appointment = next(
            (event for event in appointments if event["depart"] <= left < event["local_end"]),
            None,
        )
        if appointment:
            activity, location = "leisure", appointment["location"]
        else:
            original = next(block for block in current.blocks if block.start <= left < block.end)
            activity, location = original.activity, original.location
        hours = context["opening_hours"].get(location)
        if (
            location not in context["self"]["known_locations"]
            or hours is None
            or not _is_open(hours, left, right)
        ):
            activity, location = "leisure", home
        block = PlanBlock(start=left, end=right, activity=activity, location=location)
        if blocks and blocks[-1].activity == activity and blocks[-1].location == location:
            blocks[-1] = blocks[-1].model_copy(update={"end": right})
        else:
            blocks.append(block)
    return PlanPatch(day=current.day, start=start, blocks=blocks)
