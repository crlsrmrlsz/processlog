"""
Event Log Generator - Synthetic process event log generator from YAML configuration.

This package provides tools to generate realistic synthetic event logs for process mining
analysis, with full PM4Py and XES 1849-2023 standard compatibility.
"""

__version__ = "1.0.0"
__author__ = "Karl Romer"

from processlog.config.loader import load_config
from processlog.config.validator import validate_config
from processlog.core.generator import generate_log
from processlog.exporters.csv_exporter import export_csv
from processlog.exporters.parquet_exporter import export_parquet
from processlog.exporters.json_exporter import export_json
from processlog.exporters.xes_exporter import export_xes
from processlog.exporters.metadata import export_metadata

__all__ = [
    "load_config",
    "validate_config",
    "generate_log",
    "export_csv",
    "export_parquet",
    "export_json",
    "export_xes",
    "export_metadata",
    "__version__",
]
