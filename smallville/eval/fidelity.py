"""Hold-out evaluation with explicit invalid/missing-answer accounting."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from statistics import mean

from pydantic import Field, model_validator

from smallville.eval.reporting import evidence_labels
from smallville.eval.surveys import Answer, SurveyItem, SurveyResult, SurveyRunner
from smallville.world.models import Model


class Evidence(Model):
    id: str
    source_id: str
    question: str
    answer: Answer


class FidelitySubject(Model):
    id: str
    evidence: list[Evidence]
    gold: dict[str, Answer | None]
    prior_answers: dict[str, Answer | None] = Field(default_factory=dict)
    unscorable: dict[str, str] = Field(default_factory=dict)


class FidelityDataset(Model):
    id: str
    license: str
    source_revision: str
    items: list[SurveyItem]
    subjects: list[FidelitySubject]
    metadata: dict = Field(default_factory=dict)

    @model_validator(mode="after")
    def disjoint_evidence(self):
        ids = {i.id for i in self.items}
        if len(ids) != len(self.items) or not ids or not self.subjects:
            raise ValueError("fidelity dataset requires distinct items and subjects")
        if len({s.id for s in self.subjects}) != len(self.subjects):
            raise ValueError("duplicate fidelity subject")
        protected = {i.source_id for i in self.items}
        for subject in self.subjects:
            if ids != set(subject.gold):
                raise ValueError(
                    "every held-out item must have an answer or explicit missing value"
                )
            if any(e.source_id in protected or e.id in ids for e in subject.evidence):
                raise ValueError("held-out item leaked into persona evidence")
            for item in self.items:
                gold = subject.gold[item.id]
                if gold is not None and not item.accepts(gold):
                    raise ValueError("human answer is outside the declared survey scale")
        return self

    @classmethod
    def load(cls, path: Path) -> FidelityDataset:
        return cls.model_validate_json(path.read_text())


def score_fidelity(dataset: FidelityDataset, responses: list[SurveyResult]) -> dict:
    predictions = {r.subject: r for r in responses}
    if len(predictions) != len(responses) or set(predictions) - {s.id for s in dataset.subjects}:
        raise ValueError("duplicate or unknown prediction subject")
    rows = []
    for subject in dataset.subjects:
        prediction = predictions.get(subject.id, SurveyResult(subject=subject.id))
        for item in dataset.items:
            gold = subject.gold[item.id]
            if gold is None:
                continue
            value = prediction.answers.get(item.id)
            valid = item.accepts(value) and item.id not in prediction.invalid
            prior = subject.prior_answers.get(item.id)
            row = {
                "subject": subject.id,
                "item": item.id,
                "kind": item.kind,
                "valid": valid,
                "gold": gold,
                "prediction": value if valid else None,
                "prior_valid": item.accepts(prior),
            }
            if item.kind == "categorical":
                row.update(
                    correct=valid and value == gold,
                    prior_correct=prior == gold if item.accepts(prior) else None,
                )
            else:
                scale = item.maximum - item.minimum
                error = abs(value - gold) if valid else None
                row.update(
                    absolute_error=error,
                    normalized_error=error / scale if valid else 1.0,
                    prior_normalized_error=abs(prior - gold) / scale
                    if item.accepts(prior)
                    else None,
                )
            rows.append(row)

    def summarize(values):
        categorical = [r for r in values if r["kind"] == "categorical"]
        numerical = [r for r in values if r["kind"] == "numerical"]
        valid_numeric = [r for r in numerical if r["valid"]]
        prior_cat = [r for r in categorical if r["prior_valid"]]
        prior_num = [r for r in numerical if r["prior_valid"]]
        return {
            "eligible_human_answers": len(values),
            "valid_predictions": sum(r["valid"] for r in values),
            "coverage": sum(r["valid"] for r in values) / len(values) if values else None,
            "categorical_accuracy": mean(r["correct"] for r in categorical)
            if categorical
            else None,
            "categorical_count": len(categorical),
            "numerical_count": len(numerical),
            "numerical_mae_valid_only": mean(r["absolute_error"] for r in valid_numeric)
            if valid_numeric
            else None,
            "numerical_penalized_normalized_mae": mean(r["normalized_error"] for r in numerical)
            if numerical
            else None,
            "human_test_retest_categorical_accuracy": mean(r["prior_correct"] for r in prior_cat)
            if prior_cat
            else None,
            "human_test_retest_normalized_mae": mean(r["prior_normalized_error"] for r in prior_num)
            if prior_num
            else None,
            "human_test_retest_pairs": len(prior_cat) + len(prior_num),
        }

    return {
        "dataset": dataset.id,
        "license": dataset.license,
        "source_revision": dataset.source_revision,
        "subjects": len(dataset.subjects),
        "items": len(dataset.items),
        "profile_and_target_ids_disjoint": True,
        "summary": summarize(rows),
        "per_item": {
            item.id: summarize([r for r in rows if r["item"] == item.id]) for item in dataset.items
        },
        "per_subject": {
            s.id: summarize([r for r in rows if r["subject"] == s.id]) for s in dataset.subjects
        },
        "unscorable_human_cells": sum(v is None for s in dataset.subjects for v in s.gold.values()),
        "unscorable_reasons": dict(
            Counter(reason for s in dataset.subjects for reason in s.unscorable.values())
        ),
        "metadata": dataset.metadata,
        "predictions": [r.model_dump() for r in responses],
        "note": "Missing/invalid predictions count as categorical errors and maximum normalized numerical error. "
        "MAE on valid numerical predictions is reported separately. No causal or population-fidelity claim.",
    }


async def run_fidelity(runner: SurveyRunner, dataset: FidelityDataset, batch_size: int = 8) -> dict:
    if not 1 <= batch_size <= 32:
        raise ValueError("survey batch size must be between 1 and 32")
    results = []
    for subject in dataset.subjects:
        # Only evidence crosses the model boundary. Neither gold nor prior test-
        # retest answers appear in a request or in repair feedback.
        background = "These are answers I previously gave about my own life:\n" + json.dumps(
            [e.model_dump() for e in subject.evidence], ensure_ascii=False, sort_keys=True
        )
        facts = {e.id: e.answer for e in subject.evidence}
        combined = SurveyResult(subject=subject.id)
        for offset in range(0, len(dataset.items), batch_size):
            result = await runner.answer(
                subject.id, background, facts, dataset.items[offset : offset + batch_size]
            )
            combined.answers.update(result.answers)
            combined.invalid.update(result.invalid)
        results.append(combined)
    report = score_fidelity(dataset, results)
    report["backend"] = runner.config.backend
    report["mock_scores_are_engineering_fixtures"] = runner.config.backend == "mock"
    report["model_training_contamination_assessed"] = False
    report.update(evidence_labels(runner.config.backend))
    return report
