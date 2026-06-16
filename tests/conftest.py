"""
Pytest configuration and fixtures for event log generator tests
"""

import pytest
from pathlib import Path


@pytest.fixture
def fixtures_dir() -> Path:
    """Return path to test fixtures directory"""
    return Path(__file__).parent / 'fixtures'


@pytest.fixture
def minimal_config_yaml() -> str:
    """
    Minimal valid configuration for testing

    Simple process with 2 activities and 1 resource pool
    """
    return """
process_name: "Test Process"
num_cases: 10
seed: 42
start_date: "2024-01-01"
timezone: "UTC"

activities:
  - step: 1
    id: start
    name: "Start"
    type: automatic
    duration:
      min: 0
      max: 1
    next_steps:
      - activity: end
        probability: 1.0

  - step: 2
    id: end
    name: "End"
    type: automatic
    duration:
      min: 0
      max: 1
    next_steps: []

resource_pools:
  clerks:
    - id: clerk_001
      name: "Test Clerk"
      speed: 1.0
      consistency: 1.0
      capacity: 1.0
"""


@pytest.fixture
def invalid_probabilities_yaml() -> str:
    """Configuration with invalid probabilities (don't sum to 1.0)"""
    return """
process_name: "Test Process"
num_cases: 10
seed: 42
start_date: "2024-01-01"

activities:
  - id: start
    name: "Start"
    type: automatic
    duration:
      min: 0
      max: 1
    next_steps:
      - activity: end
        probability: 0.5

  - id: end
    name: "End"
    type: automatic
    duration:
      min: 0
      max: 1
    next_steps: []

resource_pools:
  clerks:
    - id: clerk_001
      name: "Test Clerk"
"""


@pytest.fixture
def invalid_duration_yaml() -> str:
    """Configuration with invalid duration format (both min/max and typical/spread)"""
    return """
process_name: "Test Process"
num_cases: 10
seed: 42
start_date: "2024-01-01"

activities:
  - id: start
    name: "Start"
    type: automatic
    duration:
      min: 10
      max: 20
      typical: 15
      spread: 3
    next_steps:
      - activity: end
        probability: 1.0

  - id: end
    name: "End"
    type: automatic
    duration:
      min: 0
      max: 1
    next_steps: []

resource_pools:
  clerks:
    - id: clerk_001
      name: "Test Clerk"
"""


@pytest.fixture
def missing_resource_pool_yaml() -> str:
    """Configuration with activity referencing non-existent resource pool"""
    return """
process_name: "Test Process"
num_cases: 10
seed: 42
start_date: "2024-01-01"

activities:
  - id: start
    name: "Start"
    type: human
    resource_pool: nonexistent_pool
    duration:
      min: 10
      max: 20
    next_steps:
      - activity: end
        probability: 1.0

  - id: end
    name: "End"
    type: automatic
    duration:
      min: 0
      max: 1
    next_steps: []

resource_pools:
  clerks:
    - id: clerk_001
      name: "Test Clerk"
"""
