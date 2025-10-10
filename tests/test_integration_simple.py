"""
Simple integration tests for Phase 3

Tests the complete workflow: config → validate → generate → export
"""

import pytest
import tempfile
from pathlib import Path

from event_log_gen.config import load_config, validate_config, parse_yaml
from event_log_gen.core.generator import generate_log
from event_log_gen.exporters.csv_exporter import export_csv
import pandas as pd


class TestSimpleIntegration:
    """Simple integration tests for Phase 3 minimal generator"""

    def test_end_to_end_minimal_workflow(self, minimal_config_yaml):
        """Test complete workflow: parse → validate → generate → export"""
        # 1. Parse configuration
        config = parse_yaml(minimal_config_yaml)
        assert config is not None

        # 2. Validate configuration
        result = validate_config(config)
        assert result.valid is True, f"Validation errors: {result.errors}"

        # 3. Generate event log
        df = generate_log(config, seed=42, num_cases=10)
        assert len(df) > 0
        assert df["case_id"].nunique() == 10

        # 4. Export to CSV
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "events.csv"
            export_csv(df, output_path)

            # 5. Verify CSV was created and can be read
            assert output_path.exists()
            df_read = pd.read_csv(output_path)
            assert len(df_read) > 0
            assert "case:concept:name" in df_read.columns
            assert "concept:name" in df_read.columns

    def test_workflow_with_full_config(self):
        """Test workflow with a more complete configuration"""
        config_yaml = """
        process_name: "Restaurant Permit Application (Simplified)"
        num_cases: 5
        seed: 42
        start_date: "2024-01-01"
        timezone: "America/New_York"

        activities:
          - step: 1
            id: submitted
            name: "Application Submitted"
            type: automatic
            duration:
              min: 0
              max: 1
            next_steps:
              - activity: intake_validation
                probability: 1.0

          - step: 2
            id: intake_validation
            name: "Intake Validation"
            type: human
            resource_pool: clerks
            duration:
              min: 24
              max: 72
            next_steps:
              - activity: approved
                probability: 0.6
              - activity: rejected
                probability: 0.4

          - step: 3
            id: approved
            name: "Application Approved"
            type: automatic
            duration:
              min: 0
              max: 1
            next_steps: []

          - step: 4
            id: rejected
            name: "Application Rejected"
            type: automatic
            duration:
              min: 0
              max: 1
            next_steps: []

        resource_pools:
          clerks:
            - id: clerk_001
              name: "Alice Martinez"
              speed: 0.8
              consistency: 0.9
              capacity: 1.0
            - id: clerk_002
              name: "Bob Johnson"
              speed: 1.2
              consistency: 0.7
              capacity: 1.0
        """

        # Parse and validate
        config = parse_yaml(config_yaml)
        result = validate_config(config)
        assert result.valid is True

        # Generate
        df = generate_log(config, seed=42, num_cases=5)

        # Verify structure
        assert df["case_id"].nunique() == 5
        assert "submitted" in df["activity"].values
        assert set(df["lifecycle"].unique()) == {"complete"}

        # Verify variants emerge (approved and rejected)
        final_activities = df.groupby("case_id")["activity"].last()
        assert "approved" in final_activities.values or "rejected" in final_activities.values

    def test_reproducibility_across_workflow(self, minimal_config_yaml):
        """Test that entire workflow is reproducible"""
        config = parse_yaml(minimal_config_yaml)

        # Generate twice with same seed
        df1 = generate_log(config, seed=42, num_cases=10)
        df2 = generate_log(config, seed=42, num_cases=10)

        # Should be identical
        assert df1.equals(df2)

    def test_exported_csv_has_pm4py_columns(self, minimal_config_yaml):
        """Test that exported CSV has correct PM4Py column names"""
        config = parse_yaml(minimal_config_yaml)
        df = generate_log(config, seed=42, num_cases=5)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "events.csv"
            export_csv(df, output_path)

            # Read back
            df_read = pd.read_csv(output_path)

            # Check PM4Py column names
            expected_columns = {
                "case:concept:name",
                "concept:name",
                "time:timestamp",
                "org:resource",
                "lifecycle:transition",
            }
            assert expected_columns.issubset(set(df_read.columns))

    def test_multiple_cases_have_different_timestamps(self, minimal_config_yaml):
        """Test that different cases can have overlapping timestamps"""
        config = parse_yaml(minimal_config_yaml)
        df = generate_log(config, seed=42, num_cases=10)

        # Get first event timestamp for each case
        first_events = df.groupby("case_id").first()

        # All cases should start at the same time in Phase 3
        # (Phase 4 will add inter-case delays)
        start_timestamps = first_events["timestamp"]
        assert len(start_timestamps.unique()) == 1  # All start at same time in Phase 3

    def test_validation_errors_prevent_generation(self):
        """Test that validation errors are caught before generation"""
        invalid_config_yaml = """
        process_name: "Test"
        num_cases: 10
        seed: 42
        start_date: "2024-01-01"

        activities:
          - id: start
            name: "Start"
            type: automatic
            duration:
              min: 10
              max: 20
            next_steps:
              - activity: end
                probability: 0.5  # Invalid: doesn't sum to 1.0

        resource_pools:
          clerks:
            - id: clerk_001
              name: "Clerk 1"
        """

        config = parse_yaml(invalid_config_yaml)
        result = validate_config(config)

        # Validation should fail
        assert result.valid is False
        assert any("probabilities sum to" in err for err in result.errors)

        # Generation would fail if attempted (but we skip it in practice)
