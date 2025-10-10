"""
Event Log Generator - Synthetic process event log generator from YAML configuration.

This package provides tools to generate realistic synthetic event logs for process mining
analysis, with full PM4Py and XES 1849-2023 standard compatibility.
"""

__version__ = "1.0.0"
__author__ = "Karl Romer"

from event_log_gen.config.loader import load_config
from event_log_gen.config.validator import validate_config
from event_log_gen.core.generator import generate_log
from event_log_gen.exporters.csv_exporter import export_csv
from event_log_gen.exporters.parquet_exporter import export_parquet
from event_log_gen.exporters.json_exporter import export_json
from event_log_gen.exporters.xes_exporter import export_xes

__all__ = [
    "load_config",
    "validate_config",
    "generate_log",
    "export_csv",
    "export_parquet",
    "export_json",
    "export_xes",
    "__version__",
]
