"""Integration tests for timezone-aware timestamp generation (Fix #1).

The config's `timezone` field must be honored: generated timestamps and all
exported formats must carry the declared timezone rather than being naive.
"""

import json
from pathlib import Path

import pandas as pd
import pytest
import yaml

from processlog.core.generator import generate_log
from processlog.exporters.csv_exporter import export_csv
from processlog.exporters.json_exporter import export_json
from processlog.exporters.parquet_exporter import export_parquet


@pytest.fixture
def ny_config(minimal_config_yaml):
    cfg = yaml.safe_load(minimal_config_yaml)
    cfg["timezone"] = "America/New_York"
    return cfg


def test_generator_emits_tz_aware_timestamps(ny_config):
    df = generate_log(ny_config, seed=42, num_cases=3)
    assert "timestamp" in df.columns
    ts_dtype = df["timestamp"].dtype
    assert getattr(ts_dtype, "tz", None) is not None, (
        f"expected tz-aware dtype, got {ts_dtype!r}"
    )
    assert str(ts_dtype.tz) == "America/New_York"


def test_csv_preserves_timezone(ny_config, tmp_path):
    df = generate_log(ny_config, seed=42, num_cases=3)
    out = tmp_path / "events.csv"
    export_csv(df, out)
    # The on-disk CSV must carry the tz offset in the timestamp column.
    first_data_row = out.read_text().splitlines()[1]
    assert "-05:00" in first_data_row or "-04:00" in first_data_row, (
        f"expected NY offset in CSV row, got {first_data_row!r}"
    )
    # And the string must re-parse to a tz-aware datetime via pd.to_datetime.
    roundtrip = pd.read_csv(out)
    parsed = pd.to_datetime(roundtrip["time:timestamp"], utc=False, format="ISO8601")
    assert parsed.dt.tz is not None


def test_json_preserves_timezone_offset(ny_config, tmp_path):
    df = generate_log(ny_config, seed=42, num_cases=3)
    out = tmp_path / "events.json"
    export_json(df, out)
    first_event = json.loads(out.read_text().splitlines()[0])
    ts = first_event["time:timestamp"]
    # Expect a trailing offset like "-05:00" or "-04:00" (NY winter/summer).
    assert ts.endswith("-05:00") or ts.endswith("-04:00"), (
        f"expected NY offset, got {ts!r}"
    )


def test_parquet_preserves_timezone(ny_config, tmp_path):
    df = generate_log(ny_config, seed=42, num_cases=3)
    out = tmp_path / "events.parquet"
    export_parquet(df, out)
    roundtrip = pd.read_parquet(out)
    assert roundtrip["time:timestamp"].dt.tz is not None
