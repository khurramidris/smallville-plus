import json

import pytest

from smallville.config import Config
from smallville.eval.datasets import catalog_items, gss_dataset, normalize_answer, twin_dataset
from smallville.eval.fidelity import (
    Evidence,
    FidelityDataset,
    FidelitySubject,
    run_fidelity,
    score_fidelity,
)
from smallville.eval.surveys import SurveyItem, SurveyResult, SurveyRunner
from smallville.llm.gateway import Completion, Gateway
from smallville.llm.mock import MockLLM
from smallville.world.maps import DATA


def small_dataset():
    items = [
        SurveyItem(
            id="choice",
            source_id="heldout-choice",
            question="Which do I prefer?",
            kind="categorical",
            choices=["Yes", "No"],
        ),
        SurveyItem(
            id="number",
            source_id="heldout-number",
            question="How much?",
            kind="numerical",
            minimum=0,
            maximum=10,
        ),
    ]
    return FidelityDataset(
        id="test",
        license="fixture",
        source_revision="local",
        items=items,
        subjects=[
            FidelitySubject(
                id="a",
                evidence=[
                    Evidence(
                        id="background", source_id="profile", question="My hobby", answer="reading"
                    )
                ],
                gold={"choice": "Yes", "number": 8},
                prior_answers={"choice": "No", "number": 6},
            ),
            FidelitySubject(id="b", evidence=[], gold={"choice": "No", "number": None}),
        ],
    )


def test_scales_and_invalid_answers_do_not_inflate_fidelity():
    dataset = small_dataset()
    item = dataset.items[1]
    assert not item.accepts(True) and not item.accepts(float("nan"))
    assert not item.accepts(11) and item.accepts(3.5)
    with pytest.raises(ValueError):
        SurveyItem(id="x", question="x", kind="categorical", choices=["Yes", "Yes"])
    with pytest.raises(ValueError):
        SurveyItem(id="x", question="x", kind="numerical")
    report = score_fidelity(
        dataset, [SurveyResult(subject="a", answers={"choice": "Yes"}, invalid={"number": "bad"})]
    )
    assert report["summary"]["coverage"] == 1 / 3
    assert report["summary"]["categorical_accuracy"] == 0.5
    assert report["summary"]["numerical_penalized_normalized_mae"] == 1
    assert report["summary"]["numerical_mae_valid_only"] is None
    assert report["summary"]["human_test_retest_pairs"] == 2
    assert report["unscorable_human_cells"] == 1


def test_heldout_source_ids_are_rejected_as_profile_evidence():
    data = small_dataset().model_dump()
    data["subjects"][0]["evidence"][0]["source_id"] = "heldout-number"
    with pytest.raises(ValueError, match="leaked"):
        FidelityDataset.model_validate(data)


async def test_gold_and_retest_answers_never_change_model_requests(tmp_path):
    gateway = Gateway(tmp_path, Config(), MockLLM())
    try:
        runner = SurveyRunner(gateway, Config())
        dataset = small_dataset()
        first = await run_fidelity(runner, dataset)
        modified = dataset.model_dump()
        modified["subjects"][0]["gold"] = {"choice": "No", "number": 1.23456789}
        modified["subjects"][0]["prior_answers"] = {"choice": "Yes", "number": 9.87654321}
        second = await run_fidelity(runner, FidelityDataset.model_validate(modified))
        assert first["predictions"] == second["predictions"]
        assert gateway.summary()["cache_hits"] == 2
        assert first["summary"] != second["summary"]
    finally:
        gateway.close()


async def test_malformed_surveys_are_explicit_and_wrappers_enforce_types(tmp_path):
    class BadBackend:
        async def complete(self, **kwargs):
            return Completion('{"answers":{"unexpected":"Yes"}}', 1, 1)

    gateway = Gateway(tmp_path, Config(), BadBackend())
    try:
        runner = SurveyRunner(gateway, Config())
        items = small_dataset().items
        result = await runner.answer("a", "I like reading.", {}, items)
        assert result.answers == {} and len(result.invalid) == 2
        with pytest.raises(ValueError):
            await runner.categorical_resp("a", "I like reading.", {}, items)
        with pytest.raises(ValueError):
            await runner.numerical_resp("a", "I like reading.", {}, items)
    finally:
        gateway.close()


def test_real_bundled_datasets_have_disjoint_profiles_and_human_baselines():
    twin = FidelityDataset.load(DATA / "surveys/twin_sample.json")
    gss = gss_dataset()
    assert len(twin.subjects) == 20 and len(twin.items) == 122
    assert sum(v is not None for s in twin.subjects for v in s.gold.values()) == 1888
    assert all(s.prior_answers for s in twin.subjects)
    assert {i.kind for i in twin.items} == {"categorical", "numerical"}
    assert len(gss.subjects) == 75 and len(gss.items) == 4
    assert all(not {e.id for e in s.evidence} & set(s.gold) for s in gss.subjects)


def test_catalog_codes_matrix_ids_and_local_import(tmp_path):
    catalog = [
        {
            "QuestionID": "profile",
            "QuestionText": "My background",
            "QuestionType": "MC",
            "Options": ["A", "B"],
            "Settings": {"Selector": "SAVR"},
            "csv_columns": ["profile"],
            "source": "wave1_3_persona_json",
        },
        {
            "QuestionID": "target",
            "QuestionText": "My choice",
            "QuestionType": "MC",
            "Options": ["Yes", "No"],
            "Settings": {"Selector": "SAVR"},
            "csv_columns": ["target"],
            "source": "wave4_Q_wave1_3_A",
        },
        {
            "QuestionID": "scale",
            "QuestionText": "My rating",
            "QuestionType": "Slider",
            "Statements": ["one", "three"],
            "Range": {"Min": 0, "Max": 100},
            "csv_columns": ["scale_1", "scale_3"],
            "source": "wave4_Q_wave1_3_A",
        },
        {
            "QuestionID": "free",
            "QuestionText": "An unbounded number",
            "QuestionType": "TE",
            "csv_columns": ["free_TEXT"],
        },
    ]
    items, excluded = catalog_items(catalog)
    assert "scale_3" in items and excluded[0]["question_id"] == "free"
    assert normalize_answer(items["target"], "1.0") == "Yes"
    assert normalize_answer(items["target"], "0") is None
    assert normalize_answer(items["scale_1"], "NaN") is None
    assert normalize_answer(items["scale_1"], "1000") is None
    (tmp_path / "catalog.json").write_text(json.dumps(catalog))
    (tmp_path / "train.csv").write_text("pid,profile,target,scale_1,scale_3\n1,2,2,10,20\n")
    (tmp_path / "test.csv").write_text("pid,target,scale_1,scale_3\n1,1,70,\n")
    dataset = twin_dataset(
        tmp_path / "catalog.json", tmp_path / "train.csv", tmp_path / "test.csv", "test", 1
    )
    assert [e.id for e in dataset.subjects[0].evidence] == ["profile"]
    assert dataset.subjects[0].gold == {"target": "Yes", "scale_1": 70, "scale_3": None}
    assert dataset.subjects[0].prior_answers["scale_1"] == 10
