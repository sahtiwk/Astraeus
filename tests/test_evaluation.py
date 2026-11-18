import json
from pathlib import Path
from evaluation.generate_cases import FAMILIES


def test_dataset_split_and_provenance():
    cases=[json.loads(line) for line in (Path(__file__).parents[1]/'evaluation/cases.jsonl').read_text().splitlines()]
    assert len(cases)==108
    assert len({c['run_id'] for c in cases})==len(cases)
    assert {c['family'] for c in cases}==set(FAMILIES)
    assert all(c['provenance']['method'] in ('executed','ambiguous fixture, not a confirmed fault') for c in cases)
    assert all(c['expected_cause'] not in c['logs'] for c in cases)
    assert {c['split'] for c in cases}=={'train','validation','test'}
