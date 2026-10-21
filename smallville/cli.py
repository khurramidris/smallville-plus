import argparse
import asyncio
import json
import os
import sys
import time
from pathlib import Path

from smallville.agents.mind import Mind
from smallville.config import Config
from smallville.engine.simulation import Simulation
from smallville.eval.interviews import interview
from smallville.eval.metrics import evaluate
from smallville.llm.gateway import BudgetExceeded, Gateway, LiteLLMBackend, ModelFailure
from smallville.llm.mock import MockLLM
from smallville.world.maps import SmallvilleMap
from smallville.world.store import WorldState, replay


def write_report(directory: Path, report: dict):
    (directory / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    r, p, cost = report["relationships"], report["party"], report["cost"]
    text = (
        "# Smallville+ Phase 1 run\n\n"
        f"{report['interpretation']}\n\n"
        f"- Status: {report['run']['status']}; {report['agents']} residents; "
        f"{report['run']['completed_minutes'] / 1440:g} simulated days.\n"
        f"- Cost: ${cost['usd']}; ${cost['usd_per_agent_per_simulated_day']} per resident/day.\n"
        f"- Model requests: {cost['calls']}; cache hits: {cost['cache_hits']}.\n\n"
        "| Measurement | This run | Paper |\n| --- | ---: | ---: |\n"
        f"| Sam awareness | {report['diffusion']['sam']['retained_final']}/25 | 8/25 |\n"
        f"| Party awareness | {report['diffusion']['party']['retained_final']}/25 | 13/25 |\n"
        f"| Invited guests attending | {p['invited_attending_guests']}/{p['invited_guests']} | 5/12 |\n"
        f"| Mutual-knowledge density | {r['initial_density']:.3f} → {r['final_density']:.3f} | 0.167 → 0.740 |\n\n"
        "[Paper §7.1](https://arxiv.org/html/2304.03442v2#S7.SS1). "
        "The starting relationship graph and communication channel differ from the paper. "
        "These descriptive results do not establish an improvement in realism.\n\n"
        "Full time-use, variance, error and accounting details are in `report.json`. "
        "Human believability scores remain uncollected.\n"
    )
    (directory / "report.md").write_text(text)


async def run_command(args):
    config = Config.from_env(args.backend, args.seed, args.allow_paid, args.replay_only)
    start = time.perf_counter()
    sim = Simulation(args.out, config, cache_path=args.cache)
    try:
        result = await sim.run(args.days)
        report = evaluate(sim.world)
        report["wall_seconds"] = round(time.perf_counter() - start, 3)
        write_report(args.out, report)
        print(
            json.dumps(
                result
                | {"report": str(args.out / "report.json"), "wall_seconds": report["wall_seconds"]},
                indent=2,
            )
        )
        return 0 if result["status"] == "completed" else 2
    finally:
        sim.close()


async def interview_command(args):
    world = WorldState(args.run)
    minute = world.get("metadata", "run")["completed_minutes"]
    config = Config.from_env(args.backend, args.seed, args.allow_paid)
    active = {"id": None}
    backend = MockLLM() if args.backend == "mock" else LiteLLMBackend(config.timeout_seconds)
    gateway = Gateway(
        args.run,
        config,
        backend,
        on_call=lambda record: world.log.append(minute, "llm_call", active["id"], record),
    )
    try:
        mind = Mind(world, SmallvilleMap(), gateway, config)
        identifiers = [a.id for a in world.agents()] if args.agent == "all" else [args.agent]
        answers = {}
        for identifier in identifiers:
            active["id"] = identifier
            answers[identifier] = await interview(mind, identifier, minute)
        (args.run / "interviews.json").write_text(json.dumps(answers, indent=2) + "\n")
        write_report(args.run, evaluate(world))
        print(
            json.dumps(
                {
                    "residents_interviewed": len(answers),
                    "path": str(args.run / "interviews.json"),
                    "cost": gateway.summary(),
                },
                indent=2,
            )
        )
    finally:
        gateway.close()
        world.close()
    return 0


def parser():
    p = argparse.ArgumentParser(description="Smallville+ Phase 1 research simulation")
    sub = p.add_subparsers(dest="command", required=True)
    for name in ("run", "benchmark"):
        command = sub.add_parser(name)
        if name == "benchmark":
            command.add_argument("name", choices=["valentine"])
        command.add_argument("--out", type=Path, required=True)
        command.add_argument("--days", type=float, default=2)
        command.add_argument("--backend", choices=["mock", "litellm"], default="mock")
        command.add_argument("--seed", type=int, default=42)
        command.add_argument("--cache", type=Path)
        command.add_argument("--replay-only", action="store_true")
        command.add_argument("--allow-paid", action="store_true")
    command = sub.add_parser("replay")
    command.add_argument("--source", type=Path, required=True)
    command.add_argument("--out", type=Path, required=True)
    command = sub.add_parser("evaluate")
    command.add_argument("--run", type=Path, required=True)
    command = sub.add_parser("interview")
    command.add_argument("--run", type=Path, required=True)
    command.add_argument("--agent", default="all")
    command.add_argument("--backend", choices=["mock", "litellm"], default="mock")
    command.add_argument("--seed", type=int, default=42)
    command.add_argument("--allow-paid", action="store_true")
    command = sub.add_parser("serve")
    command.add_argument("--run", type=Path, required=True)
    command.add_argument("--host", default="127.0.0.1")
    command.add_argument("--port", type=int, default=8000)
    sub.add_parser("preflight")
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        if args.command in ("run", "benchmark"):
            return asyncio.run(run_command(args))
        if args.command == "replay":
            world = replay(args.source, args.out)
            try:
                print(
                    json.dumps(
                        {"status": "replayed", "run": world.get("metadata", "run")}, indent=2
                    )
                )
            finally:
                world.close()
        elif args.command == "evaluate":
            world = WorldState(args.run)
            try:
                report = evaluate(world)
                write_report(args.run, report)
                print(str(args.run / "report.json"))
            finally:
                world.close()
        elif args.command == "interview":
            return asyncio.run(interview_command(args))
        elif args.command == "serve":
            import uvicorn

            from smallville.viewer.app import create_app

            uvicorn.run(create_app(args.run), host=args.host, port=args.port)
        elif args.command == "preflight":
            names = (
                "SIM_MODEL_DEEP",
                "SIM_MODEL_FAST",
                "SIM_MODEL_GM",
                "SIM_EMBED_MODEL",
                "SIM_MAX_USD",
                "SIM_MODEL_PRICES",
            )
            result = {
                "configured": {name: bool(os.getenv(name)) for name in names},
                "credential_presence_only": {
                    name: bool(os.getenv(name))
                    for name in (
                        "OPENAI_API_KEY",
                        "ANTHROPIC_API_KEY",
                        "GEMINI_API_KEY",
                        "AZURE_API_KEY",
                    )
                },
                "network_calls": 0,
                "paid_calls": 0,
                "note": "Readiness only; does not authenticate or authorize spending.",
            }
            try:
                Config.from_env("litellm", allow_paid=True)
                result["configuration_valid"] = True
            except ValueError:
                result["configuration_valid"] = False
            print(json.dumps(result, indent=2))
        return 0
    except (ValueError, KeyError, BudgetExceeded, ModelFailure) as error:
        print(f"Smallville stopped: {type(error).__name__}: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
