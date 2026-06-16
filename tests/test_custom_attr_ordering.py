"""Tests for alphabetical ordering of custom attribute columns (Fix #6).

The 5 mandatory XES columns appear first (in their canonical order), then
any custom attributes sorted alphabetically by name. This gives stable,
diff-friendly output across runs and across exporters.
"""

import json
from datetime import datetime
from pathlib import Path

import pandas as pd
import pytest

from processlog.exporters.csv_exporter import export_csv, _map_schema
from processlog.exporters.json_exporter import export_json
from processlog.exporters.parquet_exporter import export_parquet


MANDATORY = [
    "case:concept:name",
    "concept:name",
    "time:timestamp",
    "org:resource",
    "lifecycle:transition",
]


@pytest.fixture
def df_with_unsorted_customs():
    """DataFrame whose custom attributes are declared in non-alphabetical order."""
    return pd.DataFrame(
        {
            "case_id": ["case_001"],
            "activity": ["start"],
            "timestamp": [datetime(2024, 1, 1, 9, 0, 0)],
            "resource": ["clerk_01"],
            "lifecycle": ["complete"],
            # intentionally not alphabetical:
            "zeta:attr": [1],
            "cost:amount": [10.0],
            "alpha:attr": ["x"],
        }
    )


def test_map_schema_sorts_custom_columns(df_with_unsorted_customs):
    out = _map_schema(df_with_unsorted_customs)
    cols = list(out.columns)
    assert cols[:5] == MANDATORY
    assert cols[5:] == ["alpha:attr", "cost:amount", "zeta:attr"]


def test_csv_has_alphabetical_custom_attrs(df_with_unsorted_customs, tmp_path):
    out = tmp_path / "events.csv"
    export_csv(df_with_unsorted_customs, out)
    header = out.read_text().splitlines()[0].split(",")
    assert header[:5] == MANDATORY
    assert header[5:] == ["alpha:attr", "cost:amount", "zeta:attr"]


def test_json_has_alphabetical_custom_attrs(df_with_unsorted_customs, tmp_path):
    out = tmp_path / "events.json"
    export_json(df_with_unsorted_customs, out)
    first_event = json.loads(out.read_text().splitlines()[0])
    custom_keys = [k for k in first_event.keys() if k not in MANDATORY]
    assert custom_keys == ["alpha:attr", "cost:amount", "zeta:attr"]


def test_parquet_has_alphabetical_custom_attrs(df_with_unsorted_customs, tmp_path):
    out = tmp_path / "events.parquet"
    export_parquet(df_with_unsorted_customs, out)
    cols = list(pd.read_parquet(out).columns)
    assert cols[:5] == MANDATORY
    assert cols[5:] == ["alpha:attr", "cost:amount", "zeta:attr"]
