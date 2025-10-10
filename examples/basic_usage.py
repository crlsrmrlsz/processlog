"""
Basic usage example for Event Log Generator

This example demonstrates the complete workflow:
1. Load configuration from YAML
2. Validate configuration
3. Generate event log
4. Export to CSV
"""

from pathlib import Path
from event_log_gen import load_config, validate_config, generate_log, export_csv


def main():
    """Main example workflow"""

    # 1. Load configuration
    print("Loading configuration...")
    config_path = Path(__file__).parent.parent / "configs" / "process_config.yaml"
    config = load_config(config_path)
    print(f"✓ Loaded configuration: {config['process_name']}")

    # 2. Validate configuration
    print("\nValidating configuration...")
    result = validate_config(config)

    if not result.valid:
        print("✗ Configuration is invalid:")
        for error in result.errors:
            print(f"  - {error}")
        return

    print(f"✓ Configuration is valid")
    if result.warnings:
        print(f"  Warnings ({len(result.warnings)}):")
        for warning in result.warnings:
            print(f"  - {warning}")

    # 3. Generate event log
    print("\nGenerating event log...")
    num_cases = 10  # Generate 10 cases for this example
    seed = 42  # Use seed 42 for reproducibility

    df = generate_log(config, seed=seed, num_cases=num_cases)

    print(f"✓ Generated {len(df)} events for {df['case_id'].nunique()} cases")
    print(f"\nEvent log summary:")
    print(f"  - Activities: {df['activity'].nunique()}")
    print(f"  - Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    print(f"  - Cases: {df['case_id'].nunique()}")

    # Show activity distribution
    print(f"\n  Activity distribution:")
    activity_counts = df['activity'].value_counts()
    for activity, count in activity_counts.items():
        print(f"    - {activity}: {count} events")

    # 4. Export to CSV
    print("\nExporting to CSV...")
    output_dir = Path(__file__).parent.parent / "output"
    output_path = output_dir / "events_example.csv"

    export_csv(df, output_path)
    print(f"✓ Exported to: {output_path}")

    # Show first few rows
    print(f"\nFirst 5 events (internal schema):")
    print(df.head())

    print("\n✓ Example complete!")
    print(f"\nNext steps:")
    print(f"  - View generated CSV: {output_path}")
    print(f"  - Modify configs/process_config.yaml to change process")
    print(f"  - Change num_cases and seed parameters for different results")


if __name__ == "__main__":
    main()
