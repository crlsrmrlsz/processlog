"""
JSON exporter module

Exports event logs to JSON format (NDJSON/JSON Lines) with PM4Py-compatible field names.
NDJSON format: one JSON object per line, compatible with PM4Py's NDJSON reader.
"""

from pathlib import Path

import pandas as pd

from .csv_exporter import SCHEMA_MAPPING, ExportError, _map_schema


def export_json(df: pd.DataFrame, output_path: str | Path, orient: str = "records") -> None:
    """
    Export DataFrame to NDJSON (JSON Lines) with PM4Py-compatible field names

    Args:
        df: DataFrame with internal schema (case_id, activity, timestamp, resource, lifecycle)
        output_path: Path to output JSON file
        orient: JSON orientation format (default: 'records' for NDJSON)
                'records': list of JSON objects (one per event)
                This is the format compatible with PM4Py

    Raises:
        ExportError: If export fails

    Example:
        >>> from processlog.core.generator import generate_log
        >>> from processlog.config import load_config
        >>> config = load_config('configs/process_config.yaml')
        >>> df = generate_log(config, seed=42, num_cases=10)
        >>> export_json(df, 'output/events.json')
    """
    output_path = Path(output_path)

    # Create output directory if it doesn't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Map column names to PM4Py/XES format
    try:
        df_export = _map_schema(df)
    except Exception as e:
        raise ExportError(f"Failed to map schema: {e}") from e

    # Export to JSON (NDJSON format)
    try:
        # Serialize timestamps the same way the CSV exporter does (pandas'
        # native datetime->str): tz-aware values keep their offset
        # (e.g. "2024-01-01 09:00:00-05:00") AND sub-second precision is
        # preserved (microseconds when present), so JSON and CSV are
        # byte-identical. The previous strftime format had no "%f" directive,
        # which floored every timestamp to whole seconds and silently lost the
        # microseconds the generator produces (durations are float hours).
        if "time:timestamp" in df_export.columns:
            df_export["time:timestamp"] = df_export["time:timestamp"].astype(str)

        # Write as NDJSON (one JSON object per line)
        df_export.to_json(output_path, orient=orient, lines=True, date_format="iso")
    except Exception as e:
        raise ExportError(f"Failed to write JSON file '{output_path}': {e}") from e
