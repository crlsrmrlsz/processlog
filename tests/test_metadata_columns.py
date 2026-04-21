"""Tests for the run_metadata.json `columns` schema block (Fix #5).

Downstream consumers need to know every column that appears in an exported
event log — mandatory XES columns plus whatever custom attributes the config
declared. This metadata block removes the need to read the YAML config just
to discover the schema.
"""

import pytest
import yaml

from processlog.core.generator import generate_log


@pytest.fixture
def config_with_custom_attrs(minimal_config_yaml):
    cfg = yaml.safe_load(minimal_config_yaml)
    cfg["case_attributes"] = [
        {
            "name": "case:priority",
            "type": "string",
            "values": ["low", "high"],
            "probabilities": [0.5, 0.5],
        }
    ]
    cfg["event_attributes"] = [
        {
            "name": "cost:amount",
            "type": "float",
            "generation": {
                "distribution": "normal",
                "mean": 10.0,
                "std": 2.0,
                "min": 0.0,
                "max": 100.0,
            },
            "apply_to_types": ["human", "automatic"],
        }
    ]
    return cfg


def test_metadata_has_columns_block(config_with_custom_attrs):
    _, metadata = generate_log(
        config_with_custom_attrs, seed=42, num_cases=3, return_metadata=True
    )
    assert "columns" in metadata
    assert isinstance(metadata["columns"], list)
    assert len(metadata["columns"]) >= 5


def test_metadata_mandatory_columns_use_xes_names(config_with_custom_attrs):
    _, metadata = generate_log(
        config_with_custom_attrs, seed=42, num_cases=3, return_metadata=True
    )
    names = {c["name"] for c in metadata["columns"]}
    assert {
        "case:concept:name",
        "concept:name",
        "time:timestamp",
        "org:resource",
        "lifecycle:transition",
    }.issubset(names)


def test_metadata_each_column_has_name_type_scope(config_with_custom_attrs):
    _, metadata = generate_log(
        config_with_custom_attrs, seed=42, num_cases=3, return_metadata=True
    )
    for col in metadata["columns"]:
        assert set(col.keys()) >= {"name", "type", "scope"}
        assert col["scope"] in {"event_mandatory", "case_custom", "event_custom"}


def test_metadata_custom_attrs_labeled_correctly(config_with_custom_attrs):
    _, metadata = generate_log(
        config_with_custom_attrs, seed=42, num_cases=3, return_metadata=True
    )
    by_name = {c["name"]: c for c in metadata["columns"]}
    assert by_name["case:priority"]["scope"] == "case_custom"
    assert by_name["case:priority"]["type"] == "string"
    assert by_name["cost:amount"]["scope"] == "event_custom"
    assert by_name["cost:amount"]["type"] == "float"
