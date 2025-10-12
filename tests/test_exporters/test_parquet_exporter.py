"""
Tests for Parquet exporter module
"""

import pytest
import pandas as pd
from pathlib import Path
from datetime import datetime
import tempfile

from processlog.exporters.parquet_exporter import export_parquet
from processlog.exporters.csv_exporter import ExportError


class TestExportParquet:
    """Tests for export_parquet function"""

    def test_export_parquet_basic(self):
        """Test basic Parquet export"""
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
            output_path = Path(tmpdir) / "test_output.parquet"
            export_parquet(df_internal, output_path)

            # Check file was created
            assert output_path.exists()

            # Read back and verify
            df_read = pd.read_parquet(output_path)

            assert "case:concept:name" in df_read.columns
            assert "concept:name" in df_read.columns
            assert "time:timestamp" in df_read.columns
            assert len(df_read) == 2

    def test_export_parquet_creates_directory(self):
        """Test that export_parquet creates output directory if it doesn't exist"""
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
            output_path = Path(tmpdir) / "subdir" / "test_output.parquet"
            export_parquet(df_internal, output_path)

            # Check file was created
            assert output_path.exists()

    def test_export_parquet_with_custom_attributes(self):
        """Test Parquet export with custom attributes"""
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
            output_path = Path(tmpdir) / "test_output.parquet"
            export_parquet(df_internal, output_path)

            # Read back and verify custom attributes
            df_read = pd.read_parquet(output_path)

            assert "cost:amount" in df_read.columns
            assert "org:department" in df_read.columns
            assert df_read["cost:amount"].iloc[0] == 50.0

    def test_export_parquet_preserves_chronological_order(self):
        """Test that Parquet export preserves chronological order"""
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
            output_path = Path(tmpdir) / "test_output.parquet"
            export_parquet(df_internal, output_path)

            # Read back
            df_read = pd.read_parquet(output_path)

            # First row should be case_001 start
            assert df_read.iloc[0]["case:concept:name"] == "case_001"
            assert df_read.iloc[0]["concept:name"] == "start"

    def test_export_parquet_timestamp_format(self):
        """Test that Parquet export converts timestamps to datetime"""
        df_internal = pd.DataFrame(
            {
                "case_id": ["case_001"],
                "activity": ["start"],
                "timestamp": ["2024-01-01 09:00:00"],  # String timestamp
                "resource": [None],
                "lifecycle": ["complete"],
            }
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_output.parquet"
            export_parquet(df_internal, output_path)

            # Read back
            df_read = pd.read_parquet(output_path)

            # Check timestamp is datetime
            assert pd.api.types.is_datetime64_any_dtype(df_read["time:timestamp"])

    def test_export_parquet_empty_dataframe(self):
        """Test exporting empty DataFrame"""
        df_internal = pd.DataFrame(
            columns=["case_id", "activity", "timestamp", "resource", "lifecycle"]
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_output.parquet"
            export_parquet(df_internal, output_path)

            # File should exist but be empty
            assert output_path.exists()

            df_read = pd.read_parquet(output_path)
            assert len(df_read) == 0
            assert "case:concept:name" in df_read.columns

    def test_export_parquet_preserves_data_types(self):
        """Test that Parquet preserves data types correctly"""
        df_internal = pd.DataFrame(
            {
                "case_id": ["case_001"],
                "activity": ["review"],
                "timestamp": [datetime(2024, 1, 1, 9, 0, 0)],
                "resource": ["reviewer_001"],
                "lifecycle": ["complete"],
                "cost:amount": [50.0],
            }
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_output.parquet"
            export_parquet(df_internal, output_path)

            # Read back
            df_read = pd.read_parquet(output_path)

            # Check data types
            assert df_read["case:concept:name"].dtype == object  # string
            assert df_read["cost:amount"].dtype == float

    def test_export_parquet_schema_mapping(self):
        """Test that Parquet export uses PM4Py schema"""
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
            output_path = Path(tmpdir) / "test_output.parquet"
            export_parquet(df_internal, output_path)

            # Read back
            df_read = pd.read_parquet(output_path)

            # Check PM4Py column names
            assert "case:concept:name" in df_read.columns
            assert "concept:name" in df_read.columns
            assert "time:timestamp" in df_read.columns
            assert "org:resource" in df_read.columns
            assert "lifecycle:transition" in df_read.columns

            # Check old names are gone
            assert "case_id" not in df_read.columns
            assert "activity" not in df_read.columns

    def test_export_parquet_data_preservation(self):
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
            output_path = Path(tmpdir) / "test_output.parquet"
            export_parquet(df_internal, output_path)

            # Read back
            df_read = pd.read_parquet(output_path)

            assert df_read["case:concept:name"].iloc[0] == "case_001"
            assert df_read["concept:name"].iloc[0] == "review"
            assert df_read["org:resource"].iloc[0] == "reviewer_001"
