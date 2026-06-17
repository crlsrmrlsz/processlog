# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.1] - 2026-06-17

### Fixed
- **README hero image now renders on PyPI.** The `rendered-in-mining-lib`
  screenshot used a repo-relative path, which PyPI's description renderer does
  not resolve; switched it to an absolute `raw.githubusercontent.com` URL so the
  image shows on PyPI as well as on GitHub and npm. Docs-only; no code changes.

## [1.2.0] - 2026-05-28

### Added
- **`emit_labels` config flag (default `false`).** When set `true` at the top
  level of the YAML config, the generator emits each activity's `name:` to
  `concept:name` and each selected human resource's `name:` to `org:resource`
  (with safe fallback to `id` when `name:` is absent). Internal flow,
  `next_steps`, variant tracking, capacity-weighted resource selection, and
  workload tracking all remain id-keyed — only the externally-visible strings
  change. Lets downstream consumers ship demo datasets with human-readable
  labels (e.g. `"Application Submitted"`, `"Rachel Greene"`) without
  reshaping the engine. Backward-compatible: legacy configs that don't set
  the flag regenerate byte-for-byte as before.

## [1.1.0] - 2026-05-27

Audited and vetted for downstream consumption by process-mining tools.

### Changed
- **pm4py is now an optional `[xes]` extra.** The core install (CSV / JSON /
  Parquet generation) no longer pulls pm4py or its heavy transitive deps
  (scipy, graphviz, networkx). Install `processlog[xes]` for XES export.
  `generate -f all` skips XES with a warning when pm4py is absent; an explicit
  `-f xes` without it fails with an actionable message.

### Fixed
- **JSON timestamp precision.** The NDJSON exporter floored timestamps to whole
  seconds (its format string had no microsecond directive); it now preserves
  sub-second precision and is byte-identical to the CSV exporter.
- **pandas >= 3.0 compatibility.** Parquet string columns read back as
  `StringDtype`; the affected test accepts both `StringDtype` and `object`.

### Added
- LOG_FORMAT_SPEC v1.1 conformance test suite (`tests/test_contract_conformance.py`).
- Python 3.13 classifier (verified on 3.13).

### Notes
- Documented that resource fatigue, random delays, and peak-time slowdowns are
  config-validated but **not yet implemented** by the engine (Known Limitations §6).

## [1.0.0] - 2024-10-12

### Added
- **Timestamped Run Folders**: Event logs now output to `output/runs/YYYYMMDD_HHMMSS_process_n{cases}_s{seed}/` by default
- **Run Metadata Export**: Automatic `run_metadata.json` generation with statistics, git commit, CLI command, and more
- **New CLI Flags**:
  - `--run-name TEXT` - Custom run name override
  - `--no-timestamp` - Disable timestamped folders (flat output for CI/CD)
  - `--link-latest` - Create/update symlink to latest run (default: true)
- **Enhanced Metadata**: Git commit tracking, CLI command logging, comprehensive statistics
- **4 Export Formats**: CSV, Parquet, JSON (NDJSON), XES
- **PM4Py/XES Compatibility**: IEEE 1849-2023 standard compliance
- **Seeded Generation**: Reproducible outputs with fixed seeds
- **Resource Management**: Capacity-weighted allocation, speed/consistency profiles, fatigue modeling
- **Working Calendar**: Business hours (9-5), weekends, holidays
- **Custom Attributes**: Event-level and case-level with XES namespaces
- **Process Variants**: Probabilistic branching generates multiple execution paths
- **CLI Interface**: 3 commands (generate, validate, info)
- **Python API**: Full programmatic access to all features
- **Comprehensive Documentation**: README, ARCHITECTURE, research summary, example configs
- **Test Suite**: 164 tests with 80% coverage on core modules
- **PM4Py Integration Tests**: All discovery algorithms validated

### Changed
- **Output Default**: Changed from flat `output/` to timestamped `output/runs/{timestamp}/`
- **CLI `-o` flag**: No longer has default value, enabling timestamped mode when omitted
- **Config Validator**: Now accepts string step identifiers (e.g., "5a", "7b") for parallel activities

### Fixed
- Configuration validation warnings for string-based step values
- Backward compatibility maintained via explicit `-o` path or `--no-timestamp` flag

## [Unreleased]

### Future Enhancements
- Multi-process generation for 10M+ cases
- Incremental export for memory efficiency
- Custom exporter plugins
- GUI configuration editor
- Advanced semantics (inter-case dependencies, learning curves)
- Model export (BPMN, Petri nets)
- Database export (PostgreSQL, MongoDB)

---

[1.1.0]: https://github.com/crlsrmrlsz/processlog/releases/tag/v1.1.0
[1.0.0]: https://github.com/crlsrmrlsz/processlog/releases/tag/v1.0.0
