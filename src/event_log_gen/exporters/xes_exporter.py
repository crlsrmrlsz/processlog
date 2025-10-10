"""
XES exporter module

Exports event logs to XES format (IEEE XES 1849-2023 standard) using PM4Py.
"""

from pathlib import Path

import pandas as pd
import pm4py

from .csv_exporter import SCHEMA_MAPPING, ExportError, _map_schema


def export_xes(df: pd.DataFrame, output_path: str | Path) -> None:
    """
    Export DataFrame to XES format using PM4Py

    XES (eXtensible Event Stream) is the IEEE standard format for event logs.
    This function uses PM4Py's write_xes to ensure full XES compliance.

    Args:
        df: DataFrame with internal schema (case_id, activity, timestamp, resource, lifecycle)
        output_path: Path to output XES file

    Raises:
        ExportError: If export fails

    Example:
        >>> from event_log_gen.core.generator import generate_log
        >>> from event_log_gen.config import load_config
        >>> config = load_config('configs/process_config.yaml')
        >>> df = generate_log(config, seed=42, num_cases=10)
        >>> export_xes(df, 'output/events.xes')
    """
    output_path = Path(output_path)

    # Create output directory if it doesn't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Map column names to PM4Py/XES format
    try:
        df_export = _map_schema(df)
    except Exception as e:
        raise ExportError(f"Failed to map schema: {e}") from e

    # Export to XES using PM4Py
    try:
        # Convert timestamp to datetime if it's a string
        if "time:timestamp" in df_export.columns:
            df_export["time:timestamp"] = pd.to_datetime(df_export["time:timestamp"])

        # Format DataFrame for PM4Py
        df_formatted = pm4py.format_dataframe(
            df_export,
            case_id='case:concept:name',
            activity_key='concept:name',
            timestamp_key='time:timestamp'
        )

        # Convert to EventLog (required by write_xes)
        event_log = pm4py.convert_to_event_log(df_formatted)

        # Write XES file
        pm4py.write_xes(event_log, str(output_path))
    except Exception as e:
        raise ExportError(f"Failed to write XES file '{output_path}': {e}") from e
