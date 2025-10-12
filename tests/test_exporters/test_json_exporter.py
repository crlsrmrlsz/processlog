"""
Tests for JSON exporter module
"""

import pytest
import pandas as pd
import json
from pathlib import Path
from datetime import datetime
import tempfile

from processlog.exporters.json_exporter import export_json
from processlog.exporters.csv_exporter import ExportError


class TestExportJson:
    """Tests for export_json function"""

    def test_export_json_basic(self):
        """Test basic JSON export"""
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
            output_path = Path(tmpdir) / "test_output.json"
            export_json(df_internal, output_path)

            # Check file was created
            assert output_path.exists()

            # Read back and verify (NDJSON format)
            with open(output_path, "r") as f:
                lines = f.readlines()
                assert len(lines) == 2  # Two events

                # Parse first line
                event1 = json.loads(lines[0])
                assert "case:concept:name" in event1
                assert "concept:name" in event1
                assert "time:timestamp" in event1

    def test_export_json_ndjson_format(self):
        """Test that JSON export uses NDJSON format (one object per line)"""
        df_internal = pd.DataFrame(
            {
                "case_id": ["case_001", "case_002", "case_003"],
                "activity": ["start", "start", "start"],
                "timestamp": [
                    datetime(2024, 1, 1, 9, 0, 0),
                    datetime(2024, 1, 1, 9, 30, 0),
                    datetime(2024, 1, 1, 10, 0, 0),
                ],
                "resource": [None, None, None],
                "lifecycle": ["complete", "complete", "complete"],
            }
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_output.json"
            export_json(df_internal, output_path)

            # Read as NDJSON
            with open(output_path, "r") as f:
                lines = f.readlines()
                assert len(lines) == 3  # Three events

                # Each line should be valid JSON
                for line in lines:
                    event = json.loads(line)
                    assert isinstance(event, dict)

    def test_export_json_creates_directory(self):
        """Test that export_json creates output directory if it doesn't exist"""
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
            output_path = Path(tmpdir) / "subdir" / "test_output.json"
            export_json(df_internal, output_path)

            # Check file was created
            assert output_path.exists()

    def test_export_json_with_custom_attributes(self):
        """Test JSON export with custom attributes"""
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
            output_path = Path(tmpdir) / "test_output.json"
            export_json(df_internal, output_path)

            # Read back and verify custom attributes
            with open(output_path, "r") as f:
                event = json.loads(f.readline())

            assert "cost:amount" in event
            assert "org:department" in event
            assert event["cost:amount"] == 50.0
            assert event["org:department"] == "Legal"

    def test_export_json_preserves_chronological_order(self):
        """Test that JSON export preserves chronological order"""
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
            output_path = Path(tmpdir) / "test_output.json"
            export_json(df_internal, output_path)

            # Read back
            with open(output_path, "r") as f:
                lines = f.readlines()
                events = [json.loads(line) for line in lines]

            # First event should be case_001 start
            assert events[0]["case:concept:name"] == "case_001"
            assert events[0]["concept:name"] == "start"

    def test_export_json_timestamp_format(self):
        """Test that JSON export formats timestamps correctly"""
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
            output_path = Path(tmpdir) / "test_output.json"
            export_json(df_internal, output_path)

            # Read back
            with open(output_path, "r") as f:
                event = json.loads(f.readline())

            # Check timestamp format (should be ISO format string)
            assert "time:timestamp" in event
            assert isinstance(event["time:timestamp"], str)
            # Should be in format "YYYY-MM-DD HH:MM:SS"
            assert event["time:timestamp"] == "2024-01-01 09:00:00"

    def test_export_json_empty_dataframe(self):
        """Test exporting empty DataFrame"""
        df_internal = pd.DataFrame(
            columns=["case_id", "activity", "timestamp", "resource", "lifecycle"]
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_output.json"
            export_json(df_internal, output_path)

            # File should exist but be empty
            assert output_path.exists()

            with open(output_path, "r") as f:
                content = f.read()
                # Empty DataFrame should produce empty file or minimal content
                assert len(content.strip()) == 0 or content.strip() == ""

    def test_export_json_schema_mapping(self):
        """Test that JSON export uses PM4Py schema"""
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
            output_path = Path(tmpdir) / "test_output.json"
            export_json(df_internal, output_path)

            # Read back
            with open(output_path, "r") as f:
                event = json.loads(f.readline())

            # Check PM4Py field names
            assert "case:concept:name" in event
            assert "concept:name" in event
            assert "time:timestamp" in event
            assert "org:resource" in event
            assert "lifecycle:transition" in event

            # Check old names are gone
            assert "case_id" not in event
            assert "activity" not in event

    def test_export_json_data_preservation(self):
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
            output_path = Path(tmpdir) / "test_output.json"
            export_json(df_internal, output_path)

            # Read back
            with open(output_path, "r") as f:
                event = json.loads(f.readline())

            assert event["case:concept:name"] == "case_001"
            assert event["concept:name"] == "review"
            assert event["org:resource"] == "reviewer_001"
            assert event["lifecycle:transition"] == "complete"

    def test_export_json_handles_null_values(self):
        """Test that JSON export handles null/None values correctly"""
        df_internal = pd.DataFrame(
            {
                "case_id": ["case_001"],
                "activity": ["start"],
                "timestamp": [datetime(2024, 1, 1, 9, 0, 0)],
                "resource": [None],  # Null value
                "lifecycle": ["complete"],
            }
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_output.json"
            export_json(df_internal, output_path)

            # Read back
            with open(output_path, "r") as f:
                event = json.loads(f.readline())

            # Null should be preserved as null in JSON
            assert event["org:resource"] is None
