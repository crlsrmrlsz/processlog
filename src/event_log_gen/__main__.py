"""
Module entry point for running event-log-gen as a module

Usage:
    python -m event_log_gen generate -c config.yaml
    python -m event_log_gen validate -c config.yaml
    python -m event_log_gen info -c config.yaml
"""

import sys
from event_log_gen.cli import main

if __name__ == '__main__':
    sys.exit(main())
