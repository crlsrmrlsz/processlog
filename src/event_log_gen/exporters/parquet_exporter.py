"""
Parquet exporter module

Exports event logs to Parquet format with PM4Py-compatible column names.
"""

from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from .csv_exporter import SCHEMA_MAPPING, ExportError, _map_schema


def export_parquet(df: pd.DataFrame, output_path: str | Path) -> None:
    """
    Export DataFrame to Parquet with PM4Py-compatible column names

    Args:
        df: DataFrame with internal schema (case_id, activity, timestamp, resource, lifecycle)
        output_path: Path to output Parquet file

    Raises:
        ExportError: If export fails

    Example:
        >>> from event_log_gen.core.generator import generate_log
        >>> from event_log_gen.config import load_config
        >>> config = load_config('configs/process_config.yaml')
        >>> df = generate_log(config, seed=42, num_cases=10)
        >>> export_parquet(df, 'output/events.parquet')
    """
    output_path = Path(output_path)

    # Create output directory if it doesn't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Map column names to PM4Py/XES format
    try:
        df_export = _map_schema(df)
    except Exception as e:
        raise ExportError(f"Failed to map schema: {e}") from e

    # Export to Parquet
    try:
        # Convert timestamp column to datetime if it's a string
        if "time:timestamp" in df_export.columns:
            df_export["time:timestamp"] = pd.to_datetime(df_export["time:timestamp"])

        # Write parquet file
        table = pa.Table.from_pandas(df_export)
        pq.write_table(table, output_path)
    except Exception as e:
        raise ExportError(f"Failed to write Parquet file '{output_path}': {e}") from e
