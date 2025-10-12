# Event Log Generator

> Generate realistic synthetic process event logs for testing and developing process mining software

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)


## Purpose

Event Log Generator creates synthetic process event logs specifically designed for **developing and testing process mining software**. Whether you're building process mining tools, testing PM4Py algorithms, or validating event log processing pipelines, this tool provides realistic, customizable test data that conforms to industry standards (XES, PM4Py).

**Why use synthetic data?**
- 🔒 **No privacy concerns** - Generate unlimited test data without exposing real business processes
- 🎯 **Controlled scenarios** - Create specific edge cases, anomalies, and process variants for testing
- 🔁 **Reproducible** - Seeded generation ensures identical outputs for regression testing
- 📊 **Multiple formats** - Test your software's compatibility with CSV, Parquet, JSON, and XES formats

## Features

- **PM4Py-first design**: All exports directly importable into PM4Py without reformatting
- **IEEE XES 1849-2023 compliant**: Standard-conformant event logs with proper namespaces
- **Human-readable configuration**: YAML files with inline documentation
- **Realistic process dynamics**: Resource allocation, working calendars, performance variations
- **Custom attributes**: Add domain-specific attributes (cost, priority, locations, etc.)
- **Process variants**: Probabilistic branching generates multiple execution paths
- **Export formats**: CSV, Parquet, JSON (NDJSON), XES
- **Reproducible**: Seeded RNG for deterministic testing
- **Fast**: Generate 100K+ events in seconds


## Installation

### From Source

```bash
# Clone the repository
git clone https://github.com/crlsrmrlsz/event-log-gen.git
cd event-log-gen

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .
```

### Dependencies

- Python 3.10+
- pandas >= 2.0.0
- pyyaml >= 6.0
- pyarrow >= 12.0.0
- pm4py >= 2.7.0
- jsonschema >= 4.17.0

All dependencies are automatically installed with `pip install -e .`

## Quick Start

### CLI Usage (Recommended)

```bash
# Generate event logs (timestamped run folder, all formats)
event-log-gen generate -c configs/process_config.yaml -n 1000

# Generate with custom run name
event-log-gen generate -c configs/process_config.yaml -n 1000 --run-name experiment_v2

# Generate only CSV format to specific folder (backward compatible)
event-log-gen generate -c configs/process_config.yaml -n 100 -f csv -o output/

# Generate without timestamps (flat output for CI/CD)
event-log-gen generate -c configs/process_config.yaml -n 100 --no-timestamp

# Validate configuration
event-log-gen validate -c configs/process_config.yaml

# View process information
event-log-gen info -c configs/process_config.yaml

# Generate with custom seed
event-log-gen generate -c configs/process_config.yaml -s 123 -n 500
```

### Python API Usage

```python
from event_log_gen import (
    load_config, validate_config, generate_log,
    export_csv, export_parquet, export_json, export_xes
)

# Load and validate configuration
config = load_config('configs/process_config.yaml')
result = validate_config(config)

if not result.valid:
    print("Configuration errors:", result.errors)
    exit(1)

# Generate 1000 cases with reproducible seed
df = generate_log(config, seed=42, num_cases=1000)

# Export to PM4Py-compatible formats
export_csv(df, 'output/events.csv')
export_parquet(df, 'output/events.parquet')
export_json(df, 'output/events.json')
export_xes(df, 'output/events.xes')

print(f"Generated {len(df)} events across {df['case_id'].nunique()} cases")
```

### Run the Example

```bash
python examples/basic_usage.py
```

This generates a small event log (10 cases) from the restaurant permit process and displays statistics.

### Test with PM4Py

```python
import pm4py

# Load generated event log
df = pm4py.read_csv('output/events.csv')
log = pm4py.convert_to_event_log(df)

# Discover process model
dfg, start_activities, end_activities = pm4py.discover_dfg(log)

# Generate visualization (requires Graphviz)
pm4py.view_dfg(dfg, start_activities, end_activities)
```

## Configuration

Event logs are defined using self-documenting YAML files. Here's a minimal example:

```yaml
process_name: "Order Fulfillment"
num_cases: 100
seed: 42
start_date: "2024-01-01"

activities:
  - step: 1
    id: order_received
    name: "Order Received"
    type: automatic
    duration: {min: 0, max: 0.1}  # hours
    next_steps:
      - activity: payment_check
        probability: 1.0

  - step: 2
    id: payment_check
    name: "Payment Validation"
    type: human
    resource_pool: clerks
    duration: {min: 0.5, max: 2.0}
    next_steps:
      - activity: approved
        probability: 0.95
      - activity: rejected
        probability: 0.05

resource_pools:
  clerks:
    - id: clerk_01
      name: "Alice"
      speed: 1.0      # Normal speed
      consistency: 0.9  # Low variance
      capacity: 1.0   # Standard workload
```

### Example Configuration

See [`configs/process_config.yaml`](configs/process_config.yaml) for a complete example of a restaurant permit process with:
- 10 activities with probabilistic branching
- 5 process variants (approval, rejection, withdrawal, etc.)
- 3 resource pools with 10 workers
- Working calendar (business hours, weekends, holidays)
- Custom attributes (cost, priority, location)

## Output Structure

Event logs are organized in **timestamped run folders** by default for better organization and reproducibility:

```
output/
├── runs/
│   ├── 20241012_143022_permit_n1000_s42/
│   │   ├── events.csv
│   │   ├── events.parquet
│   │   ├── events.json
│   │   ├── events.xes
│   │   └── run_metadata.json
│   └── 20241012_150815_permit_n5000_s123/
│       └── ...
└── latest -> runs/20241012_150815_permit_n5000_s123/  (symlink)
```

**Folder naming**: `YYYYMMDD_HHMMSS_{process_name}_n{cases}_s{seed}/`
- Chronologically sorted (ISO 8601 timestamp)
- Self-documenting (parameters embedded in name)
- Non-destructive (each run preserved separately)

**Metadata file** (`run_metadata.json`):
```json
{
  "generator_version": "1.0.0",
  "generated_at": "2024-10-12T14:30:22.855153",
  "process_name": "Restaurant Permit Application",
  "num_cases": 1000,
  "num_events": 7234,
  "seed": 42,
  "statistics": {
    "mean_cycle_time_hours": 489.6,
    "mean_events_per_case": 7.2
  },
  "activity_distribution": {...},
  "resource_utilization": {...},
  "git_commit": "903aab0",
  "cli_command": "event-log-gen generate ..."
}
```

**CLI Options**:
- Use `-o path/` to specify custom output directory (disables timestamping)
- Use `--no-timestamp` for flat output in `output/` (CI/CD mode)
- Use `--run-name custom` to override process name in folder
- Symlink `output/latest` always points to most recent run (if enabled)

## Use Cases

### For Process Mining Tool Developers
- Test your software with realistic event logs before accessing real data
- Generate edge cases and anomalies for robust error handling
- Benchmark performance with large datasets (100K+ events)
- Validate PM4Py compatibility and XES standard conformance

### For Researchers
- Create reproducible datasets for academic papers
- Test process discovery algorithms with known ground truth
- Compare algorithm performance across different process structures
- Generate baseline and anomaly scenarios for evaluation

### For Software Testers
- Generate regression test datasets with fixed seeds
- Create integration test data for process mining pipelines
- Test data format conversions (CSV ↔ Parquet ↔ JSON ↔ XES)
- Validate event log validators and quality checkers

## PM4Py & XES Compatibility

All generated event logs are **directly importable** into PM4Py without any preprocessing or column renaming.

### Supported Formats

| Format | Extension | PM4Py Function | IEEE XES Standard |
|--------|-----------|----------------|-------------------|
| CSV | `.csv` | `pm4py.read_csv()` | Column names compliant |
| Parquet | `.parquet` | Load with pandas → PM4Py | Column names compliant |
| JSON | `.json` | Load with pandas → PM4Py | NDJSON format |
| XES | `.xes` | `pm4py.read_xes()` | IEEE 1849-2023 ✓ |

### XES Standard Attributes

| Internal | XES/PM4Py Name | Type |
|----------|----------------|------|
| `case_id` | `case:concept:name` | String |
| `activity` | `concept:name` | String |
| `timestamp` | `time:timestamp` | Timestamp |
| `resource` | `org:resource` | String |
| `lifecycle` | `lifecycle:transition` | String |

Custom attributes use proper XES namespaces (e.g., `cost:amount`, `org:department`, `case:priority`).

### Tested PM4Py Functions

✅ **Import/Export**: `read_csv()`, `read_xes()`, `write_xes()`, `convert_to_event_log()`
✅ **Discovery**: `discover_dfg()`, `discover_petri_net_inductive()`, `discover_petri_net_alpha()`
✅ **Models**: DFG, Petri nets, Process trees, BPMN diagrams
✅ **Statistics**: `get_start_activities()`, `get_end_activities()`, variant analysis

See [test suite](tests/) for complete PM4Py compatibility validation.

## Development & Testing

```bash
# Run all tests
pytest tests/ -v

# Generate coverage report
pytest tests/ --cov=event_log_gen --cov-report=html

# Validate a configuration
python -c "from event_log_gen import load_config, validate_config; \
           result = validate_config(load_config('configs/process_config.yaml')); \
           print('Valid!' if result.valid else result.errors)"
```

## Documentation

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) - System design and module structure
- [`docs/research_summary.md`](docs/research_summary.md) - PM4Py/XES research and design philosophy
- [`configs/process_config.yaml`](configs/process_config.yaml) - Annotated configuration example

## Contributing

Contributions are welcome! This project is designed to help the process mining community develop and test their software.

**Ways to contribute:**
- 🐛 Report bugs or issues
- 📝 Improve documentation
- ✨ Add new example configurations
- 🧪 Expand test coverage
- 🔧 Suggest new features

Please open an issue first to discuss significant changes.

## License

MIT License - see [LICENSE](LICENSE) file for details.

This project is free and open-source software designed to support process mining research and development.

## Citation

If you use this tool in academic research, please cite:

```bibtex
@software{event_log_generator_2024,
  title = {Event Log Generator: Synthetic Process Event Logs for Testing},
  author = {Romer, Karl},
  year = {2024},
  url = {https://github.com/crlsrmrlsz/event-log-gen},
  note = {Process mining test data generator with PM4Py and XES compatibility}
}
```

## Acknowledgments

- **PM4Py** - Process Mining for Python ([pm4py.org](https://pm4py.org))
- **IEEE XES Standard** - eXtensible Event Stream format ([xes-standard.org](https://www.xes-standard.org))
- **Process Mining Community** - For advancing the field of process analytics

---

**Version**: 1.0.0 | **Status**: Production/Stable | **License**: MIT
