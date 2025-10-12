# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

[1.0.0]: https://github.com/crlsrmrlsz/event-log-gen/releases/tag/v1.0.0
