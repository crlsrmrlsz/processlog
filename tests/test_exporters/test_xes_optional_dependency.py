"""
Tests for XES export's optional-dependency (pm4py) handling.

pm4py is an optional extra (``processlog[xes]``). These tests verify the lazy
import and its actionable error message WITHOUT requiring pm4py to be
installed — they simulate its absence, so they run on the lean core venv too.
"""

import sys
import tempfile
from datetime import datetime
from pathlib import Path

import pandas as pd
import pytest

from processlog.exporters.csv_exporter import ExportError
from processlog.exporters.xes_exporter import export_xes


def _sample_df() -> pd.DataFrame:
    return pd.DataFrame(
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


def test_export_xes_without_pm4py_raises_actionable_error(monkeypatch):
    """When pm4py is absent, export_xes raises a clear ExportError naming the
    processlog[xes] extra — not a raw ImportError."""
    # Setting a module to None in sys.modules makes `import pm4py` raise
    # ImportError, regardless of whether pm4py is actually installed.
    monkeypatch.setitem(sys.modules, "pm4py", None)

    with tempfile.TemporaryDirectory() as tmpdir:
        with pytest.raises(ExportError, match=r"processlog\[xes\]"):
            export_xes(_sample_df(), Path(tmpdir) / "events.xes")
