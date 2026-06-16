"""
Tests for the opt-in `emit_labels` config flag.

When `emit_labels: true` is set at the top level of the YAML config, the
generator must emit each activity's human-readable `name:` to the event's
`activity` field (which becomes `concept:name` on export) and each
selected human resource's `name:` to the `resource` field (which becomes
`org:resource`). Internal flow / next_steps / variant tracking / resource
selection stay id-keyed.

Default behaviour (`emit_labels` absent or false) is preserved exactly:
ids emit as before so legacy configs and their pinned fixtures stay
byte-identical.
"""

import pytest

from processlog.config.loader import parse_yaml
from processlog.config.validator import validate_config
from processlog.core.generator import generate_log


@pytest.fixture
def labels_config_yaml() -> str:
    """
    Minimal config with `name:` on every activity and resource so that
    flipping `emit_labels` is observable in the generated DataFrame.
    """
    return """
process_name: "Labels Demo"
num_cases: 5
seed: 42
start_date: "2024-01-01"
timezone: "UTC"
emit_labels: true

activities:
  - step: 1
    id: begin
    name: "Beginning"
    type: automatic
    duration:
      min: 0
      max: 1
    next_steps:
      - activity: human_review
        probability: 1.0

  - step: 2
    id: human_review
    name: "Human Review"
    type: human
    resource_pool: workers
    duration:
      min: 0
      max: 1
    next_steps:
      - activity: end
        probability: 1.0

  - step: 3
    id: end
    name: "End"
    type: automatic
    duration:
      min: 0
      max: 1
    next_steps: []

resource_pools:
  workers:
    - id: user_001
      name: "Alice Worker"
      speed: 1.0
      consistency: 1.0
      capacity: 1.0
"""


class TestEmitLabels:
    """The `emit_labels` flag changes only the strings emitted to the
    `activity` and `resource` columns; everything else (case flow,
    counts, durations) is unaffected."""

    def test_flag_validates(self, labels_config_yaml):
        """The flag is accepted by the validator as a boolean field."""
        config = parse_yaml(labels_config_yaml)
        result = validate_config(config)
        assert result.valid, f"validator errors: {result.errors}"

    def test_emit_labels_true_uses_activity_names(self, labels_config_yaml):
        """Every emitted `activity` is the human-readable name, never an id."""
        config = parse_yaml(labels_config_yaml)
        df = generate_log(config, seed=42, num_cases=5)

        activities = set(df["activity"].unique())
        assert activities == {"Beginning", "Human Review", "End"}
        # Negative: no id strings leaked.
        assert "begin" not in activities
        assert "human_review" not in activities
        assert "end" not in activities

    def test_emit_labels_true_uses_resource_names(self, labels_config_yaml):
        """Human-activity rows carry the resource display name."""
        config = parse_yaml(labels_config_yaml)
        df = generate_log(config, seed=42, num_cases=5)

        human_rows = df[df["activity"] == "Human Review"]
        assert not human_rows.empty
        resources = set(human_rows["resource"].dropna().unique())
        assert resources == {"Alice Worker"}
        assert "user_001" not in resources

    def test_emit_labels_keeps_automatic_resource_null(self, labels_config_yaml):
        """Automatic-activity rows still emit `None` for resource, not a fabricated name."""
        config = parse_yaml(labels_config_yaml)
        df = generate_log(config, seed=42, num_cases=5)

        auto_rows = df[df["activity"].isin(["Beginning", "End"])]
        assert auto_rows["resource"].isna().all()

    def test_emit_labels_default_false_preserves_ids(self, labels_config_yaml):
        """Without `emit_labels` (or with it `false`), ids emit as before — guards permit fixtures' byte-identity."""
        # Strip the `emit_labels: true` line so the config defaults to off.
        yaml_without_flag = labels_config_yaml.replace("emit_labels: true\n", "")
        config = parse_yaml(yaml_without_flag)
        df = generate_log(config, seed=42, num_cases=5)

        activities = set(df["activity"].unique())
        assert activities == {"begin", "human_review", "end"}
        assert "Beginning" not in activities

        human_rows = df[df["activity"] == "human_review"]
        assert set(human_rows["resource"].dropna().unique()) == {"user_001"}

    def test_emit_labels_false_explicitly_preserves_ids(self, labels_config_yaml):
        """`emit_labels: false` set explicitly behaves the same as absent."""
        yaml_off = labels_config_yaml.replace("emit_labels: true", "emit_labels: false")
        config = parse_yaml(yaml_off)
        df = generate_log(config, seed=42, num_cases=5)

        assert set(df["activity"].unique()) == {"begin", "human_review", "end"}

    def test_emit_labels_falls_back_to_id_when_name_missing(self):
        """Defensive: an activity or resource without `name:` falls back to `id`, so the flag is safe to flip on legacy configs."""
        yaml_with_missing_names = """
process_name: "Fallback Demo"
num_cases: 3
seed: 42
start_date: "2024-01-01"
timezone: "UTC"
emit_labels: true

activities:
  - step: 1
    id: lone_start
    type: automatic
    duration:
      min: 0
      max: 1
    next_steps:
      - activity: lone_end
        probability: 1.0

  - step: 2
    id: lone_end
    type: automatic
    duration:
      min: 0
      max: 1
    next_steps: []

resource_pools: {}
"""
        config = parse_yaml(yaml_with_missing_names)
        df = generate_log(config, seed=42, num_cases=3)

        # `name:` absent → fall back to `id:`.
        assert set(df["activity"].unique()) == {"lone_start", "lone_end"}

    def test_emit_labels_does_not_change_case_count(self, labels_config_yaml):
        """The flag is purely a string substitution; case + event counts are unchanged vs ids-only."""
        config_with = parse_yaml(labels_config_yaml)
        config_without = parse_yaml(
            labels_config_yaml.replace("emit_labels: true", "emit_labels: false")
        )

        df_with = generate_log(config_with, seed=42, num_cases=5)
        df_without = generate_log(config_without, seed=42, num_cases=5)

        assert df_with["case_id"].nunique() == df_without["case_id"].nunique()
        assert len(df_with) == len(df_without)
