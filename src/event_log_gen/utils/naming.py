"""
Naming utilities for run folders and metadata

Provides professional naming conventions for output directories and files
following MLOps and data pipeline best practices.
"""

import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional


def generate_run_name(
    process_name: str,
    num_cases: int,
    seed: int,
    timestamp: Optional[datetime] = None,
    custom_name: Optional[str] = None
) -> str:
    """
    Generate timestamped run folder name with embedded parameters

    Format: YYYYMMDD_HHMMSS_{process_slug}_n{cases}_s{seed}
    Example: 20241012_143022_permit_n1000_s42

    Args:
        process_name: Full process name from config
        num_cases: Number of cases generated
        seed: Random seed used
        timestamp: Optional timestamp (defaults to now)
        custom_name: Optional custom name to use instead of process slug

    Returns:
        Formatted run name string

    Example:
        >>> generate_run_name("Restaurant Permit Application", 1000, 42)
        '20241012_143022_permit_n1000_s42'
    """
    if timestamp is None:
        timestamp = datetime.now()

    # Format timestamp as YYYYMMDD_HHMMSS
    ts_str = timestamp.strftime("%Y%m%d_%H%M%S")

    # Use custom name or slugify process name
    if custom_name:
        slug = slugify_process_name(custom_name)
    else:
        slug = slugify_process_name(process_name)

    # Build run name with parameters
    run_name = f"{ts_str}_{slug}_n{num_cases}_s{seed}"

    return run_name


def slugify_process_name(process_name: str, max_length: int = 20) -> str:
    """
    Convert process name to filesystem-safe slug

    Rules:
    - Lowercase only
    - Replace spaces and special chars with underscores
    - Remove consecutive underscores
    - Truncate to max_length
    - Remove leading/trailing underscores

    Args:
        process_name: Full process name
        max_length: Maximum slug length (default: 20)

    Returns:
        Slugified name

    Example:
        >>> slugify_process_name("Restaurant Permit Application")
        'permit'
        >>> slugify_process_name("Order-to-Cash Process (V2)")
        'order_to_cash'
    """
    # Convert to lowercase
    slug = process_name.lower()

    # Replace spaces and special characters with underscores
    slug = re.sub(r'[^a-z0-9]+', '_', slug)

    # Remove consecutive underscores
    slug = re.sub(r'_+', '_', slug)

    # Remove leading/trailing underscores
    slug = slug.strip('_')

    # Truncate to max length
    if len(slug) > max_length:
        # Try to keep meaningful words (split on underscore)
        parts = slug.split('_')
        slug = parts[0]  # Start with first word

        # Add more words if they fit
        for part in parts[1:]:
            if len(slug) + len(part) + 1 <= max_length:
                slug += '_' + part
            else:
                break

    return slug or 'process'  # Fallback if empty


def get_git_commit() -> Optional[str]:
    """
    Get current git commit hash (short form)

    Returns:
        7-character commit hash or None if not in git repo

    Example:
        >>> get_git_commit()
        '903aab0'
    """
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--short', 'HEAD'],
            capture_output=True,
            text=True,
            timeout=2,
            check=False
        )

        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None


def create_output_path(
    base_dir: Path,
    run_name: str,
    create_symlink: bool = True
) -> Path:
    """
    Create output directory path and optionally symlink

    Args:
        base_dir: Base output directory (e.g., output/runs/)
        run_name: Generated run name
        create_symlink: If True, create/update 'latest' symlink

    Returns:
        Path to run directory

    Example:
        >>> path = create_output_path(Path("output/runs"), "20241012_143022_permit_n1000_s42")
        >>> print(path)
        output/runs/20241012_143022_permit_n1000_s42
    """
    run_path = base_dir / run_name
    run_path.mkdir(parents=True, exist_ok=True)

    if create_symlink:
        symlink_path = base_dir.parent / 'latest'

        # Remove existing symlink if present
        if symlink_path.is_symlink() or symlink_path.exists():
            symlink_path.unlink()

        # Create relative symlink
        try:
            relative_target = Path('runs') / run_name
            symlink_path.symlink_to(relative_target)
        except OSError:
            # Symlinks may not work on all filesystems (Windows without dev mode)
            pass

    return run_path


def get_cli_command() -> str:
    """
    Get the CLI command that was executed

    Returns:
        Command string (e.g., "event-log-gen generate -c config.yaml -n 1000")
    """
    import sys
    return ' '.join(sys.argv)
