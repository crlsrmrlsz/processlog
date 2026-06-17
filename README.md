# ProcessLog

> Generate realistic synthetic event logs for building and testing process-mining software.

[![PyPI](https://img.shields.io/pypi/v/processlog.svg)](https://pypi.org/project/processlog/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![license: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

ProcessLog turns a small YAML description of a process into a realistic event log
— seeded and reproducible, with resource pools, working calendars, probabilistic
variants, and custom attributes — and exports it as CSV, NDJSON, Parquet, or IEEE
XES. Every format imports straight into [PM4Py](https://pm4py.org), no reshaping.

It's the data source for when you're developing a process-mining tool and don't
have (or can't share) real logs.

## What it is

```
   process definition          ProcessLog              event log
       (YAML)        ──────▶   generate, seeded   ──▶  CSV · NDJSON · Parquet · XES
                                                        PM4Py-ready · IEEE XES 1849-2023
```

- **Standards-clean output** — CSV, NDJSON, Parquet, and XES, all directly
  importable into PM4Py; XES is IEEE 1849-2023 compliant with proper namespaces.
- **Realistic dynamics** — resource pools with speed/consistency, working
  calendars (business hours, weekends, holidays), probabilistic branching into
  named process variants, and domain attributes (cost, priority, region, …).
- **Reproducible** — a seed pins the entire run, so regression fixtures stay
  byte-stable.
- **Configured, not coded** — one self-documenting YAML file describes the whole
  process.

**Pairs with [mining-lib](https://github.com/crlsrmrlsz/mining-lib)** — the logs
you generate here render directly in it, an embeddable browser viewer for
interactive Directly-Follows Graphs.

## Example

A few rows of a generated CSV — the standard XES column names, ready for PM4Py:

```csv
case:concept:name,concept:name,time:timestamp,org:resource,lifecycle:transition
case_0001,submitted,2024-01-02 09:00:00-05:00,,complete
case_0001,intake_validation,2024-01-02 10:30:00-05:00,clerk_002,complete
case_0001,review_in_progress,2024-01-03 09:15:00-05:00,reviewer_001,complete
case_0001,approved,2024-01-05 14:20:00-05:00,reviewer_001,complete
```

Drop that log into mining-lib and you get an interactive process map:

[![A ProcessLog-generated log rendered as an interactive Directly-Follows Graph in mining-lib.](https://raw.githubusercontent.com/crlsrmrlsz/processlog/main/docs/demo.png)](https://crlsrmrlsz.github.io/mining-lib/)

## How to use

```sh
pip install processlog          # add [xes] for XES export: pip install "processlog[xes]"
```

Generate a log from a config — the CLI is the quickest path:

```sh
processlog generate -c configs/process_config.yaml -n 1000   # 1000 cases, all formats
processlog validate -c configs/process_config.yaml           # check a config
processlog info     -c configs/process_config.yaml           # summarise the process
```

Or from Python:

```python
from processlog import load_config, generate_log, export_csv

config = load_config("configs/process_config.yaml")
df = generate_log(config, seed=42, num_cases=1000)
export_csv(df, "events.csv")
```

The full CLI, Python API, config schema, and output format live in
**[docs/USAGE.md](docs/USAGE.md)**.

## Develop

```sh
git clone https://github.com/crlsrmrlsz/processlog.git
cd processlog
python3 -m venv venv && source venv/bin/activate
pip install -e ".[dev]"
pytest
```

## License

MIT — see [LICENSE](LICENSE).
