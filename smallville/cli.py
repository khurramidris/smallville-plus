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
from smallville.eval.datasets import gss_dataset, twin_dataset
from smallville.eval.fidelity import FidelityDataset, run_fidelity
from smallville.eval.interviews import interview
from smallville.eval.metrics import evaluate
from smallville.eval.surveys import SurveyRunner
from smallville.llm.gateway import BudgetExceeded, Gateway, LiteLLMBackend, ModelFailure
from smallville.llm.mock import MockLLM
from smallville.personas.pipeline import PersonaPipeline
from smallville.personas.population import Population
from smallville.world.maps import DATA, SmallvilleMap
from smallville.world.store import WorldState, replay


def write_report(directory: Path, report: dict):
    (directory / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    r, p, cost = report["relationships"], report["party"], report["cost"]
    text = (
        f"# Smallville+ Phase {report['run'].get('phase', 1)} run\n\n"
        f"{report['interpretation']}\n\n"
        f"- Status: {report['run']['status']}; {report['agents']} residents; "
        f"{report['run']['completed_minutes'] / 1440:g} simulated days.\n"
        f"- Cost: ${cost['usd']}; ${cost['usd_per_agent_per_simulated_day']} per resident/day.\n"
        f"- Model requests: {cost['calls']}; cache hits: {cost['cache_hits']}.\n\n"
        "| Measurement | This run | Paper |\n| --- | ---: | ---: |\n"
        f"| Sam awareness | {report['diffusion']['sam']['retained_final']}/{report['agents']} | 8/25 |\n"
        f"| Party awareness | {report['diffusion']['party']['retained_final']}/{report['agents']} | 13/25 |\n"
        f"| Invited guests attending | {p['invited_attending_guests']}/{p['invited_guests']} | 5/12 |\n"
        f"| Mutual-knowledge density | {r['initial_density']:.3f} → {r['final_density']:.3f} | 0.167 → 0.740 |\n\n"
        "[Paper §7.1](https://arxiv.org/html/2304.03442v2#S7.SS1). "
        "The starting relationship graph and communication channel differ from the paper. "
        "These descriptive results do not establish an improvement in realism.\n\n"
        "Full time-use, variance, error and accounting details are in `report.json`. "
        "Human believability scores remain uncollected.\n"
    )
    (directory / "report.md").write_text(text)
    if report.get("economy", {}).get("enabled"):
        economy = report["economy"]
        audit = economy["audit"]
        with (directory / "report.md").open("a") as file:
            file.write(
                "\n## Town economy and council\n\n"
                f"Money conserved: {audit['money_conserved']}; ledger matches accounts: "
                f"{audit['ledger_matches_accounts']}; food conserved: {audit['food_conserved']}.\n\n"
                f"{economy['transfers']} transfers; rent arrears "
                f"${economy['rent_arrears_cents'] / 100:.2f}; "
                f"{economy['ballots']} ballots; {economy['news']['published']} public notices. "
                "All town amounts are fictional and separate from API USD.\n"
            )


async def run_command(args):
    population = Population.load(args.population) if args.population else None
    seed = args.seed if args.seed is not None else population.seed if population else 42
    config = Config.from_env(args.backend, seed, args.allow_paid, args.replay_only)
    config = Config.model_validate(
        config.model_dump()
        | {
            "phase": args.phase or (2 if population else 1),
            "supply_delay_day": args.supply_delay_day,
            **(
                {"decision_concurrency": 4, "routine_actions": True, "compact_context": True}
                if args.optimized
                else {}
            ),
        }
    )
    start = time.perf_counter()
    sim = Simulation(args.out, config, cache_path=args.cache, population=population)
    try:
        result = await sim.run(args.days)
        report = evaluate(sim.world)
        report["wall_seconds"] = round(time.perf_counter() - start, 3)
        report["inference_timing"] = sim.gateway.timing_summary()
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
    seed = args.seed if args.seed is not None else world.get("metadata", "config")["seed"]
    config = Config.from_env(args.backend, seed, args.allow_paid)
    config = Config.model_validate(
        config.model_dump() | {"phase": world.get("metadata", "run").get("phase", 1)}
    )
    active = {"id": None}
    backend = (
        MockLLM()
        if args.backend == "mock"
        else LiteLLMBackend(config.timeout_seconds, config.reasoning_effort)
    )
    gateway = Gateway(
        args.run,
        config,
        backend,
        on_call=lambda record: world.log.append(minute, "llm_call", active["id"], record),
    )
    try:
        original_map = SmallvilleMap()
        from smallville.world.models import Location

        extras = [
            Location.model_validate(row)
            for row in world.get("metadata", "map")["locations"]
            if row["id"] not in original_map.locations
        ]
        mind = Mind(world, SmallvilleMap(extra_locations=extras), gateway, config)
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


async def populate_command(args):
    config = Config.from_env(args.backend, args.seed, args.allow_paid, args.replay_only)
    if (args.out / "population.json").exists():
        raise ValueError("population already exists; use a fresh output directory")
    backend = (
        MockLLM()
        if args.backend == "mock"
        else LiteLLMBackend(config.timeout_seconds, config.reasoning_effort)
    )
    gateway = Gateway(args.out, config, backend, args.cache)
    pipeline = PersonaPipeline(SmallvilleMap(), gateway, config, args.max_attempts)
    start = time.perf_counter()
    try:
        population = await pipeline.build(args.residents, args.history_days)
        population.validate_map(SmallvilleMap(extra_locations=population.locations))
        population.save(args.out / "population.json")
        result = {
            "status": "validated",
            "residents": len(population.agents),
            "history_days": population.history_days,
            "messages": len(population.messages),
            "calendar_entries": len(population.calendar),
            "map_units_added": len(population.locations),
            "consistency_attempts": len(population.consistency),
            "regenerations": len(population.consistency) - len(population.agents),
            "digest": population.digest,
            "cost": gateway.summary(),
            "wall_seconds": round(time.perf_counter() - start, 3),
        }
        (args.out / "preparation.json").write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result, indent=2))
        return 0
    except (ValueError, BudgetExceeded, ModelFailure) as error:
        result = {
            "status": "incomplete",
            "error_type": type(error).__name__,
            "consistency_attempts": [a.model_dump() for a in pipeline.attempts],
            "cost": gateway.summary(),
            "population_published": False,
        }
        (args.out / "preparation.json").write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result, indent=2))
        return 2
    finally:
        gateway.close()


async def fidelity_command(args):
    config = Config.from_env(args.backend, args.seed, args.allow_paid)
    backend = (
        MockLLM()
        if args.backend == "mock"
        else LiteLLMBackend(config.timeout_seconds, config.reasoning_effort)
    )
    gateway = Gateway(args.out, config, backend)
    reports = []
    try:
        runner = SurveyRunner(gateway, config)
        datasets = []
        if args.dataset in ("twin", "all"):
            datasets.append(
                FidelityDataset.load(args.twin_data or DATA / "surveys/twin_sample.json")
            )
        if args.dataset in ("gss", "all"):
            datasets.append(gss_dataset())
        for dataset in datasets:
            reports.append(await run_fidelity(runner, dataset, args.batch_size))
        result = {
            "status": "completed",
            "backend": args.backend,
            "reports": reports,
            "cost": gateway.summary(),
        }
        (args.out / "fidelity.json").write_text(json.dumps(result, indent=2) + "\n")
        print(
            json.dumps(
                {
                    "status": result["status"],
                    "reports": [
                        {
                            "dataset": r["dataset"],
                            "subjects": r["subjects"],
                            "items": r["items"],
                            "summary": r["summary"],
                        }
                        for r in reports
                    ],
                    "cost": result["cost"],
                    "path": str(args.out / "fidelity.json"),
                },
                indent=2,
            )
        )
        return 0
    except (BudgetExceeded, ModelFailure) as error:
        (args.out / "fidelity.json").write_text(
            json.dumps(
                {
                    "status": "incomplete",
                    "error_type": type(error).__name__,
                    "completed_reports": reports,
                    "cost": gateway.summary(),
                },
                indent=2,
            )
            + "\n"
        )
        return 2
    finally:
        gateway.close()


def parser():
    p = argparse.ArgumentParser(description="Smallville+ research simulation")
    sub = p.add_subparsers(dest="command", required=True)
    for name in ("run", "benchmark"):
        command = sub.add_parser(name)
        if name == "benchmark":
            command.add_argument("name", choices=["valentine"])
        command.add_argument("--out", type=Path, required=True)
        command.add_argument("--phase", type=int, choices=[1, 2, 3])
        command.add_argument("--supply-delay-day", type=int, default=None)
        command.add_argument("--days", type=float, default=2)
        command.add_argument("--backend", choices=["mock", "litellm"], default="mock")
        command.add_argument("--seed", type=int)
        command.add_argument("--population", type=Path)
        command.add_argument("--cache", type=Path)
        command.add_argument("--replay-only", action="store_true")
        command.add_argument("--allow-paid", action="store_true")
        command.add_argument(
            "--optimized",
            action="store_true",
            help="Bounded parallel decisions, compact context and chosen routines",
        )
    command = sub.add_parser("replay")
    command.add_argument("--source", type=Path, required=True)
    command.add_argument("--out", type=Path, required=True)
    command = sub.add_parser("evaluate")
    command.add_argument("--run", type=Path, required=True)
    command = sub.add_parser("interview")
    command.add_argument("--run", type=Path, required=True)
    command.add_argument("--agent", default="all")
    command.add_argument("--backend", choices=["mock", "litellm"], default="mock")
    command.add_argument("--seed", type=int)
    command.add_argument("--allow-paid", action="store_true")
    command = sub.add_parser("serve")
    command.add_argument("--run", type=Path, required=True)
    command.add_argument("--host", default="127.0.0.1")
    command.add_argument("--port", type=int, default=8000)
    sub.add_parser("preflight")
    command = sub.add_parser("populate")
    command.add_argument("--out", type=Path, required=True)
    command.add_argument("--residents", type=int, default=100)
    command.add_argument("--history-days", type=int, default=21)
    command.add_argument("--max-attempts", type=int, default=3)
    command.add_argument("--seed", type=int, default=42)
    command.add_argument("--backend", choices=["mock", "litellm"], default="mock")
    command.add_argument("--allow-paid", action="store_true")
    command.add_argument("--replay-only", action="store_true")
    command.add_argument("--cache", type=Path)
    command = sub.add_parser("validate-population")
    command.add_argument("--population", type=Path, required=True)
    command = sub.add_parser("fidelity")
    command.add_argument("--out", type=Path, required=True)
    command.add_argument("--dataset", choices=["twin", "gss", "all"], default="all")
    command.add_argument("--twin-data", type=Path)
    command.add_argument("--batch-size", type=int, default=8)
    command.add_argument("--seed", type=int, default=42)
    command.add_argument("--backend", choices=["mock", "litellm"], default="mock")
    command.add_argument("--allow-paid", action="store_true")
    command = sub.add_parser("import-twin")
    for name in ("catalog", "train", "test", "out"):
        command.add_argument("--" + name, type=Path, required=True)
    command.add_argument("--revision", required=True)
    command.add_argument("--subjects", type=int, default=20)
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        if args.command in ("run", "benchmark"):
            return asyncio.run(run_command(args))
        if args.command == "populate":
            return asyncio.run(populate_command(args))
        if args.command == "validate-population":
            population = Population.load(args.population)
            population.validate_map(SmallvilleMap(extra_locations=population.locations))
            print(
                json.dumps(
                    {
                        "status": "validated",
                        "residents": len(population.agents),
                        "digest": population.digest,
                    },
                    indent=2,
                )
            )
            return 0
        if args.command == "fidelity":
            return asyncio.run(fidelity_command(args))
        if args.command == "import-twin":
            dataset = twin_dataset(
                args.catalog, args.train, args.test, args.revision, args.subjects
            )
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(dataset.model_dump_json(indent=2) + "\n")
            print(
                json.dumps(
                    {
                        "subjects": len(dataset.subjects),
                        "items": len(dataset.items),
                        "path": str(args.out),
                    },
                    indent=2,
                )
            )
            return 0
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
                        "OPENROUTER_API_KEY",
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
