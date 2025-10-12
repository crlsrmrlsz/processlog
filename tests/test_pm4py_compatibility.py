"""
PM4Py compatibility tests

CRITICAL: These tests validate that generated event logs are fully compatible
with PM4Py functions for process mining analysis.
"""

import pytest
import pandas as pd
import tempfile
from pathlib import Path

from processlog.config import load_config, validate_config, parse_yaml
from processlog.core.generator import generate_log
from processlog.exporters.csv_exporter import export_csv
from processlog.exporters.parquet_exporter import export_parquet
from processlog.exporters.json_exporter import export_json


class TestPM4PyImport:
    """Test PM4Py can import generated files"""

    def test_pandas_read_csv(self, minimal_config_yaml):
        """Test pandas can read generated CSV files"""
        config = parse_yaml(minimal_config_yaml)
        df = generate_log(config, seed=42, num_cases=10)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "events.csv"
            export_csv(df, output_path)

            # Read CSV with pandas
            df_imported = pd.read_csv(str(output_path))

            assert df_imported is not None
            assert len(df_imported) > 0
            assert "case:concept:name" in df_imported.columns
            assert "concept:name" in df_imported.columns
            assert "time:timestamp" in df_imported.columns

    def test_pm4py_format_dataframe(self, minimal_config_yaml):
        """Test PM4Py format_dataframe accepts generated DataFrame"""
        import pm4py

        config = parse_yaml(minimal_config_yaml)
        df = generate_log(config, seed=42, num_cases=10)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "events.csv"
            export_csv(df, output_path)
            df_imported = pd.read_csv(str(output_path))

            # PM4Py should be able to format the DataFrame
            df_formatted = pm4py.format_dataframe(
                df_imported,
                case_id='case:concept:name',
                activity_key='concept:name',
                timestamp_key='time:timestamp'
            )

            assert df_formatted is not None
            assert len(df_formatted) > 0
            # Check PM4Py added index columns
            assert '@@index' in df_formatted.columns or '@@case_index' in df_formatted.columns


class TestPM4PyConversion:
    """Test PM4Py EventLog conversion"""

    def test_pm4py_convert_to_event_log(self, minimal_config_yaml):
        """Test PM4Py can convert DataFrame to EventLog"""
        import pm4py

        config = parse_yaml(minimal_config_yaml)
        df = generate_log(config, seed=42, num_cases=10)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "events.csv"
            export_csv(df, output_path)
            df_imported = pd.read_csv(str(output_path))
            df_formatted = pm4py.format_dataframe(
                df_imported,
                case_id='case:concept:name',
                activity_key='concept:name',
                timestamp_key='time:timestamp'
            )

            # Convert to EventLog
            event_log = pm4py.convert_to_event_log(df_formatted)

            assert event_log is not None
            assert len(event_log) > 0  # Should have traces
            # Check that we have the expected number of cases
            assert len(event_log) == 10


class TestPM4PyProcessDiscovery:
    """Test PM4Py process discovery functions"""

    def test_pm4py_discover_dfg(self, minimal_config_yaml):
        """Test PM4Py can discover DFG from generated log"""
        import pm4py

        config = parse_yaml(minimal_config_yaml)
        df = generate_log(config, seed=42, num_cases=10)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "events.csv"
            export_csv(df, output_path)
            df_imported = pd.read_csv(str(output_path))
            df_formatted = pm4py.format_dataframe(
                df_imported,
                case_id='case:concept:name',
                activity_key='concept:name',
                timestamp_key='time:timestamp'
            )
            event_log = pm4py.convert_to_event_log(df_formatted)

            # Discover DFG
            dfg, start_activities, end_activities = pm4py.discover_dfg(event_log)

            assert dfg is not None
            assert isinstance(dfg, dict)
            assert len(dfg) > 0  # Should have at least one edge

            assert start_activities is not None
            assert len(start_activities) > 0

            assert end_activities is not None
            assert len(end_activities) > 0


class TestPM4PyStatistics:
    """Test PM4Py statistics functions"""

    def test_pm4py_get_start_activities(self, minimal_config_yaml):
        """Test PM4Py get_start_activities works"""
        import pm4py

        config = parse_yaml(minimal_config_yaml)
        df = generate_log(config, seed=42, num_cases=10)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "events.csv"
            export_csv(df, output_path)
            df_imported = pd.read_csv(str(output_path))
            df_formatted = pm4py.format_dataframe(
                df_imported,
                case_id='case:concept:name',
                activity_key='concept:name',
                timestamp_key='time:timestamp'
            )
            event_log = pm4py.convert_to_event_log(df_formatted)

            # Get start activities
            start_activities = pm4py.get_start_activities(event_log)

            assert start_activities is not None
            assert isinstance(start_activities, dict)
            assert len(start_activities) > 0
            # Should have 'start' as the only start activity
            assert 'start' in start_activities

    def test_pm4py_get_end_activities(self, minimal_config_yaml):
        """Test PM4Py get_end_activities works"""
        import pm4py

        config = parse_yaml(minimal_config_yaml)
        df = generate_log(config, seed=42, num_cases=10)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "events.csv"
            export_csv(df, output_path)
            df_imported = pd.read_csv(str(output_path))
            df_formatted = pm4py.format_dataframe(
                df_imported,
                case_id='case:concept:name',
                activity_key='concept:name',
                timestamp_key='time:timestamp'
            )
            event_log = pm4py.convert_to_event_log(df_formatted)

            # Get end activities
            end_activities = pm4py.get_end_activities(event_log)

            assert end_activities is not None
            assert isinstance(end_activities, dict)
            assert len(end_activities) > 0
            # Should have 'end' as the only end activity
            assert 'end' in end_activities


class TestPM4PyCustomAttributes:
    """Test PM4Py preserves custom attributes"""

    @pytest.mark.skip(reason="Custom attributes support is Phase 4 - not yet implemented")
    def test_pm4py_custom_attributes_preserved(self):
        """Test custom attributes are preserved in PM4Py (Phase 4)"""
        import pm4py

        config_yaml = """
        process_name: "Test with Custom Attributes"
        num_cases: 5
        seed: 42
        start_date: "2024-01-01"

        activities:
          - step: 1
            id: start
            name: "Start"
            type: automatic
            duration:
              min: 0
              max: 1
            custom_attributes:
              org:department: "IT"
              cost:amount: 100.0
            next_steps:
              - activity: end
                probability: 1.0

          - step: 2
            id: end
            name: "End"
            type: automatic
            duration:
              min: 0
              max: 1
            custom_attributes:
              org:department: "Operations"
              cost:amount: 50.0
            next_steps: []

        resource_pools:
          clerks:
            - id: clerk_001
              name: "Test Clerk"
        """

        config = parse_yaml(config_yaml)
        df = generate_log(config, seed=42, num_cases=5)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "events.csv"
            export_csv(df, output_path)

            # Read with pandas
            df_imported = pd.read_csv(str(output_path))

            # Check custom attributes are present
            assert "org:department" in df_imported.columns
            assert "cost:amount" in df_imported.columns

            # Verify values
            start_events = df_imported[df_imported["concept:name"] == "start"]
            assert (start_events["org:department"] == "IT").all()
            assert (start_events["cost:amount"] == 100.0).all()


class TestPM4PyParquetImport:
    """Test PM4Py can import generated Parquet files"""

    def test_pandas_read_parquet(self, minimal_config_yaml):
        """Test pandas can read generated Parquet files"""
        config = parse_yaml(minimal_config_yaml)
        df = generate_log(config, seed=42, num_cases=10)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "events.parquet"
            export_parquet(df, output_path)

            # Read Parquet with pandas
            df_imported = pd.read_parquet(str(output_path))

            assert df_imported is not None
            assert len(df_imported) > 0
            assert "case:concept:name" in df_imported.columns
            assert "concept:name" in df_imported.columns
            assert "time:timestamp" in df_imported.columns

    def test_pm4py_format_dataframe_parquet(self, minimal_config_yaml):
        """Test PM4Py format_dataframe accepts Parquet-loaded DataFrame"""
        import pm4py

        config = parse_yaml(minimal_config_yaml)
        df = generate_log(config, seed=42, num_cases=10)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "events.parquet"
            export_parquet(df, output_path)
            df_imported = pd.read_parquet(str(output_path))

            # PM4Py should be able to format the DataFrame
            df_formatted = pm4py.format_dataframe(
                df_imported,
                case_id='case:concept:name',
                activity_key='concept:name',
                timestamp_key='time:timestamp'
            )

            assert df_formatted is not None
            assert len(df_formatted) > 0
            # Check PM4Py added index columns
            assert '@@index' in df_formatted.columns or '@@case_index' in df_formatted.columns

    def test_pm4py_convert_to_event_log_parquet(self, minimal_config_yaml):
        """Test PM4Py can convert Parquet-loaded DataFrame to EventLog"""
        import pm4py

        config = parse_yaml(minimal_config_yaml)
        df = generate_log(config, seed=42, num_cases=10)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "events.parquet"
            export_parquet(df, output_path)
            df_imported = pd.read_parquet(str(output_path))
            df_formatted = pm4py.format_dataframe(
                df_imported,
                case_id='case:concept:name',
                activity_key='concept:name',
                timestamp_key='time:timestamp'
            )

            # Convert to EventLog
            event_log = pm4py.convert_to_event_log(df_formatted)

            assert event_log is not None
            assert len(event_log) > 0
            assert len(event_log) == 10

    def test_pm4py_discover_dfg_parquet(self, minimal_config_yaml):
        """Test PM4Py can discover DFG from Parquet-loaded log"""
        import pm4py

        config = parse_yaml(minimal_config_yaml)
        df = generate_log(config, seed=42, num_cases=10)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "events.parquet"
            export_parquet(df, output_path)
            df_imported = pd.read_parquet(str(output_path))
            df_formatted = pm4py.format_dataframe(
                df_imported,
                case_id='case:concept:name',
                activity_key='concept:name',
                timestamp_key='time:timestamp'
            )
            event_log = pm4py.convert_to_event_log(df_formatted)

            # Discover DFG
            dfg, start_activities, end_activities = pm4py.discover_dfg(event_log)

            assert dfg is not None
            assert isinstance(dfg, dict)
            assert len(dfg) > 0

            assert start_activities is not None
            assert len(start_activities) > 0

            assert end_activities is not None
            assert len(end_activities) > 0

    def test_pm4py_csv_parquet_equivalence(self, minimal_config_yaml):
        """Test that CSV and Parquet produce identical PM4Py EventLogs"""
        import pm4py

        config = parse_yaml(minimal_config_yaml)
        df = generate_log(config, seed=42, num_cases=10)

        with tempfile.TemporaryDirectory() as tmpdir:
            # Export to both formats
            csv_path = Path(tmpdir) / "events.csv"
            parquet_path = Path(tmpdir) / "events.parquet"
            export_csv(df, csv_path)
            export_parquet(df, parquet_path)

            # Load CSV
            df_csv = pd.read_csv(str(csv_path))
            df_csv_formatted = pm4py.format_dataframe(
                df_csv,
                case_id='case:concept:name',
                activity_key='concept:name',
                timestamp_key='time:timestamp'
            )
            log_csv = pm4py.convert_to_event_log(df_csv_formatted)

            # Load Parquet
            df_parquet = pd.read_parquet(str(parquet_path))
            df_parquet_formatted = pm4py.format_dataframe(
                df_parquet,
                case_id='case:concept:name',
                activity_key='concept:name',
                timestamp_key='time:timestamp'
            )
            log_parquet = pm4py.convert_to_event_log(df_parquet_formatted)

            # Both should have same number of cases and events
            assert len(log_csv) == len(log_parquet)

            # Total events should match
            csv_events = sum(len(trace) for trace in log_csv)
            parquet_events = sum(len(trace) for trace in log_parquet)
            assert csv_events == parquet_events


class TestPM4PyJsonImport:
    """Test PM4Py can import generated JSON files"""

    def test_pandas_read_json(self, minimal_config_yaml):
        """Test pandas can read generated JSON files"""
        config = parse_yaml(minimal_config_yaml)
        df = generate_log(config, seed=42, num_cases=10)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "events.json"
            export_json(df, output_path)

            # Read JSON with pandas (NDJSON format)
            df_imported = pd.read_json(str(output_path), lines=True)

            assert df_imported is not None
            assert len(df_imported) > 0
            assert "case:concept:name" in df_imported.columns
            assert "concept:name" in df_imported.columns
            assert "time:timestamp" in df_imported.columns

    def test_pm4py_format_dataframe_json(self, minimal_config_yaml):
        """Test PM4Py format_dataframe accepts JSON-loaded DataFrame"""
        import pm4py

        config = parse_yaml(minimal_config_yaml)
        df = generate_log(config, seed=42, num_cases=10)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "events.json"
            export_json(df, output_path)
            df_imported = pd.read_json(str(output_path), lines=True)

            # PM4Py should be able to format the DataFrame
            df_formatted = pm4py.format_dataframe(
                df_imported,
                case_id='case:concept:name',
                activity_key='concept:name',
                timestamp_key='time:timestamp'
            )

            assert df_formatted is not None
            assert len(df_formatted) > 0
            # Check PM4Py added index columns
            assert '@@index' in df_formatted.columns or '@@case_index' in df_formatted.columns

    def test_pm4py_convert_to_event_log_json(self, minimal_config_yaml):
        """Test PM4Py can convert JSON-loaded DataFrame to EventLog"""
        import pm4py

        config = parse_yaml(minimal_config_yaml)
        df = generate_log(config, seed=42, num_cases=10)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "events.json"
            export_json(df, output_path)
            df_imported = pd.read_json(str(output_path), lines=True)
            df_formatted = pm4py.format_dataframe(
                df_imported,
                case_id='case:concept:name',
                activity_key='concept:name',
                timestamp_key='time:timestamp'
            )

            # Convert to EventLog
            event_log = pm4py.convert_to_event_log(df_formatted)

            assert event_log is not None
            assert len(event_log) > 0
            assert len(event_log) == 10

    def test_pm4py_discover_dfg_json(self, minimal_config_yaml):
        """Test PM4Py can discover DFG from JSON-loaded log"""
        import pm4py

        config = parse_yaml(minimal_config_yaml)
        df = generate_log(config, seed=42, num_cases=10)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "events.json"
            export_json(df, output_path)
            df_imported = pd.read_json(str(output_path), lines=True)
            df_formatted = pm4py.format_dataframe(
                df_imported,
                case_id='case:concept:name',
                activity_key='concept:name',
                timestamp_key='time:timestamp'
            )
            event_log = pm4py.convert_to_event_log(df_formatted)

            # Discover DFG
            dfg, start_activities, end_activities = pm4py.discover_dfg(event_log)

            assert dfg is not None
            assert isinstance(dfg, dict)
            assert len(dfg) > 0

            assert start_activities is not None
            assert len(start_activities) > 0

            assert end_activities is not None
            assert len(end_activities) > 0
