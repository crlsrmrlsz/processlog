"""
Tests for CSV exporter module
"""

import pytest
import pandas as pd
from pathlib import Path
from datetime import datetime
import tempfile

from processlog.exporters.csv_exporter import (
    export_csv,
    ExportError,
    get_pm4py_column_names,
    _map_schema,
)


class TestGetPM4PyColumnNames:
    """Tests for get_pm4py_column_names function"""

    def test_get_pm4py_column_names(self):
        """Test getting PM4Py column name mapping"""
        mapping = get_pm4py_column_names()

        assert mapping["case_id"] == "case:concept:name"
        assert mapping["activity"] == "concept:name"
        assert mapping["timestamp"] == "time:timestamp"
        assert mapping["resource"] == "org:resource"
        assert mapping["lifecycle"] == "lifecycle:transition"

    def test_get_pm4py_column_names_returns_copy(self):
        """Test that function returns a copy (not reference)"""
        mapping1 = get_pm4py_column_names()
        mapping2 = get_pm4py_column_names()

        # Modify mapping1
        mapping1["case_id"] = "modified"

        # mapping2 should not be affected
        assert mapping2["case_id"] == "case:concept:name"


class TestMapSchema:
    """Tests for _map_schema function"""

    def test_map_schema_basic(self):
        """Test basic schema mapping"""
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

        df_mapped = _map_schema(df_internal)

        # Check that columns were renamed
        assert "case:concept:name" in df_mapped.columns
        assert "concept:name" in df_mapped.columns
        assert "time:timestamp" in df_mapped.columns
        assert "org:resource" in df_mapped.columns
        assert "lifecycle:transition" in df_mapped.columns

        # Check that old column names are gone
        assert "case_id" not in df_mapped.columns
        assert "activity" not in df_mapped.columns

    def test_map_schema_preserves_data(self):
        """Test that schema mapping preserves data"""
        df_internal = pd.DataFrame(
            {
                "case_id": ["case_001"],
                "activity": ["review"],
                "timestamp": [datetime(2024, 1, 1, 9, 0, 0)],
                "resource": ["reviewer_001"],
                "lifecycle": ["complete"],
            }
        )

        df_mapped = _map_schema(df_internal)

        assert df_mapped["case:concept:name"].iloc[0] == "case_001"
        assert df_mapped["concept:name"].iloc[0] == "review"
        assert df_mapped["org:resource"].iloc[0] == "reviewer_001"

    def test_map_schema_with_custom_attributes(self):
        """Test schema mapping with custom attributes"""
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

        df_mapped = _map_schema(df_internal)

        # Standard columns mapped
        assert "case:concept:name" in df_mapped.columns
        # Custom attributes preserved
        assert "cost:amount" in df_mapped.columns
        assert "org:department" in df_mapped.columns
        assert df_mapped["cost:amount"].iloc[0] == 50.0

    def test_map_schema_chronological_ordering(self):
        """Test that schema mapping ensures chronological ordering"""
        df_internal = pd.DataFrame(
            {
                "case_id": ["case_001", "case_001", "case_002", "case_002"],
                "activity": ["end", "start", "end", "start"],
                "timestamp": [
                    datetime(2024, 1, 1, 10, 0, 0),
                    datetime(2024, 1, 1, 9, 0, 0),
                    datetime(2024, 1, 1, 11, 0, 0),
                    datetime(2024, 1, 1, 9, 30, 0),
                ],
                "resource": [None, None, None, None],
                "lifecycle": ["complete", "complete", "complete", "complete"],
            }
        )

        df_mapped = _map_schema(df_internal)

        # Check ordering: case_001 events should be start, end
        case_001_df = df_mapped[df_mapped["case:concept:name"] == "case_001"]
        assert case_001_df.iloc[0]["concept:name"] == "start"
        assert case_001_df.iloc[1]["concept:name"] == "end"


class TestExportCsv:
    """Tests for export_csv function"""

    def test_export_csv_basic(self):
        """Test basic CSV export"""
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
            output_path = Path(tmpdir) / "test_output.csv"
            export_csv(df_internal, output_path)

            # Check file was created
            assert output_path.exists()

            # Read back and verify
            df_read = pd.read_csv(output_path)

            assert "case:concept:name" in df_read.columns
            assert "concept:name" in df_read.columns
            assert len(df_read) == 2

    def test_export_csv_creates_directory(self):
        """Test that export_csv creates output directory if it doesn't exist"""
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
            output_path = Path(tmpdir) / "subdir" / "test_output.csv"
            export_csv(df_internal, output_path)

            # Check file was created
            assert output_path.exists()

    def test_export_csv_with_custom_attributes(self):
        """Test CSV export with custom attributes"""
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
            output_path = Path(tmpdir) / "test_output.csv"
            export_csv(df_internal, output_path)

            # Read back and verify custom attributes
            df_read = pd.read_csv(output_path)

            assert "cost:amount" in df_read.columns
            assert "org:department" in df_read.columns
            assert df_read["cost:amount"].iloc[0] == 50.0

    def test_export_csv_no_header(self):
        """Test CSV export without header"""
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
            output_path = Path(tmpdir) / "test_output.csv"
            export_csv(df_internal, output_path, include_header=False)

            # Read file content
            with open(output_path, "r") as f:
                content = f.read()

            # Should not start with column names
            assert not content.startswith("case:concept:name")

    def test_export_csv_preserves_chronological_order(self):
        """Test that CSV export preserves chronological order"""
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
            output_path = Path(tmpdir) / "test_output.csv"
            export_csv(df_internal, output_path)

            # Read back
            df_read = pd.read_csv(output_path)

            # First row should be case_001 start
            assert df_read.iloc[0]["case:concept:name"] == "case_001"
            assert df_read.iloc[0]["concept:name"] == "start"

    def test_export_csv_empty_dataframe(self):
        """Test exporting empty DataFrame"""
        df_internal = pd.DataFrame(
            columns=["case_id", "activity", "timestamp", "resource", "lifecycle"]
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_output.csv"
            export_csv(df_internal, output_path)

            # File should exist but be empty (except header)
            assert output_path.exists()

            df_read = pd.read_csv(output_path)
            assert len(df_read) == 0
            assert "case:concept:name" in df_read.columns
