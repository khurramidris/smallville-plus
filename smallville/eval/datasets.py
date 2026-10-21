"""Adapters for licensed public GSS bank and Twin question/response files."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
from pathlib import Path

from smallville.eval.fidelity import Evidence, FidelityDataset, FidelitySubject
from smallville.eval.surveys import SurveyItem
from smallville.personas.generation import GSS_REVISION
from smallville.world.maps import DATA


def gss_dataset() -> FidelityDataset:
    files = sorted((DATA / "gss").glob("*.json"))
    records = [(p.stem, json.loads(p.read_text())) for p in files]
    categorical = ("political_views", "party_identification", "religion")
    protected = {*categorical, "age"}
    items = [
        SurveyItem(
            id=k,
            source_id=k,
            question=f"How do I describe my {k.replace('_', ' ')}?",
            kind="categorical",
            fact_key=k,
            choices=sorted({str(r[k]) for _, r in records}),
        )
        for k in categorical
    ]
    items.append(
        SurveyItem(
            id="age",
            source_id="age",
            fact_key="age",
            question="How old am I in years?",
            kind="numerical",
            minimum=18,
            maximum=120,
            integer=True,
        )
    )
    subjects = []
    for identifier, record in records:
        evidence = [
            Evidence(id=k, source_id=k, question=f"My {k.replace('_', ' ')}", answer=v)
            for k, v in record.items()
            if k not in protected | {"first_name", "last_name", "street_address", "city", "state"}
        ]
        subjects.append(
            FidelitySubject(
                id="gss:" + identifier, evidence=evidence, gold={i.id: record[i.id] for i in items}
            )
        )
    return FidelityDataset(
        id="genagents-gss-heldout-demographics",
        license="MIT",
        source_revision=GSS_REVISION,
        items=items,
        subjects=subjects,
        metadata={
            "source_population": 3505,
            "retained_subjects": len(subjects),
            "selection": "first 75 by SHA256('smallville-phase2:' + source path)",
            "scope": "Public GSS-derived demographic bank, not restricted interview agents or a new human experiment.",
            "heldout_fields": sorted(protected),
        },
    )


def catalog_items(catalog: list[dict]) -> tuple[dict[str, SurveyItem], list[dict]]:
    items, excluded = {}, []
    for entry in catalog:
        qid, kind = entry["QuestionID"], entry["QuestionType"]
        columns = entry.get("csv_columns", [])
        common = {"source_id": qid, "block": entry.get("BlockName", "").strip()}
        text = entry.get("QuestionText", "").strip()
        selector = entry.get("Settings", {}).get("Selector", "")
        generated = []
        if kind == "MC" and selector in ("SAVR", "SAHR") and len(columns) == 1 and text:
            generated.append(
                SurveyItem(
                    id=columns[0],
                    question=text,
                    kind="categorical",
                    choices=entry["Options"],
                    **common,
                )
            )
        elif kind == "Matrix" and entry.get("Columns") and text:
            rows = entry.get("Rows", [])
            if len(rows) == len(columns):
                generated.extend(
                    SurveyItem(
                        id=c,
                        question=text + "\n" + row,
                        kind="categorical",
                        choices=entry["Columns"],
                        **common,
                    )
                    for c, row in zip(columns, rows)
                )
        elif kind == "Slider" and entry.get("Range") and text:
            labels = entry.get("Statements", [""])
            if len(labels) == len(columns):
                generated.extend(
                    SurveyItem(
                        id=c,
                        question=text + ("\n" + label if label else ""),
                        kind="numerical",
                        minimum=entry["Range"]["Min"],
                        maximum=entry["Range"]["Max"],
                        **common,
                    )
                    for c, label in zip(columns, labels)
                )
        elif kind == "TE" and len(columns) == 1:
            bounds = re.search(r"number between (\d+) and (\d+)", text)
            if bounds:
                generated.append(
                    SurveyItem(
                        id=columns[0],
                        question=text,
                        kind="numerical",
                        minimum=int(bounds[1]),
                        maximum=int(bounds[2]),
                        **common,
                    )
                )
        if not generated:
            excluded.append(
                {
                    "question_id": qid,
                    "block": common["block"],
                    "reason": "unsupported encoding, missing stimulus, or no explicit numerical bounds",
                }
            )
        for item in generated:
            if item.id in items:
                raise ValueError("question catalog produced duplicate CSV item IDs")
            items[item.id] = item
    return items, excluded


def normalize_answer(item: SurveyItem, raw: str | None):
    if raw is None or not raw.strip():
        return None
    try:
        number = float(raw)
        if not math.isfinite(number):
            return None
        if item.kind == "categorical":
            if number != int(number) or not 1 <= number <= len(item.choices):
                return None
            return item.choices[int(number) - 1]
        if item.accepts(number):
            return int(number) if item.integer else number
    except (ValueError, OverflowError):
        return raw if item.accepts(raw) else None
    return None


def twin_dataset(
    catalog_path: Path, train_path: Path, test_path: Path, revision: str, subjects: int = 20
) -> FidelityDataset:
    if subjects < 1:
        raise ValueError("at least one survey subject is required")
    catalog = json.loads(catalog_path.read_text())
    all_items, excluded = catalog_items(catalog)
    heldout_roots = {e["QuestionID"] for e in catalog if e.get("source") == "wave4_Q_wave1_3_A"}
    targets = [i for i in all_items.values() if i.source_id in heldout_roots]
    profile_items = [i for i in all_items.values() if i.source_id not in heldout_roots][:32]
    with train_path.open() as file:
        train = {r["pid"]: r for r in csv.DictReader(file)}
    with test_path.open() as file:
        test = {r["pid"]: r for r in csv.DictReader(file)}
    identifiers = sorted(
        train.keys() & test.keys(),
        key=lambda x: hashlib.sha256(("smallville-twin:" + x).encode()).hexdigest(),
    )[:subjects]
    records = []
    for identifier in identifiers:
        evidence = []
        for item in profile_items:
            answer = normalize_answer(item, train[identifier].get(item.id))
            if answer is not None:
                evidence.append(
                    Evidence(
                        id=item.id, source_id=item.source_id, question=item.question, answer=answer
                    )
                )
        gold = {i.id: normalize_answer(i, test[identifier].get(i.id)) for i in targets}
        prior = {i.id: normalize_answer(i, train[identifier].get(i.id)) for i in targets}
        records.append(
            FidelitySubject(
                id="twin:" + identifier,
                evidence=evidence,
                gold=gold,
                prior_answers=prior,
                unscorable={
                    k: "missing or out-of-scale source answer" for k, v in gold.items() if v is None
                },
            )
        )
    return FidelityDataset(
        id="Twin-2K-500-wave4-subset",
        license="CC-BY-4.0",
        source_revision=revision,
        items=targets,
        subjects=records,
        metadata={
            "total_source_subjects": len(test),
            "retained_subjects": len(records),
            "source_question_blocks": len(catalog),
            "supported_target_items": len(targets),
            "profile_items_limit": 32,
            "excluded_catalog_entries": excluded,
            "split": "Profile: 32 supported wave1-3 fields excluding every wave4 QuestionID. Gold: wave4; prior wave1-3 answers are scorer-only test-retest baselines.",
            "limitations": "Bounded subset and supported encodings only; source between-subject missingness is retained. This is not the complete paper evaluation protocol.",
        },
    )
