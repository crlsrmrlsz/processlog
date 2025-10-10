# Event Log Generator

Synthetic process event log generator from YAML configuration with full PM4Py and XES 1849-2023 standard compatibility.

## Overview

This tool generates realistic synthetic event logs for process mining analysis. It reads a human-friendly YAML configuration file and produces event logs in multiple formats (CSV, Parquet, JSON, XES) that are directly usable by PM4Py and other process mining tools.

**Key Features:**
- 🎯 **PM4Py-first design**: All exports directly importable into PM4Py without reformatting
- 📝 **Human-centric configuration**: Self-documenting YAML with inline comments
- 🔁 **Reproducible**: Seeded RNG ensures identical outputs for the same configuration
- 📊 **Multiple formats**: CSV, Parquet, JSON, XES (Phase 4)
- ⚡ **Fast**: Generate 100K+ events in seconds
- 🧪 **Well-tested**: >80% test coverage with PM4Py compatibility tests

## Project Status

**Current Phase: Phase 4 - Full Features** ✅ **COMPLETE**

- ✅ **Phase 0**: Research & documentation
- ✅ **Phase 1**: Configuration schema & validator
- ✅ **Phase 2**: Architecture design
- ✅ **Phase 3**: Minimal generator (CSV export, basic features)
- ✅ **Phase 4**: Full features (Parquet/JSON/XES, resource pools, calendars, custom attributes)
- ⏳ **Phase 5**: CLI & packaging
- ⏳ **Phase 6**: Final integration & sample datasets

**Phase 4 Complete (2025-10-10):**
- ✅ Core generator with seeded RNG and reproducibility
- ✅ Activity flow (next_steps probability tree, 5 variants)
- ✅ Resource allocation (capacity-weighted, speed/consistency profiles)
- ✅ Working calendar (business hours 9-5, weekends, holidays)
- ✅ Custom attributes (event-level & case-level with XES namespaces)
- ✅ Export formats: CSV, Parquet, JSON (NDJSON), XES
- ✅ PM4Py compatibility tests (135 tests, 80% coverage)
- ✅ PM4Py visualization tests (DFG, Petri nets, BPMN, Process trees)
- ✅ Visualization script (`scripts/generate_visualizations.py`)

## Installation

### Prerequisites

- Python 3.10 or higher
- pip package manager

### Install Dependencies

```bash
# Production dependencies
pip install -r requirements.txt

# Development dependencies (includes testing tools)
pip install -r requirements-dev.txt
```

**Core dependencies:**
- `pyyaml>=6.0` - Configuration parsing
- `pandas>=2.0.0` - DataFrame manipulation
- `pyarrow>=12.0.0` - Parquet export (Phase 4)
- `pm4py>=2.7.0` - XES export and validation
- `jsonschema>=4.17.0` - Configuration validation

## Quick Start

### 1. Basic Usage

```python
from event_log_gen import (
    load_config, validate_config, generate_log,
    export_csv, export_parquet, export_json, export_xes
)

# Load configuration
config = load_config('configs/process_config.yaml')

# Validate configuration
result = validate_config(config)
if not result.valid:
    print("Errors:", result.errors)
    exit(1)

# Generate event log
df = generate_log(config, seed=42, num_cases=1000)

# Export to multiple formats (all PM4Py-compatible)
export_csv(df, 'output/events.csv')
export_parquet(df, 'output/events.parquet')
export_json(df, 'output/events.json')
export_xes(df, 'output/events.xes')
```

### 2. Run Example

```bash
python examples/basic_usage.py
```

This will:
1. Load `configs/process_config.yaml`
2. Validate the configuration
3. Generate 10 cases
4. Export to `output/events_example.csv`
5. Display summary statistics

### 3. Generate PM4Py Visualizations

```bash
# Install Graphviz first (system package required)
sudo apt-get install graphviz  # Ubuntu/Debian
# brew install graphviz          # macOS

# Run visualization script
./scripts/run_visualizations.sh

# Or run directly with Python
source venv/bin/activate
python3 scripts/generate_visualizations.py
```

Generates 6 PNG visualizations in `visualizations/` folder:
- DFG (frequency & performance)
- Petri nets (Inductive & Alpha miners)
- Process tree
- BPMN diagram

See `scripts/README.md` for details.

## Configuration

### Structure

Event logs are configured using YAML files with the following sections:

```yaml
# Process metadata
process_name: "Your Process Name"
num_cases: 1000
seed: 42
start_date: "2024-01-01"

# Activities (chronological order)
activities:
  - step: 1
    id: start
    name: "Start Activity"
    type: automatic  # or "human"
    duration:
      min: 0  # hours
      max: 1
    next_steps:
      - activity: next_activity
        probability: 1.0

# Resource pools (for human activities)
resource_pools:
  clerks:
    - id: clerk_001
      name: "Alice"
      speed: 0.8        # 20% faster than average
      consistency: 0.9  # Low variance
      capacity: 1.0     # Standard capacity
```

### Example Configuration

See `configs/process_config.yaml` for a complete example modeling a restaurant permit application process with:
- 10 activities
- 5 process variants (Direct Approval 58%, Request More Info 24%, etc.)
- 3 resource pools (10 resources total)
- Anomaly knobs (random delays, peak times)

## Project Structure

```
event-log-gen/
├── configs/                    # Configuration examples
│   └── process_config.yaml    # Full example (628 lines, self-documenting)
├── docs/                       # Documentation
│   ├── ARCHITECTURE.md        # System architecture (1000+ lines)
│   ├── research_summary.md    # PM4Py/XES research & design
│   └── PROCESS_DEFINITION.md  # Original process specification
├── src/event_log_gen/         # Source code
│   ├── config/                # Configuration loading & validation
│   │   ├── loader.py          # YAML config loader
│   │   └── validator.py       # Schema & semantic validation
│   ├── core/                  # Event generation logic
│   │   └── generator.py       # Main generator (resource allocation, calendar)
│   └── exporters/             # Export formats
│       ├── csv_exporter.py    # PM4Py-compatible CSV
│       ├── parquet_exporter.py # Parquet export
│       ├── json_exporter.py   # JSON/NDJSON export
│       └── xes_exporter.py    # XES export via PM4Py
├── tests/                      # Test suite (135 tests, 80% coverage)
│   ├── test_config/           # Configuration tests
│   ├── test_core/             # Generator tests
│   ├── test_exporters/        # Exporter tests
│   ├── test_pm4py_compatibility.py  # PM4Py format tests
│   └── test_pm4py_visualization.py  # PM4Py discovery tests
├── scripts/                    # Utility scripts
│   ├── generate_visualizations.py   # PM4Py visualization generator
│   ├── run_visualizations.sh        # Wrapper with dependency checks
│   └── README.md              # Script documentation
├── examples/                   # Usage examples
│   └── basic_usage.py
├── output/                     # Generated event logs (gitignored)
└── visualizations/            # Generated PNG files (gitignored)
```

## Testing

### Run All Tests

```bash
pytest tests/ -v
```

### Run Specific Test Modules

```bash
# Configuration tests
pytest tests/test_config/ -v

# Generator tests
pytest tests/test_core/ -v

# CSV exporter tests
pytest tests/test_exporters/ -v
```

### Test Coverage

```bash
pytest tests/ --cov=event_log_gen --cov-report=html
```

View coverage report: `open htmlcov/index.html`

## PM4Py Compatibility

All exported logs are PM4Py-compatible:

### Column Names

| Internal Name | PM4Py/XES Name | Description |
|--------------|----------------|-------------|
| `case_id` | `case:concept:name` | Case identifier |
| `activity` | `concept:name` | Activity name |
| `timestamp` | `time:timestamp` | Event timestamp |
| `resource` | `org:resource` | Resource (person/system) |
| `lifecycle` | `lifecycle:transition` | Lifecycle state |

Custom attributes (e.g., `org:department`, `cost:amount`) are preserved with their namespace prefixes.

### PM4Py Usage

```python
import pm4py

# Import generated CSV
df = pm4py.read_csv('output/events.csv')
log = pm4py.convert_to_event_log(df)

# Discover process model
dfg, start_activities, end_activities = pm4py.discover_dfg(log)

# Filter log
from pm4py.algo.filtering.log.variants import variants_filter
filtered_log = variants_filter.apply(log)
```

## Configuration Validation

The validator checks:

✅ **Schema validation**: Required fields, types, structure
✅ **Probability validation**: next_steps probabilities sum to 1.0 (±0.001)
✅ **Duration validation**: min/max OR typical/spread (mutually exclusive)
✅ **Cross-references**: Activity IDs, resource pools exist
✅ **Semantic constraints**: min < max, probabilities 0-1, values > 0

Example:

```python
from event_log_gen import load_config, validate_config

config = load_config('configs/process_config.yaml')
result = validate_config(config)

if result.valid:
    print("✓ Valid")
else:
    print("✗ Errors:")
    for error in result.errors:
        print(f"  - {error}")

if result.warnings:
    print("⚠ Warnings:")
    for warning in result.warnings:
        print(f"  - {warning}")
```

## Roadmap

### ✅ Phase 4: Full Features (COMPLETE)
- [x] Parquet exporter (`pyarrow`)
- [x] JSON/NDJSON exporter
- [x] XES exporter (via `pm4py.write_xes`)
- [x] Full resource allocation (pools, performance profiles)
- [x] Working hours/calendar logic
- [x] Custom attributes (event & case level)
- [x] PM4Py compatibility tests (135 tests)
- [x] PM4Py visualization tests (DFG, Petri nets, BPMN, Process trees)
- [x] Visualization generation script

### Phase 5: CLI & Packaging (Next)
- [ ] Command-line interface with argparse
- [ ] Comprehensive user documentation
- [ ] Example configurations (baseline vs anomaly scenarios)
- [ ] Installation via pip (PyPI package)

### Phase 6: Final Integration
- [ ] Sample datasets (50 events each format)
- [ ] Full PM4Py workflow tests (import → discover → filter → export)
- [ ] Performance optimization (>100K cases)
- [ ] Production release (v1.0.0)

## Documentation

- **Architecture**: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) - Complete system design
- **Research**: [`docs/research_summary.md`](docs/research_summary.md) - PM4Py/XES research & design philosophy
- **Configuration**: [`configs/README.md`](configs/README.md) - Configuration guide
- **Process Spec**: [`docs/PROCESS_DEFINITION.md`](docs/PROCESS_DEFINITION.md) - Example process definition

## Contributing

This project follows a phased development approach. Currently accepting:
- Bug reports for Phase 1-3 features
- Documentation improvements
- Test coverage enhancements

Please wait for Phase 6 completion before submitting feature requests.

## License

MIT License - See LICENSE file for details

## Citation

If you use this tool in research, please cite:

```bibtex
@software{event_log_generator,
  title = {Event Log Generator: Synthetic Process Event Logs from YAML},
  author = {Your Name},
  year = {2024},
  version = {0.1.0},
  url = {https://github.com/yourusername/event-log-gen}
}
```

## Acknowledgments

- **PM4Py**: Process mining framework ([pm4py.org](https://pm4py.org))
- **IEEE XES Standard 1849-2023**: Event log format ([xes-standard.org](https://www.xes-standard.org))
- **Anthropic Claude**: AI assistance for development

---

**Status**: Phase 4 (Full Features) ✅ COMPLETE - All core features implemented, 135 tests passing, 80% coverage
