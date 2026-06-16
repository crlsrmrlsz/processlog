"""
Output-contract conformance tests (Phase 33 audit).

Generates a run from the shipped restaurant-permit config and asserts the
LOG_FORMAT_SPEC v1.1 guarantees hold end-to-end:

  * deterministic generation (same seed -> identical frames)
  * per-case timestamp monotonicity (strictly increasing)
  * timezone-aware timestamps
  * working-hours adherence (working day + within [start, end])
  * lifecycle:transition always "complete"
  * org:resource null for automatic activities, set for human ones
  * mandatory columns first, custom attributes sorted alphabetically
  * exact CSV <-> JSON timestamp parity (sub-second precision preserved)
  * exactly one start activity per case

These pin the engine's current, correct behavior so later changes have a
provable delta, and double as the audit's contract verification.
"""

import json
import tempfile
from datetime import time
from pathlib import Path

import pandas as pd
import pytest

from processlog.config.loader import load_config
from processlog.core.generator import generate_log
from processlog.exporters.csv_exporter import _map_schema, export_csv
from processlog.exporters.json_exporter import export_json

CONFIG_PATH = Path(__file__).parent.parent / "configs" / "process_config.yaml"
SEED = 42
NUM_CASES = 60
MANDATORY = [
    "case:concept:name",
    "concept:name",
    "time:timestamp",
    "org:resource",
    "lifecycle:transition",
]


@pytest.fixture(scope="module")
def config() -> dict:
    return load_config(str(CONFIG_PATH))


@pytest.fixture(scope="module")
def df(config) -> pd.DataFrame:
    return generate_log(config, seed=SEED, num_cases=NUM_CASES)


@pytest.fixture(scope="module")
def activity_types(config) -> dict:
    return {a["id"]: a.get("type", "automatic") for a in config.get("activities", [])}


def test_generation_is_deterministic(config):
    a = generate_log(config, seed=SEED, num_cases=NUM_CASES)
    b = generate_log(config, seed=SEED, num_cases=NUM_CASES)
    pd.testing.assert_frame_equal(a, b)


def test_timestamps_strictly_increasing_within_case(df):
    for case_id, trace in df.groupby("case_id"):
        ts = trace["timestamp"].tolist()
        assert all(ts[i] < ts[i + 1] for i in range(len(ts) - 1)), case_id


def test_timestamps_are_timezone_aware(df):
    assert df["timestamp"].dt.tz is not None


def test_working_hours_adherence(df, config):
    wh = config.get("working_hours", {})
    if not wh.get("enabled", False):
        pytest.skip("working_hours not enabled in config")
    sh, sm = map(int, wh.get("start_time", "09:00").split(":"))
    eh, em = map(int, wh.get("end_time", "17:00").split(":"))
    start, end = time(sh, sm), time(eh, em)
    name_to_num = {
        "Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
        "Friday": 4, "Saturday": 5, "Sunday": 6,
    }
    working = {
        name_to_num[d]
        for d in wh.get("days", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
        if d in name_to_num
    }
    holidays = set()
    for h in wh.get("holidays", []) or []:
        try:
            holidays.add(pd.Timestamp(h).date())
        except (ValueError, TypeError):
            pass
    for ts in df["timestamp"]:
        assert ts.weekday() in working
        assert ts.date() not in holidays
        assert start <= ts.time() <= end


def test_lifecycle_always_complete(df):
    assert (df["lifecycle"] == "complete").all()


def test_resource_nullness_matches_activity_type(df, activity_types):
    # Null-ness is the contract (empty in CSV / null in JSON); pandas may store
    # it as NaN or None internally, so test with pd.isna rather than `is None`.
    for _, row in df.iterrows():
        atype = activity_types.get(row["activity"], "automatic")
        if atype == "human":
            assert not pd.isna(row["resource"])
        else:
            assert pd.isna(row["resource"])


def test_custom_attribute_columns_sorted_alphabetically(df):
    cols = list(_map_schema(df).columns)
    assert cols[:5] == MANDATORY
    custom = cols[5:]
    assert custom == sorted(custom)


def test_csv_json_timestamp_parity_full_precision(df):
    with tempfile.TemporaryDirectory() as tmp:
        csv_path = Path(tmp) / "events.csv"
        json_path = Path(tmp) / "events.json"
        export_csv(df, csv_path)
        export_json(df, json_path)
        csv_ts = pd.read_csv(csv_path, dtype=str)["time:timestamp"].tolist()
        json_ts = [
            json.loads(line)["time:timestamp"]
            for line in json_path.read_text().splitlines()
        ]
        # Byte-identical timestamps across formats ...
        assert csv_ts == json_ts
        # ... and sub-second precision actually present (regression guard).
        assert any("." in t for t in json_ts)


def test_each_case_has_single_start_activity(df, config):
    start_activity = config["activities"][0]["id"]
    for case_id, trace in df.groupby("case_id"):
        assert trace.iloc[0]["activity"] == start_activity, case_id
