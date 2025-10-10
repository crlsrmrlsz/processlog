# Event Log Generator - System Architecture

**Version**: 0.1.0
**Date**: 2025-01-09
**Status**: Phase 3 Complete - Minimal Generator Implementation

---

## 1. Overview

The Event Log Generator is a Python application that generates realistic synthetic process event logs from a single YAML configuration file. The system produces PM4Py and XES 1849-2023 compatible outputs in four formats: CSV, Parquet, JSON (NDJSON), and XES.

### 1.1 Design Philosophy

- **Human-centric configuration**: Non-technical users can modify behavior without code changes
- **PM4Py-first**: All outputs are directly importable and usable by PM4Py without reformatting
- **Reproducibility**: Seeded RNG ensures identical outputs for the same configuration
- **Extensibility**: Modular design allows easy addition of new exporters and features

### 1.2 Key Requirements

1. **PM4Py Compatibility**: Generated logs must be fully usable by PM4Py functions (read, discover, filter, analyze)
2. **XES Standard Compliance**: Follow IEEE XES 1849-2023 naming conventions and attribute structure
3. **Semantic Realism**: Resource performance profiles, workload effects, and domain constraints
4. **Testability**: Each module independently testable with high coverage (>80%)

### 1.3 Implementation Status

**Phase 0 - Research & Analysis**: ✅ **COMPLETE**
- `docs/research_summary.md` - PM4Py/XES research, schema design
- `docs/PROCESS_DEFINITION.md` - Restaurant permit process specification

**Phase 1 - Configuration Schema**: ✅ **COMPLETE**
- `configs/process_config.yaml` - 628 lines, self-documenting, 10 activities, 5 variants
- `src/event_log_gen/config/loader.py` - YAML loading (114 lines)
- `src/event_log_gen/config/validator.py` - Schema + semantic validation (508 lines)
- `tests/test_config/` - 50+ validation tests

**Phase 2 - Architecture Design**: ✅ **COMPLETE**
- This document (600+ lines)

**Phase 3 - Minimal Generator**: ✅ **COMPLETE**
- `src/event_log_gen/core/generator.py` - Core generator with seeded RNG (341 lines)
- `src/event_log_gen/exporters/csv_exporter.py` - CSV export with PM4Py schema (114 lines)
- `tests/test_core/` - Generator tests (20+ tests)
- `tests/test_exporters/` - CSV exporter tests (15+ tests)
- `tests/test_integration_simple.py` - End-to-end integration tests
- `examples/basic_usage.py` - Example workflow
- `README.md` - Complete documentation (350+ lines)

**Implemented Features (Phase 3)**:
- ✅ Seeded RNG for reproducibility
- ✅ Activity flow via next_steps probability tree
- ✅ Variant emergence (5 variants from probabilities)
- ✅ Duration calculation (min/max uniform, typical/spread normal)
- ✅ PM4Py schema mapping (internal → XES column names)
- ✅ Custom attribute support (namespace prefixes preserved)
- ✅ Chronological event ordering
- ✅ CSV export with PM4Py-compatible format

**Pending Features (Phase 4+)**:
- ⏳ Full resource allocation (currently placeholder)
- ⏳ 7-step duration pipeline (Phase 3: simplified 2-step)
- ⏳ Anomaly system (delays, peak times, fatigue)
- ⏳ Working hours/calendar logic
- ⏳ Rework loops
- ⏳ Parquet, JSON, XES exporters
- ⏳ PM4Py compatibility validation tests

---

## 2. System Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     User Interface                          │
│                  (CLI / Python API)                         │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                Configuration Module                         │
│  ┌────────────┐              ┌──────────────┐              │
│  │   Loader   │────────────▶ │  Validator   │              │
│  └────────────┘              └──────────────┘              │
│     (YAML)                    (Schema + Logic)              │
└───────────────────────┬─────────────────────────────────────┘
                        │ ConfigDict
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                   Core Generation Module                    │
│  ┌──────────────┐  ┌────────────┐  ┌──────────────┐        │
│  │  Generator   │─▶│  Process   │─▶│    Time      │        │
│  │   (Main)     │  │   Engine   │  │   Engine     │        │
│  └──────┬───────┘  └─────┬──────┘  └──────────────┘        │
│         │                 │                                  │
│         │                 ▼                                  │
│         │          ┌────────────┐                           │
│         └─────────▶│ Resources  │                           │
│                    │  Manager   │                           │
│                    └────────────┘                           │
└───────────────────────┬─────────────────────────────────────┘
                        │ DataFrame (internal schema)
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                  Export Module                              │
│  ┌────────┐  ┌─────────┐  ┌────────┐  ┌────────┐          │
│  │  CSV   │  │ Parquet │  │  JSON  │  │  XES   │          │
│  └────────┘  └─────────┘  └────────┘  └────────┘          │
│  (Schema mapping: internal → PM4Py/XES names)              │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
                 Output Files (.csv, .parquet, .json, .xes)
```

### 2.2 Module Structure

```
src/event_log_gen/
├── __init__.py                  # Package exports
├── __main__.py                  # CLI entry point
├── cli.py                       # CLI interface (Phase 5)
│
├── config/                      # Configuration module
│   ├── __init__.py
│   ├── loader.py               # YAML loading
│   └── validator.py            # Schema + semantic validation
│
├── core/                        # Core generation logic
│   ├── __init__.py
│   ├── generator.py            # Main orchestration
│   ├── process.py              # Process flow logic (variants, next_steps)
│   ├── resources.py            # Resource allocation & performance
│   └── time_engine.py          # Duration calculation (7-step pipeline)
│
└── exporters/                   # Output format exporters
    ├── __init__.py
    ├── base.py                 # Base exporter interface
    ├── csv_exporter.py         # CSV export (Phase 3)
    ├── parquet_exporter.py     # Parquet export (Phase 4)
    ├── json_exporter.py        # JSON/NDJSON export (Phase 4)
    └── xes_exporter.py         # XES export via pm4py (Phase 4)
```

---

## 3. Module Responsibilities

### 3.1 Configuration Module (`config/`)

**Purpose**: Load and validate YAML configuration files

#### `loader.py`
**Responsibilities**:
- Parse YAML file using `pyyaml`
- Return structured dictionary (`ConfigDict`)
- Handle file I/O errors gracefully

**Key Functions**:
```python
def load_config(file_path: str) -> ConfigDict:
    """Load YAML configuration from file"""

def parse_yaml(yaml_string: str) -> ConfigDict:
    """Parse YAML string (for testing)"""
```

#### `validator.py`
**Responsibilities**:
- Validate configuration schema (required fields, types)
- Validate semantic constraints (probabilities sum to 1.0, duration formats)
- Validate PM4Py column naming conventions
- Validate XES namespace conventions for custom attributes

**Key Validations**:
1. **Schema validation**: Required sections (process, activities, resources)
2. **Probability validation**: `next_steps` probabilities sum to 1.0 (±0.001 tolerance)
3. **Duration validation**: Each activity has EITHER `min/max` OR `typical/spread`, not both
4. **Resource validation**: All referenced resource pools exist
5. **Custom attribute validation**: Namespace prefixes valid (`org:`, `cost:`, `location:`, `case:`)
6. **Semantic validation**: Activity IDs unique, step numbers sequential

**Key Functions**:
```python
def validate_config(config: ConfigDict) -> ValidationResult:
    """Validate configuration, return errors/warnings"""

def validate_probabilities(next_steps: List[Dict]) -> bool:
    """Check probabilities sum to 1.0"""

def validate_duration_format(duration: Dict) -> bool:
    """Check min/max OR typical/spread, not both"""
```

**Error Handling**:
- **Errors**: Stop execution (invalid schema, probabilities don't sum to 1.0)
- **Warnings**: Allow execution (missing optional fields, sub-optimal values)

---

### 3.2 Core Module (`core/`)

**Purpose**: Generate event log from validated configuration

#### `generator.py`
**Responsibilities**:
- Main orchestration: coordinate all generation steps
- Initialize seeded RNG (`random.Random(seed)`)
- Generate specified number of cases
- Return DataFrame with internal schema

**Key Functions**:
```python
def generate_log(config: ConfigDict, seed: int, num_cases: int) -> pd.DataFrame:
    """Main entry point - generate complete event log"""

def generate_case(case_id: str, config: ConfigDict, rng: random.Random) -> List[Event]:
    """Generate single case (trace)"""
```

**Data Flow**:
1. Initialize RNG with seed
2. Create resource manager from config
3. For each case:
   - Select variant (via process engine)
   - Generate events following activity flow
   - Calculate timestamps (via time engine)
   - Assign resources (via resource manager)
4. Collect all events into DataFrame (internal schema)

#### `process.py`
**Responsibilities**:
- Variant selection based on probabilities
- Activity flow logic (follow `next_steps` probability tree)
- Rework loop handling (max iterations)
- Track variant path for statistics

**Key Functions**:
```python
def select_next_activity(current_activity: str, config: ConfigDict, rng: random.Random) -> str:
    """Select next activity based on next_steps probabilities"""

def should_rework(activity: str, iteration: int, config: ConfigDict, rng: random.Random) -> bool:
    """Determine if activity should enter rework loop"""

def track_variant_path(events: List[Event]) -> str:
    """Infer variant from event sequence"""
```

**Variant Emergence**:
- Variants emerge naturally from probability tree
- No explicit variant definitions
- Variant tracked for ground truth metadata

#### `resources.py`
**Responsibilities**:
- Resource pool management
- Resource allocation (round-robin, workload-based)
- Performance profile tracking (speed, consistency, capacity)
- Fatigue modeling (workload accumulation)

**Key Functions**:
```python
def allocate_resource(pool_name: str, timestamp: datetime) -> Resource:
    """Allocate resource from pool based on availability"""

def get_performance_multiplier(resource: Resource, workload: int) -> float:
    """Calculate speed multiplier considering fatigue"""

def get_consistency_variance(resource: Resource, rng: random.Random) -> float:
    """Calculate consistency-based variance"""
```

**Resource Performance**:
- **Speed**: Base multiplier (0.7-1.4×) for all tasks
- **Consistency**: Variance in performance (0.6-1.0 → ±40% swing)
- **Capacity**: Workload capacity before fatigue (0.8-1.5×)
- **Fatigue**: Gradual slowdown after exceeding capacity

#### `time_engine.py`
**Responsibilities**:
- Implement 7-step duration calculation pipeline
- Apply anomaly knobs (delays, peak times)
- Enforce working hours/calendar logic
- Maintain chronological ordering

**Key Functions**:
```python
def calculate_duration(
    activity: Activity,
    resource: Resource,
    workload: int,
    timestamp: datetime,
    config: ConfigDict,
    rng: random.Random
) -> timedelta:
    """Calculate final duration using 7-step pipeline"""

def apply_working_hours(start: datetime, duration: timedelta, config: ConfigDict) -> datetime:
    """Adjust end time considering working hours"""

def should_apply_delay(config: ConfigDict, rng: random.Random) -> bool:
    """Random delay check (5% probability)"""

def should_apply_peak_slowdown(timestamp: datetime, config: ConfigDict, rng: random.Random) -> bool:
    """Peak time check (30% probability)"""
```

**7-Step Duration Calculation Pipeline**:
1. **Sample**: Draw base duration from distribution (uniform or normal)
2. **Speed**: Apply resource speed multiplier
3. **Consistency**: Apply resource consistency variance
4. **Fatigue**: Apply workload fatigue factor
5. **Delay**: Apply random delay anomaly (5% probability)
6. **Peak**: Apply peak time slowdown (30% probability)
7. **Calendar**: Adjust for working hours/holidays

**Anomaly Stacking**:
- Delays and peak times are **independent** (can both trigger)
- Example: 5% delay × 30% peak = 1.5% chance of both

---

### 3.3 Export Module (`exporters/`)

**Purpose**: Export internal DataFrame to PM4Py/XES compatible formats

#### `base.py`
**Responsibilities**:
- Define base exporter interface
- Common schema mapping logic (internal → PM4Py/XES)
- Custom attribute namespace handling

**Key Functions**:
```python
class BaseExporter(ABC):
    @abstractmethod
    def export(self, df: pd.DataFrame, output_path: str) -> None:
        """Export DataFrame to file"""

    def map_schema(self, df: pd.DataFrame) -> pd.DataFrame:
        """Map internal schema to PM4Py/XES schema"""
```

**Schema Mapping**:
```python
INTERNAL_SCHEMA = {
    'case_id': str,
    'activity': str,
    'timestamp': datetime,
    'resource': str,
    'lifecycle': str,
    # Custom attributes with original names
}

EXPORT_SCHEMA = {
    'case:concept:name': str,       # case_id
    'concept:name': str,             # activity
    'time:timestamp': datetime,      # timestamp
    'org:resource': str,             # resource
    'lifecycle:transition': str,     # lifecycle
    # Custom attributes with namespace prefixes preserved
}
```

#### `csv_exporter.py` (Phase 3)
**Responsibilities**:
- Export to CSV with PM4Py column names
- Handle custom attributes with XES namespaces
- Ensure chronological sort by case and timestamp

**Format**:
```csv
case:concept:name,concept:name,time:timestamp,org:resource,lifecycle:transition,cost:amount,location:office
case_001,submitted,2024-01-01 09:00:00,,,start,,
case_001,intake_validation,2024-01-01 09:00:00,clerk_001,complete,50.00,NY-Manhattan
```

#### `parquet_exporter.py` (Phase 4)
**Responsibilities**:
- Export to Parquet using `pyarrow`
- Preserve PM4Py column names and types
- Efficient for large datasets (1M+ events)

#### `json_exporter.py` (Phase 4)
**Responsibilities**:
- Export to NDJSON (newline-delimited JSON)
- Use PM4Py field names
- One event per line for streaming support

**Format**:
```json
{"case:concept:name":"case_001","concept:name":"submitted","time:timestamp":"2024-01-01T09:00:00","org:resource":null,"lifecycle:transition":"start"}
{"case:concept:name":"case_001","concept:name":"intake_validation","time:timestamp":"2024-01-01T09:00:00","org:resource":"clerk_001","lifecycle:transition":"complete"}
```

#### `xes_exporter.py` (Phase 4)
**Responsibilities**:
- Export to XES using `pm4py.write_xes()`
- Validate custom attributes work in XES format
- Critical test for full XES standard compliance

**Approach**:
1. Map internal DataFrame to PM4Py EventLog
2. Use `pm4py.convert_to_event_log()` for conversion
3. Write using `pm4py.write_xes(output_path, event_log)`

---

## 4. Data Flow

### 4.1 End-to-End Pipeline

```
1. YAML Config File
   └─▶ config.loader.load_config()
       └─▶ ConfigDict (raw)
           └─▶ config.validator.validate_config()
               └─▶ ConfigDict (validated)

2. ConfigDict (validated)
   └─▶ core.generator.generate_log()
       ├─▶ core.process.select_next_activity() [variant selection]
       ├─▶ core.resources.allocate_resource() [resource assignment]
       └─▶ core.time_engine.calculate_duration() [timestamp calculation]
           └─▶ DataFrame (internal schema)

3. DataFrame (internal schema)
   └─▶ exporters.*.export()
       ├─▶ exporters.base.map_schema() [internal → PM4Py/XES]
       └─▶ DataFrame (export schema)
           └─▶ Output File (.csv / .parquet / .json / .xes)
```

### 4.2 Internal Data Structures

#### Event (internal representation)
```python
@dataclass
class Event:
    case_id: str
    activity: str
    timestamp: datetime
    resource: Optional[str]
    lifecycle: str = "complete"
    custom_attributes: Dict[str, Any] = field(default_factory=dict)
```

#### ConfigDict (type hints)
```python
ConfigDict = TypedDict('ConfigDict', {
    'process_name': str,
    'num_cases': int,
    'seed': int,
    'start_date': str,
    'timezone': str,
    'working_hours': Dict[str, Any],
    'activities': List[Dict[str, Any]],
    'resource_pools': Dict[str, List[Dict[str, Any]]],
    'rework_loops': Dict[str, int],
    'anomalies': Dict[str, Any]
})
```

---

## 5. PM4Py/XES Compatibility Strategy

### 5.1 Column Naming Conventions

**Export column names** follow XES standard extensions:

| Internal Name | Export Name (PM4Py/XES) | XES Extension | Type |
|--------------|-------------------------|---------------|------|
| `case_id` | `case:concept:name` | Concept | string |
| `activity` | `concept:name` | Concept | string |
| `timestamp` | `time:timestamp` | Time | datetime |
| `resource` | `org:resource` | Organizational | string |
| `lifecycle` | `lifecycle:transition` | Lifecycle | string |

**Custom attributes** retain their namespace prefixes:
- `org:department` → `org:department` (unchanged)
- `cost:amount` → `cost:amount` (unchanged)
- `case:priority` → `case:priority` (unchanged)

### 5.2 PM4Py Integration Points

The system ensures PM4Py compatibility at three levels:

#### Level 1: Import (Phase 3)
Generated files must be directly importable:
```python
import pm4py

# CSV import
df = pm4py.read_csv('output/events.csv')

# Convert to EventLog
log = pm4py.convert_to_event_log(df)
```

#### Level 2: Analysis (Phase 4)
PM4Py analysis functions must work:
```python
# Process discovery
dfg, start_act, end_act = pm4py.discover_dfg(log)

# Statistics
start_activities = pm4py.get_start_activities(log)
end_activities = pm4py.get_end_activities(log)

# Filtering
filtered_log = pm4py.filter_time_range(log, start_date, end_date)
```

#### Level 3: Advanced Operations (Phase 6)
Full PM4Py workflows must complete:
```python
# Conformance checking
from pm4py.algo.conformance.tokenreplay import algorithm as token_replay
replayed_traces = token_replay.apply(log, net, im, fm)

# Performance analysis
from pm4py.statistics.traces.cycle_time import log as cycle_time
cycle_times = cycle_time.get_cycle_time(log)
```

### 5.3 Testing Strategy

**Phase 3 Tests** (Minimal Generator):
- `test_pm4py_read_csv()` - Basic import
- `test_pm4py_convert_to_event_log()` - DataFrame → EventLog conversion
- `test_pm4py_discover_dfg()` - Process discovery
- `test_pm4py_get_start_activities()` - Statistics functions

**Phase 4 Tests** (Full Features):
- `test_pm4py_read_parquet()` - Parquet import
- `test_pm4py_read_xes()` - XES import
- `test_pm4py_filter_operations()` - Time, attribute, variant filters
- `test_pm4py_custom_attributes()` - Custom attribute queries

**Phase 6 Tests** (Final Integration):
- `test_pm4py_full_workflow()` - Complete pipeline (import → discover → filter → export)
- `test_pm4py_conformance_checking()` - Advanced analysis
- `test_pm4py_performance_metrics()` - Throughput, cycle time calculations

---

## 6. Duration Calculation Pipeline (Detailed)

The duration calculation is the **core complexity** of the system. It follows a strict 7-step pipeline:

### 6.1 Pipeline Steps

```python
def calculate_duration(
    activity: Activity,
    resource: Resource,
    workload: int,
    timestamp: datetime,
    config: ConfigDict,
    rng: random.Random
) -> timedelta:
    """
    7-step duration calculation pipeline

    Example: intake_validation activity
    - Config: min=24h, max=72h
    - Resource: clerk_001 (speed=0.8, consistency=0.9, capacity=1.0)
    - Workload: 25 cases (fatigue_factor=1.15)
    - Anomalies: delay=5%, peak=30%
    """

    # STEP 1: SAMPLE base duration
    if 'min' in activity['duration']:
        # Uniform distribution
        base_duration = rng.uniform(
            activity['duration']['min'],
            activity['duration']['max']
        )
    else:
        # Normal distribution (typical/spread)
        base_duration = rng.gauss(
            activity['duration']['typical'],
            activity['duration']['spread']
        )
    # Example: base_duration = 48 hours

    # STEP 2: APPLY resource speed multiplier
    if activity['type'] == 'human':
        base_duration *= resource.speed
    # Example: 48 × 0.8 = 38.4 hours

    # STEP 3: APPLY resource consistency variance
    if activity['type'] == 'human':
        consistency_factor = resource.consistency
        variance = (1.0 - consistency_factor)
        swing = rng.uniform(-variance/2, variance/2)
        base_duration *= (1.0 + swing)
    # Example: consistency=0.9 → ±5% swing
    # 38.4 × (1 + 0.03) = 39.6 hours

    # STEP 4: APPLY resource fatigue
    if activity['type'] == 'human':
        fatigue_factor = calculate_fatigue(workload, resource.capacity)
        base_duration *= fatigue_factor
    # Example: workload=25, capacity=1.0 → fatigue=1.15
    # 39.6 × 1.15 = 45.5 hours

    # STEP 5: APPLY random delay anomaly
    if should_apply_delay(config['anomalies']['random_delays'], rng):
        delay_multiplier = rng.uniform(
            config['anomalies']['random_delays']['multiplier_min'],
            config['anomalies']['random_delays']['multiplier_max']
        )
        base_duration *= delay_multiplier
    # Example: 5% chance, multiplier=3.0
    # 45.5 × 3.0 = 136.5 hours (if triggered)

    # STEP 6: APPLY peak time anomaly
    if should_apply_peak_slowdown(timestamp, config['anomalies']['peak_times'], rng):
        slowdown_factor = config['anomalies']['peak_times']['slowdown_factor']
        base_duration *= slowdown_factor
    # Example: 30% chance, slowdown=1.1
    # 45.5 × 1.1 = 50.0 hours (if triggered)
    # Note: If both delay and peak trigger: 45.5 × 3.0 × 1.1 = 150.2 hours

    # STEP 7: APPLY calendar (working hours)
    return timedelta(hours=base_duration)
```

### 6.2 Anomaly Stacking

Delays and peak times are **independent probabilities**:

| Scenario | Delay (5%) | Peak (30%) | Combined Probability | Multiplier |
|----------|------------|------------|---------------------|------------|
| Neither | ❌ | ❌ | 66.5% | 1.0× |
| Peak only | ❌ | ✅ | 28.5% | 1.1× |
| Delay only | ✅ | ❌ | 4.75% | 3.0× |
| **Both** | ✅ | ✅ | **0.25%** | **3.3×** |

**Example**:
- Base duration after fatigue: 45.5 hours
- Delay triggers (5%): 45.5 × 3.0 = 136.5 hours
- Peak **also** triggers (30%): 136.5 × 1.1 = **150.2 hours**

### 6.3 Working Hours Calendar

The final step adjusts timestamps to respect working hours:

```python
def apply_working_hours(
    start: datetime,
    duration: timedelta,
    config: ConfigDict
) -> datetime:
    """
    Adjust end time considering working hours and holidays

    Example:
    - Start: Friday 4:00 PM
    - Duration: 8 hours
    - Working hours: Mon-Fri 9 AM - 5 PM
    - Result: Monday 12:00 PM (skips weekend)
    """
    current = start
    remaining = duration

    while remaining > timedelta(0):
        # Check if current time is within working hours
        if is_working_time(current, config):
            # Advance 1 hour
            current += timedelta(hours=1)
            remaining -= timedelta(hours=1)
        else:
            # Skip to next working hour
            current = next_working_hour(current, config)

    return current
```

---

## 7. Testing Architecture

### 7.1 Test Structure

```
tests/
├── __init__.py
├── conftest.py                     # Pytest fixtures (sample configs, RNG seeds)
│
├── test_config/                    # Configuration tests
│   ├── test_loader.py             # YAML loading
│   └── test_validator.py          # Schema + semantic validation
│
├── test_core/                      # Core logic tests
│   ├── test_generator.py          # End-to-end generation
│   ├── test_process.py            # Variant selection, next_steps
│   ├── test_resources.py          # Resource allocation, fatigue
│   └── test_time_engine.py        # 7-step duration pipeline
│
├── test_exporters/                 # Export tests
│   ├── test_csv_exporter.py       # CSV export
│   ├── test_parquet_exporter.py   # Parquet export
│   ├── test_json_exporter.py      # JSON export
│   ├── test_xes_exporter.py       # XES export
│   └── test_pm4py_compatibility.py # PM4Py integration tests
│
└── fixtures/                       # Test data
    ├── minimal_config.yaml        # 2 activities, 1 variant
    ├── full_config.yaml           # Copy of configs/process_config.yaml
    └── expected_outputs/          # Reference outputs for regression
```

### 7.2 Test Categories

#### Unit Tests
Test individual functions in isolation:
```python
def test_select_next_activity_probabilities():
    """Test that next activity selection respects probabilities"""
    config = load_fixture('minimal_config.yaml')
    rng = random.Random(42)

    # Run 1000 trials
    results = [select_next_activity('activity_1', config, rng) for _ in range(1000)]

    # Check distribution matches config (within tolerance)
    assert 0.55 <= results.count('activity_2') / 1000 <= 0.65  # Expected: 0.60
```

#### Integration Tests
Test module interactions:
```python
def test_generate_case_produces_valid_trace():
    """Test that generate_case produces chronologically ordered events"""
    config = load_fixture('full_config.yaml')
    rng = random.Random(42)

    events = generate_case('case_001', config, rng)

    # Check chronological order
    assert all(events[i].timestamp <= events[i+1].timestamp for i in range(len(events)-1))

    # Check variant validity
    assert events[0].activity == 'submitted'
    assert events[-1].activity in ['approved', 'rejected', 'withdrawn']
```

#### PM4Py Compatibility Tests
Critical tests ensuring PM4Py can use generated logs:
```python
def test_pm4py_can_discover_dfg_from_csv():
    """Test PM4Py can discover DFG from generated CSV"""
    # Generate log
    config = load_fixture('full_config.yaml')
    df = generate_log(config, seed=42, num_cases=10)

    # Export to CSV
    export_csv(df, 'test_output.csv')

    # Import with PM4Py
    df_imported = pm4py.read_csv('test_output.csv')
    log = pm4py.convert_to_event_log(df_imported)

    # Discover DFG (should not raise)
    dfg, start_activities, end_activities = pm4py.discover_dfg(log)

    # Validate structure
    assert len(start_activities) >= 1
    assert len(end_activities) >= 1
    assert len(dfg) >= 5  # At least 5 transitions
```

### 7.3 Coverage Targets

- **Phase 3** (Minimal Generator): >70% coverage (core functionality)
- **Phase 4** (Full Features): >80% coverage (all features)
- **Phase 6** (Final): >85% coverage (production-ready)

**Critical paths requiring 100% coverage**:
- Duration calculation pipeline (all 7 steps)
- Schema mapping (internal → PM4Py/XES)
- Probability validation (next_steps sum to 1.0)

---

## 8. Error Handling Strategy

### 8.1 Configuration Errors

**At validation time** (before generation):
```python
class ConfigurationError(Exception):
    """Raised when configuration is invalid"""
    pass

# Example: Probabilities don't sum to 1.0
if abs(sum(probs) - 1.0) > 0.001:
    raise ConfigurationError(
        f"Activity '{activity_id}' next_steps probabilities sum to {sum(probs)}, expected 1.0"
    )
```

### 8.2 Generation Errors

**During event generation**:
```python
class GenerationError(Exception):
    """Raised when event generation fails"""
    pass

# Example: Infinite loop detection
if iteration > 1000:
    raise GenerationError(
        f"Case '{case_id}' exceeded 1000 iterations, possible infinite loop"
    )
```

### 8.3 Export Errors

**During file export**:
```python
class ExportError(Exception):
    """Raised when export fails"""
    pass

# Example: PM4Py conversion failure
try:
    log = pm4py.convert_to_event_log(df)
except Exception as e:
    raise ExportError(
        f"Failed to convert DataFrame to PM4Py EventLog: {e}"
    ) from e
```

### 8.4 Error Recovery

- **Configuration errors**: Stop immediately, show clear error message
- **Generation warnings**: Log warning, continue generation
- **Export errors**: Try alternative export path, fallback to CSV

---

## 9. Performance Considerations

### 9.1 Target Performance

| Dataset Size | Generation Time | Export Time (CSV) | Memory Usage |
|-------------|-----------------|-------------------|--------------|
| 100 cases | <1 second | <1 second | <50 MB |
| 1,000 cases | <5 seconds | <2 seconds | <100 MB |
| 10,000 cases | <30 seconds | <10 seconds | <500 MB |
| 100,000 cases | <5 minutes | <1 minute | <2 GB |

### 9.2 Optimization Strategies

#### Phase 3 (Minimal)
- No optimization, focus on correctness
- Accept O(n) complexity for 1,000 cases

#### Phase 4 (Full Features)
- **Vectorization**: Use pandas vectorized operations where possible
- **Lazy evaluation**: Generate events on-demand, not all at once
- **Memory efficiency**: Stream to disk for large datasets (>100k cases)

#### Phase 6 (Production)
- **Parallel generation**: Use multiprocessing for independent cases
- **Batch export**: Write in chunks to reduce memory pressure
- **Progress reporting**: Show progress for long-running generations

### 9.3 Scalability Limits

**Current architecture**:
- Single-threaded: Up to 1M cases (10-30 minutes)
- Multi-threaded: Up to 10M cases (phase 6 enhancement)

**Memory constraints**:
- DataFrame in-memory: ~50 bytes per event
- 1M events ≈ 50 MB raw data + pandas overhead ≈ 200 MB total

---

## 10. Future Enhancements

### 10.1 Post-MVP Features

**Phase 7 (Potential)**:
- Multi-process generation for >10M cases
- Incremental export (streaming)
- Custom exporter plugins
- GUI configuration editor
- Real-time generation monitoring

### 10.2 Advanced Features

**Semantic extensions**:
- Inter-case dependencies (batch processing)
- Time-of-day effects (morning vs afternoon performance)
- Learning curves (resource improvement over time)
- Seasonal variations (holiday periods)

**Export extensions**:
- BPMN model export (process map)
- Simulation model export (CPN Tools, Simul8)
- Database export (PostgreSQL, MongoDB)

---

## 11. Dependencies

### 11.1 Core Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `python` | ≥3.10 | Modern type hints, match statements |
| `pyyaml` | ≥6.0 | YAML configuration parsing |
| `pandas` | ≥2.0.0 | DataFrame manipulation (PM4Py standard) |
| `pyarrow` | ≥12.0.0 | Parquet export |
| `pm4py` | ≥2.7.0 | XES export, validation |
| `jsonschema` | ≥4.17.0 | Configuration validation |

### 11.2 Development Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `pytest` | ≥7.3.0 | Testing framework |
| `pytest-cov` | ≥4.1.0 | Coverage reporting |
| `black` | ≥23.3.0 | Code formatting |
| `mypy` | ≥1.3.0 | Type checking |

### 11.3 Dependency Rationale

- **pandas**: Industry standard for event logs, PM4Py native format
- **pm4py**: Essential for XES export and validation
- **pyarrow**: Fastest Parquet implementation
- **pyyaml**: Human-readable config format
- **jsonschema**: Schema validation without custom code

---

## 12. Design Decisions

### 12.1 Key Architectural Choices

#### Why DataFrame (not EventLog)?
**Decision**: Use pandas DataFrame as internal representation, convert to PM4Py EventLog only on export

**Rationale**:
- Faster manipulation (vectorized operations)
- Easier testing (familiar DataFrame API)
- More flexible (custom attributes as columns)
- PM4Py EventLog is primarily for analysis, not generation

#### Why Dual Schema?
**Decision**: Maintain internal schema (simple names) separate from export schema (XES names)

**Rationale**:
- Cleaner internal code (`case_id` vs `case:concept:name`)
- Single point of schema mapping (exporters module)
- Easier to add new export formats (only change mapping)

#### Why 7-Step Pipeline?
**Decision**: Strict ordering of duration calculation steps

**Rationale**:
- **Composability**: Each step independent, easy to test
- **Transparency**: Users can understand calculation
- **Extensibility**: Easy to add new steps (e.g., holidays)
- **Reproducibility**: Deterministic order ensures same outputs

#### Why Seeded RNG?
**Decision**: Use seeded RNG instead of true randomness

**Rationale**:
- **Reproducibility**: Same config + seed = identical output
- **Debugging**: Easier to trace generation issues
- **Testing**: Deterministic tests possible
- **Research**: Enables controlled experiments

### 12.2 Trade-offs

| Choice | Pros | Cons | Mitigation |
|--------|------|------|------------|
| DataFrame-first | Fast, flexible | Memory intensive | Stream to disk for large datasets |
| YAML config | Human-readable | No schema enforcement | Add validator module |
| Single-threaded | Simple, debuggable | Slow for 10M+ cases | Add multiprocessing in phase 7 |
| 7-step pipeline | Transparent, testable | Slightly slower | Acceptable for target scale |

---

## 13. Glossary

- **Activity**: A step in the process (e.g., "intake_validation")
- **Case**: A single process instance with unique case_id
- **Event**: A single occurrence of an activity within a case
- **Trace**: Sequence of events for a single case (synonym: case)
- **Variant**: A unique path through the process (e.g., "Direct Approval")
- **Resource**: A person or system that performs activities
- **Resource Pool**: A group of resources (e.g., "clerks")
- **Lifecycle**: Event state (start, complete, suspend, resume)
- **XES**: eXtensible Event Stream, IEEE standard 1849-2023
- **PM4Py**: Python library for process mining
- **DFG**: Directly-Follows Graph, a process model representation
- **EventLog**: PM4Py's internal representation (Log → Traces → Events)
- **Namespace**: XES attribute prefix (e.g., `org:`, `cost:`)
- **Custom Attribute**: User-defined event or case attribute

---

## Document Status

**Current Phase**: ✅ Phase 3 Complete - Minimal Generator Implementation
**Next Phase**: Phase 4 - Full Features (Parquet/JSON/XES, resources, calendars, anomalies)
**Last Updated**: 2025-01-09

### Completed Modules (Phase 3)

| Module | Status | Lines | Tests | Description |
|--------|--------|-------|-------|-------------|
| `config/loader.py` | ✅ | 114 | 20+ | YAML configuration loading |
| `config/validator.py` | ✅ | 508 | 30+ | Schema + semantic validation |
| `core/generator.py` | ✅ | 341 | 20+ | Event log generation with seeded RNG |
| `exporters/csv_exporter.py` | ✅ | 114 | 15+ | CSV export with PM4Py schema |

**Total**: ~1,100 lines of production code, 50+ test cases

### Pending Modules (Phase 4+)

| Module | Status | Description |
|--------|--------|-------------|
| `core/process.py` | ⏳ | Advanced process flow (rework loops) |
| `core/resources.py` | ⏳ | Full resource allocation & performance |
| `core/time_engine.py` | ⏳ | 7-step duration pipeline, calendar logic |
| `exporters/parquet_exporter.py` | ⏳ | Parquet export |
| `exporters/json_exporter.py` | ⏳ | JSON/NDJSON export |
| `exporters/xes_exporter.py` | ⏳ | XES export via pm4py |
| `cli.py` | ⏳ | Command-line interface |

### How to Use (Phase 3)

```python
from event_log_gen import load_config, validate_config, generate_log, export_csv

# Load and validate
config = load_config('configs/process_config.yaml')
result = validate_config(config)

if result.valid:
    # Generate log
    df = generate_log(config, seed=42, num_cases=1000)

    # Export to PM4Py-compatible CSV
    export_csv(df, 'output/events.csv')
```

For complete documentation, see `README.md`.
