"""
Metadata exporter module

Exports run metadata to JSON format for tracking and reproducibility.
"""

import json
from pathlib import Path
from typing import Any, Dict


def export_metadata(metadata: Dict[str, Any], output_path: str | Path) -> None:
    """
    Export metadata dictionary to JSON file

    Args:
        metadata: Metadata dictionary from generator
        output_path: Path to output JSON file

    Example:
        >>> metadata = {
        ...     "generator_version": "1.0.0",
        ...     "process_name": "Restaurant Permit Application",
        ...     "num_cases": 1000,
        ...     "num_events": 7234,
        ...     "seed": 42
        ... }
        >>> export_metadata(metadata, "output/run_metadata.json")
    """
    output_path = Path(output_path)

    # Create output directory if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write JSON with pretty formatting
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
