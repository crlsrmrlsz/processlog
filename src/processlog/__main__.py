"""
Module entry point for running processlog as a module

Usage:
    python -m processlog generate -c config.yaml
    python -m processlog validate -c config.yaml
    python -m processlog info -c config.yaml
"""

import sys
from processlog.cli import main

if __name__ == '__main__':
    sys.exit(main())
