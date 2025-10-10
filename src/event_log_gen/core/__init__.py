"""
Core generation module

Provides core event log generation functionality.
"""

from .generator import Event, GenerationError, generate_log

__all__ = [
    "Event",
    "GenerationError",
    "generate_log",
]
