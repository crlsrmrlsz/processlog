"""
CSV exporter module

Exports event logs to CSV format with PM4Py-compatible column names.
"""

from pathlib import Path
from typing import Dict

import pandas as pd


# Schema mapping: internal names → PM4Py/XES names
SCHEMA_MAPPING = {
    "case_id": "case:concept:name",
    "activity": "concept:name",
    "timestamp": "time:timestamp",
    "resource": "org:resource",
    "lifecycle": "lifecycle:transition",
}


class ExportError(Exception):
    """Raised when export fails"""

    pass


def export_csv(df: pd.DataFrame, output_path: str | Path, include_header: bool = True) -> None:
    """
    Export DataFrame to CSV with PM4Py-compatible column names

    Args:
        df: DataFrame with internal schema (case_id, activity, timestamp, resource, lifecycle)
        output_path: Path to output CSV file
        include_header: Whether to include column headers (default: True)

    Raises:
        ExportError: If export fails

    Example:
        >>> from processlog.core.generator import generate_log
        >>> from processlog.config import load_config
        >>> config = load_config('configs/process_config.yaml')
        >>> df = generate_log(config, seed=42, num_cases=10)
        >>> export_csv(df, 'output/events.csv')
    """
    output_path = Path(output_path)

    # Create output directory if it doesn't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Map column names to PM4Py/XES format
    try:
        df_export = _map_schema(df)
    except Exception as e:
        raise ExportError(f"Failed to map schema: {e}") from e

    # Export to CSV
    try:
        df_export.to_csv(output_path, index=False, header=include_header)
    except Exception as e:
        raise ExportError(f"Failed to write CSV file '{output_path}': {e}") from e


def _map_schema(df: pd.DataFrame) -> pd.DataFrame:
    """
    Map internal schema to PM4Py/XES schema

    Internal schema:
        case_id, activity, timestamp, resource, lifecycle, custom_attr1, custom_attr2, ...

    PM4Py/XES schema:
        case:concept:name, concept:name, time:timestamp, org:resource, lifecycle:transition,
        custom_attr1, custom_attr2, ...

    Custom attributes retain their original names (e.g., org:department, cost:amount)

    Args:
        df: DataFrame with internal schema

    Returns:
        DataFrame with PM4Py/XES schema
    """
    df_mapped = df.copy()

    # Rename standard columns
    rename_dict = {
        internal_name: xes_name
        for internal_name, xes_name in SCHEMA_MAPPING.items()
        if internal_name in df_mapped.columns
    }

    df_mapped = df_mapped.rename(columns=rename_dict)

    # Ensure chronological ordering (required by PM4Py)
    if "case:concept:name" in df_mapped.columns and "time:timestamp" in df_mapped.columns:
        df_mapped = df_mapped.sort_values(
            by=["case:concept:name", "time:timestamp"]
        ).reset_index(drop=True)

    return df_mapped


def get_pm4py_column_names() -> Dict[str, str]:
    """
    Get mapping of internal column names to PM4Py/XES column names

    Returns:
        Dictionary mapping internal names to PM4Py/XES names

    Example:
        >>> mapping = get_pm4py_column_names()
        >>> print(mapping['case_id'])
        'case:concept:name'
    """
    return SCHEMA_MAPPING.copy()
