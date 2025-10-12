"""
Command-line interface for Event Log Generator
"""

import sys
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional

from event_log_gen import (
    load_config,
    validate_config,
    generate_log,
    export_csv,
    export_parquet,
    export_json,
    export_xes,
    export_metadata,
    __version__,
)
from event_log_gen.utils.naming import (
    generate_run_name,
    create_output_path,
    get_git_commit,
    get_cli_command,
)


def cmd_generate(args: argparse.Namespace) -> int:
    """Generate event logs from configuration"""
    try:
        # Load configuration
        print(f"Loading configuration from {args.config}...")
        config = load_config(str(args.config))

        # Validate configuration
        print("Validating configuration...")
        result = validate_config(config)
        if not result.valid:
            print("✗ Configuration has errors:")
            for error in result.errors:
                print(f"  - {error}")
            return 1

        if result.warnings:
            print("⚠ Configuration warnings:")
            for warning in result.warnings:
                print(f"  - {warning}")

        print("✓ Configuration valid")

        # Override config values if specified
        num_cases = args.cases if args.cases else config.get("num_cases", 100)
        seed = args.seed if args.seed is not None else config.get("seed", 42)

        # Determine output directory
        if args.output:
            # User specified output path - use as-is (backward compatibility)
            output_dir = Path(args.output)
            output_dir.mkdir(parents=True, exist_ok=True)
        elif args.no_timestamp:
            # Flat output without timestamp (for CI/CD)
            output_dir = Path("output")
            output_dir.mkdir(parents=True, exist_ok=True)
        else:
            # Generate timestamped run folder (new default behavior)
            process_name = config.get("process_name", "process")
            timestamp = datetime.now()

            # Use custom run name if provided
            if args.run_name:
                run_name = generate_run_name(
                    process_name=process_name,
                    num_cases=num_cases,
                    seed=seed,
                    timestamp=timestamp,
                    custom_name=args.run_name
                )
            else:
                run_name = generate_run_name(
                    process_name=process_name,
                    num_cases=num_cases,
                    seed=seed,
                    timestamp=timestamp
                )

            # Create run directory with optional symlink
            base_runs_dir = Path("output") / "runs"
            output_dir = create_output_path(
                base_dir=base_runs_dir,
                run_name=run_name,
                create_symlink=args.link_latest
            )

            print(f"Run directory: {output_dir}/")

        # Generate event log with metadata
        print(f"Generating {num_cases} cases (seed={seed})...")
        df, metadata = generate_log(config, seed=seed, num_cases=num_cases, return_metadata=True)
        print(f"✓ Generated {len(df)} events across {df['case_id'].nunique()} cases")

        # Enhance metadata with CLI context
        git_commit = get_git_commit()
        if git_commit:
            metadata["git_commit"] = git_commit
        metadata["cli_command"] = get_cli_command()
        metadata["config_file"] = str(args.config)

        # Export to requested formats
        formats = args.format if args.format != ['all'] else ['csv', 'parquet', 'json', 'xes']

        for fmt in formats:
            output_path = output_dir / f"events.{fmt}"
            print(f"Exporting to {fmt.upper()}...", end=" ", flush=True)

            if fmt == 'csv':
                export_csv(df, output_path)
            elif fmt == 'parquet':
                export_parquet(df, output_path)
            elif fmt == 'json':
                export_json(df, output_path)
            elif fmt == 'xes':
                export_xes(df, output_path)
            else:
                print(f"✗ Unknown format: {fmt}")
                continue

            print(f"✓ {output_path.name}")

        # Export metadata
        metadata_path = output_dir / "run_metadata.json"
        export_metadata(metadata, metadata_path)
        print(f"Metadata: ✓ {metadata_path.name}")

        print(f"\n✓ Event logs generated in {output_dir}/")
        return 0

    except FileNotFoundError as e:
        print(f"✗ Error: {e}")
        return 1
    except Exception as e:
        print(f"✗ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def cmd_validate(args: argparse.Namespace) -> int:
    """Validate configuration file"""
    try:
        print(f"Loading configuration from {args.config}...")
        config = load_config(str(args.config))

        print("Validating configuration...")
        result = validate_config(config)

        if result.valid:
            print("✓ Configuration is valid")
            print(f"\nProcess: {config.get('process_name', 'Unnamed')}")
            print(f"Activities: {len(config.get('activities', []))}")
            print(f"Resource pools: {len(config.get('resource_pools', {}))}")
            return 0
        else:
            print("✗ Configuration has errors:")
            for error in result.errors:
                print(f"  - {error}")
            return 1

    except FileNotFoundError as e:
        print(f"✗ Error: {e}")
        return 1
    except Exception as e:
        print(f"✗ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def cmd_info(args: argparse.Namespace) -> int:
    """Display information about configuration"""
    try:
        config = load_config(str(args.config))
        result = validate_config(config)

        if not result.valid:
            print("✗ Configuration is invalid. Run with 'validate' to see errors.")
            return 1

        print(f"Process: {config.get('process_name', 'Unnamed')}")
        print(f"Cases to generate: {config.get('num_cases', 100)}")
        print(f"Random seed: {config.get('seed', 42)}")
        print(f"Start date: {config.get('start_date', 'Not specified')}")
        print()

        activities = config.get('activities', [])
        print(f"Activities ({len(activities)}):")
        for activity in activities:
            activity_type = activity.get('type', 'unknown')
            print(f"  {activity['step']}. {activity['id']} ({activity_type})")

        resource_pools = config.get('resource_pools', {})
        print(f"\nResource Pools ({len(resource_pools)}):")
        for pool_name, resources in resource_pools.items():
            print(f"  {pool_name}: {len(resources)} resources")

        # Count process variants (terminal activities)
        variants = set()
        for activity in activities:
            next_steps = activity.get('next_steps', [])
            if not next_steps:  # Terminal activity
                variants.add(activity['id'])
        print(f"\nProcess Variants: {len(variants)} endpoints")

        return 0

    except FileNotFoundError as e:
        print(f"✗ Error: {e}")
        return 1
    except Exception as e:
        print(f"✗ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser"""
    parser = argparse.ArgumentParser(
        prog='event-log-gen',
        description='Generate synthetic process event logs for testing and development',
        epilog='For more information, visit: https://github.com/crlsrmrlsz/event-log-gen'
    )

    parser.add_argument(
        '--version',
        action='version',
        version=f'%(prog)s {__version__}'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Generate command
    gen_parser = subparsers.add_parser(
        'generate',
        help='Generate event logs from configuration'
    )
    gen_parser.add_argument(
        '-c', '--config',
        type=Path,
        required=True,
        help='Path to YAML configuration file'
    )
    gen_parser.add_argument(
        '-o', '--output',
        type=Path,
        default=None,
        help='Output directory (default: timestamped run folder)'
    )
    gen_parser.add_argument(
        '-f', '--format',
        nargs='+',
        choices=['csv', 'parquet', 'json', 'xes', 'all'],
        default=['all'],
        help='Export formats (default: all)'
    )
    gen_parser.add_argument(
        '-n', '--cases',
        type=int,
        help='Number of cases to generate (overrides config)'
    )
    gen_parser.add_argument(
        '-s', '--seed',
        type=int,
        help='Random seed (overrides config)'
    )
    gen_parser.add_argument(
        '--run-name',
        type=str,
        help='Custom run name (default: auto-generated from process name)'
    )
    gen_parser.add_argument(
        '--no-timestamp',
        action='store_true',
        help='Disable timestamped run folders (output to flat directory)'
    )
    gen_parser.add_argument(
        '--link-latest',
        action='store_true',
        default=True,
        help='Create/update "latest" symlink to this run (default: True)'
    )

    # Validate command
    val_parser = subparsers.add_parser(
        'validate',
        help='Validate configuration file'
    )
    val_parser.add_argument(
        '-c', '--config',
        type=Path,
        required=True,
        help='Path to YAML configuration file'
    )

    # Info command
    info_parser = subparsers.add_parser(
        'info',
        help='Display configuration information'
    )
    info_parser.add_argument(
        '-c', '--config',
        type=Path,
        required=True,
        help='Path to YAML configuration file'
    )

    return parser


def main(argv: Optional[list] = None) -> int:
    """Main entry point"""
    parser = create_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 1

    if args.command == 'generate':
        return cmd_generate(args)
    elif args.command == 'validate':
        return cmd_validate(args)
    elif args.command == 'info':
        return cmd_info(args)
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
