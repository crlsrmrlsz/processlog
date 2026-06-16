# Usage reference

The complete CLI, Python API, configuration schema, and output format. For the
quick start see the [README](../README.md); for the shape of the generated log
see [OUTPUT_DESCRIPTION](OUTPUT_DESCRIPTION.md), and for the example process see
[PROCESS_DEFINITION](PROCESS_DEFINITION.md).

- [Install](#install)
- [CLI](#cli)
- [Python API](#python-api)
- [Configuration](#configuration)
- [Output](#output)
- [PM4Py & XES compatibility](#pm4py--xes-compatibility)

---

## Install

```sh
pip install processlog            # core: CSV, NDJSON, Parquet
pip install "processlog[xes]"     # adds XES export (pulls pm4py + its deps)
```

Or from source:

```sh
git clone https://github.com/crlsrmrlsz/processlog.git
cd processlog
python3 -m venv venv && source venv/bin/activate
pip install -e ".[dev]"
```

Python 3.10+. Core dependencies: `pandas`, `pyyaml`, `pyarrow`, `jsonschema`.
XES export additionally needs `pm4py` (kept optional because it pulls heavy
transitive deps — scipy, graphviz, networkx).

## CLI

Three subcommands: `generate`, `validate`, `info`.

```sh
processlog generate -c configs/process_config.yaml -n 1000
processlog validate -c configs/process_config.yaml
processlog info     -c configs/process_config.yaml
```

### `generate`

| Flag | Default | Meaning |
|---|---|---|
| `-c`, `--config` | *(required)* | path to the YAML config |
| `-n`, `--cases` | from config | number of cases to generate (overrides config) |
| `-s`, `--seed` | from config | random seed (overrides config) |
| `-f`, `--format` | `all` | one or more of `csv` `parquet` `json` `xes` `all` |
| `-o`, `--output` | timestamped run folder | output directory (setting it disables timestamping) |
| `--run-name` | from process name | custom run-folder name |
| `--no-timestamp` | off | write to a flat directory instead of a timestamped run folder |
| `--link-latest` | on | update the `latest` symlink to point at this run |

```sh
# CSV only, into a flat folder (handy for CI)
processlog generate -c configs/process_config.yaml -n 100 -f csv -o output/ --no-timestamp

# A named, seeded run in every format
processlog generate -c configs/process_config.yaml -n 5000 -s 123 --run-name experiment_v2
```

### `validate` / `info`

`validate -c <config>` checks the config against the schema and reports errors.
`info -c <config>` prints a summary of the process (activities, variants,
resources) without generating anything.

## Python API

```python
from processlog import (
    load_config, validate_config, generate_log,
    export_csv, export_parquet, export_json, export_xes, export_metadata,
)

config = load_config("configs/process_config.yaml")

result = validate_config(config)
if not result.valid:
    raise SystemExit(result.errors)

# A pandas DataFrame with the standard XES columns.
df = generate_log(config, seed=42, num_cases=1000)

export_csv(df, "output/events.csv")
export_parquet(df, "output/events.parquet")
export_json(df, "output/events.json")     # NDJSON
export_xes(df, "output/events.xes")       # requires processlog[xes]

print(f"{len(df)} events across {df['case:concept:name'].nunique()} cases")
```

## Configuration

A process is one self-documenting YAML file. Minimal shape:

```yaml
process_name: "Order Fulfillment"
num_cases: 100
seed: 42
start_date: "2024-01-01"

activities:
  - step: 1
    id: order_received
    name: "Order Received"
    type: automatic            # automatic | human
    duration: { min: 0, max: 0.1 }   # hours
    next_steps:
      - activity: payment_check
        probability: 1.0

  - step: 2
    id: payment_check
    name: "Payment Validation"
    type: human
    resource_pool: clerks
    duration: { min: 0.5, max: 2.0 }
    next_steps:
      - activity: approved
        probability: 0.95
      - activity: rejected
        probability: 0.05

resource_pools:
  clerks:
    - id: clerk_01
      name: "Alice"
      speed: 1.0          # >1 faster, <1 slower
      consistency: 0.9    # lower = more duration variance
      capacity: 1.0
```

- **Activities** carry a `step`, `id`, display `name`, a `type` (`automatic` has
  no resource; `human` draws from a `resource_pool`), a `duration` range in
  hours, and weighted `next_steps`. Probabilistic branching across `next_steps`
  is what produces distinct process **variants**.
- **Resource pools** model workers with `speed`, `consistency`, and `capacity`.
- **Optional top-level keys** add a working calendar (business hours, weekends,
  holidays), case- and event-level **custom attributes** (e.g. `cost:amount`,
  `case:priority`), and `emit_labels: true` to write human-readable activity and
  resource names into `concept:name` / `org:resource` (default off — ids emit).

A complete, annotated example — a restaurant-permit process with 10 activities,
5 variants, 3 resource pools, a working calendar, and custom attributes — ships
at [`configs/process_config.yaml`](../configs/process_config.yaml). Its structure
is documented in [PROCESS_DEFINITION](PROCESS_DEFINITION.md).

## Output

By default each run lands in a timestamped, self-describing folder so runs never
clobber each other:

```
output/
├── runs/
│   └── 20241012_143022_permit_n1000_s42/
│       ├── events.csv
│       ├── events.parquet
│       ├── events.json          # NDJSON
│       ├── events.xes
│       └── run_metadata.json
└── latest -> runs/20241012_143022_permit_n1000_s42/
```

`run_metadata.json` records the generator version, parameters (cases, seed,
dates, timezone), the column schema, and summary statistics (mean cycle time,
events per case) — enough to reproduce or audit the run. The exact field-by-field
schema is in [OUTPUT_DESCRIPTION](OUTPUT_DESCRIPTION.md).

## PM4Py & XES compatibility

Every format imports into PM4Py with no column renaming.

| Format | Extension | Load with | Notes |
|---|---|---|---|
| CSV | `.csv` | `pm4py.read_csv()` | XES-compliant column names |
| Parquet | `.parquet` | pandas → PM4Py | XES-compliant column names |
| JSON | `.json` | pandas → PM4Py | NDJSON (one object per line) |
| XES | `.xes` | `pm4py.read_xes()` | IEEE 1849-2023 |

The mandatory columns use the standard XES names — `case:concept:name`,
`concept:name`, `time:timestamp`, `org:resource`, `lifecycle:transition` — and
custom attributes use proper namespaces (`cost:amount`, `case:priority`, …).

```python
import pm4py

df = pm4py.read_csv("output/events.csv")
log = pm4py.convert_to_event_log(df)
dfg, start, end = pm4py.discover_dfg(log)
```

PM4Py import/discovery coverage is exercised by the test suite
(`tests/test_pm4py_*`).
