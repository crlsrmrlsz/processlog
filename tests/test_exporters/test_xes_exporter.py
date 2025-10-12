"""
Tests for XES exporter module
"""

import pytest
import pandas as pd
import pm4py
from pathlib import Path
from datetime import datetime
import tempfile

from processlog.exporters.xes_exporter import export_xes
from processlog.exporters.csv_exporter import ExportError


class TestExportXes:
    """Tests for export_xes function"""

    def test_export_xes_basic(self):
        """Test basic XES export"""
        df_internal = pd.DataFrame(
            {
                "case_id": ["case_001", "case_001"],
                "activity": ["start", "end"],
                "timestamp": [
                    datetime(2024, 1, 1, 9, 0, 0),
                    datetime(2024, 1, 1, 10, 0, 0),
                ],
                "resource": [None, "clerk_001"],
                "lifecycle": ["complete", "complete"],
            }
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_output.xes"
            export_xes(df_internal, output_path)

            # Check file was created
            assert output_path.exists()

            # Verify file is readable by PM4Py
            log_read = pm4py.read_xes(str(output_path))
            assert log_read is not None
            assert len(log_read) > 0  # Should have traces

    def test_export_xes_creates_directory(self):
        """Test that export_xes creates output directory if it doesn't exist"""
        df_internal = pd.DataFrame(
            {
                "case_id": ["case_001"],
                "activity": ["start"],
                "timestamp": [datetime(2024, 1, 1, 9, 0, 0)],
                "resource": [None],
                "lifecycle": ["complete"],
            }
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "subdir" / "test_output.xes"
            export_xes(df_internal, output_path)

            # Check file was created
            assert output_path.exists()

    def test_export_xes_with_custom_attributes(self):
        """Test XES export with custom attributes"""
        df_internal = pd.DataFrame(
            {
                "case_id": ["case_001"],
                "activity": ["review"],
                "timestamp": [datetime(2024, 1, 1, 9, 0, 0)],
                "resource": ["reviewer_001"],
                "lifecycle": ["complete"],
                "cost:amount": [50.0],
                "org:department": ["Legal"],
            }
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_output.xes"
            export_xes(df_internal, output_path)

            # Read back
            log_read = pm4py.read_xes(str(output_path))
            assert log_read is not None

            # Check that the log has the expected case
            assert len(log_read) == 1

    def test_export_xes_preserves_chronological_order(self):
        """Test that XES export preserves chronological order"""
        df_internal = pd.DataFrame(
            {
                "case_id": ["case_001", "case_001", "case_002", "case_002"],
                "activity": ["start", "end", "start", "end"],
                "timestamp": [
                    datetime(2024, 1, 1, 9, 0, 0),
                    datetime(2024, 1, 1, 10, 0, 0),
                    datetime(2024, 1, 1, 9, 30, 0),
                    datetime(2024, 1, 1, 11, 0, 0),
                ],
                "resource": [None, None, None, None],
                "lifecycle": ["complete", "complete", "complete", "complete"],
            }
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_output.xes"
            export_xes(df_internal, output_path)

            # Read back (returns DataFrame)
            df_read = pm4py.read_xes(str(output_path))

            # Should have 4 events total
            assert len(df_read) == 4

            # Should have 2 unique cases
            assert len(df_read["case:concept:name"].unique()) == 2

            # First case events should be in order
            case_001 = df_read[df_read["case:concept:name"] == "case_001"]
            assert case_001.iloc[0]["concept:name"] == "start"
            assert case_001.iloc[1]["concept:name"] == "end"

    def test_export_xes_readable_by_pm4py(self):
        """Test that exported XES is readable by PM4Py"""
        df_internal = pd.DataFrame(
            {
                "case_id": ["case_001", "case_001"],
                "activity": ["start", "end"],
                "timestamp": [
                    datetime(2024, 1, 1, 9, 0, 0),
                    datetime(2024, 1, 1, 10, 0, 0),
                ],
                "resource": ["clerk_001", "clerk_001"],
                "lifecycle": ["complete", "complete"],
            }
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_output.xes"
            export_xes(df_internal, output_path)

            # PM4Py should be able to read it
            log_read = pm4py.read_xes(str(output_path))

            # Convert to DataFrame to verify content
            df_read = pm4py.convert_to_dataframe(log_read)

            assert "case:concept:name" in df_read.columns
            assert "concept:name" in df_read.columns
            assert "time:timestamp" in df_read.columns

    def test_export_xes_data_preservation(self):
        """Test that data values are preserved correctly"""
        df_internal = pd.DataFrame(
            {
                "case_id": ["case_001"],
                "activity": ["review"],
                "timestamp": [datetime(2024, 1, 1, 9, 0, 0)],
                "resource": ["reviewer_001"],
                "lifecycle": ["complete"],
            }
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_output.xes"
            export_xes(df_internal, output_path)

            # Read back
            log_read = pm4py.read_xes(str(output_path))
            df_read = pm4py.convert_to_dataframe(log_read)

            assert df_read["case:concept:name"].iloc[0] == "case_001"
            assert df_read["concept:name"].iloc[0] == "review"
            assert df_read["org:resource"].iloc[0] == "reviewer_001"

    def test_export_xes_multiple_cases(self):
        """Test XES export with multiple cases"""
        df_internal = pd.DataFrame(
            {
                "case_id": ["case_001", "case_001", "case_002", "case_002", "case_003"],
                "activity": ["start", "end", "start", "end", "start"],
                "timestamp": [
                    datetime(2024, 1, 1, 9, 0, 0),
                    datetime(2024, 1, 1, 10, 0, 0),
                    datetime(2024, 1, 1, 9, 30, 0),
                    datetime(2024, 1, 1, 11, 0, 0),
                    datetime(2024, 1, 1, 10, 30, 0),
                ],
                "resource": [None, None, None, None, None],
                "lifecycle": ["complete", "complete", "complete", "complete", "complete"],
            }
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_output.xes"
            export_xes(df_internal, output_path)

            # Read back (returns DataFrame)
            df_read = pm4py.read_xes(str(output_path))

            # Should have 5 events total
            assert len(df_read) == 5

            # Should have 3 unique cases
            assert len(df_read["case:concept:name"].unique()) == 3

            # Verify event counts per case
            case_001 = df_read[df_read["case:concept:name"] == "case_001"]
            case_002 = df_read[df_read["case:concept:name"] == "case_002"]
            case_003 = df_read[df_read["case:concept:name"] == "case_003"]

            assert len(case_001) == 2
            assert len(case_002) == 2
            assert len(case_003) == 1

    def test_export_xes_schema_compliance(self):
        """Test that XES export uses correct XES schema"""
        df_internal = pd.DataFrame(
            {
                "case_id": ["case_001"],
                "activity": ["start"],
                "timestamp": [datetime(2024, 1, 1, 9, 0, 0)],
                "resource": ["clerk_001"],
                "lifecycle": ["complete"],
            }
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_output.xes"
            export_xes(df_internal, output_path)

            # Read and convert back to DataFrame
            log_read = pm4py.read_xes(str(output_path))
            df_read = pm4py.convert_to_dataframe(log_read)

            # Check XES standard column names
            assert "case:concept:name" in df_read.columns
            assert "concept:name" in df_read.columns
            assert "time:timestamp" in df_read.columns
            assert "org:resource" in df_read.columns
            assert "lifecycle:transition" in df_read.columns

    def test_export_xes_pm4py_process_discovery(self):
        """Test that XES export can be used for PM4Py process discovery"""
        df_internal = pd.DataFrame(
            {
                "case_id": ["case_001", "case_001", "case_002", "case_002"],
                "activity": ["start", "end", "start", "end"],
                "timestamp": [
                    datetime(2024, 1, 1, 9, 0, 0),
                    datetime(2024, 1, 1, 10, 0, 0),
                    datetime(2024, 1, 1, 9, 30, 0),
                    datetime(2024, 1, 1, 11, 0, 0),
                ],
                "resource": [None, None, None, None],
                "lifecycle": ["complete", "complete", "complete", "complete"],
            }
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_output.xes"
            export_xes(df_internal, output_path)

            # Read back
            log_read = pm4py.read_xes(str(output_path))
            event_log = pm4py.convert_to_event_log(log_read)

            # Should be able to discover DFG
            dfg, start_activities, end_activities = pm4py.discover_dfg(event_log)

            assert dfg is not None
            assert len(start_activities) > 0
            assert len(end_activities) > 0
