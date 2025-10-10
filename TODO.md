# Event Log Generator - Project TODO

## Overall Strategy
Build a Python application that generates realistic synthetic process event logs from a single YAML configuration file. Work incrementally with tests at each phase. **Critical**: Full PM4Py and XES compatibility, human-centric configuration design.

## Current Phase: Phase 4 - Full Features ✅ COMPLETE
**Status**: Phase 0-4 complete, all core features implemented!

**Phase 4 Progress** (2025-10-10):
- ✅ Parquet exporter with PM4Py schema mapping (19 lines, 79% coverage)
- ✅ JSON/NDJSON exporter with PM4Py field names (16 lines, 75% coverage)
- ✅ XES exporter via pm4py.write_xes() (19 lines, 79% coverage)
- ✅ PM4Py compatibility tests for all 3 new formats (18 tests)
- ✅ **Resource allocation**: capacity-weighted selection, speed multiplier, consistency variance
- ✅ **Working calendar**: business hours (9-5), weekends, holidays
- ✅ **Custom attributes**: event-level (cost:amount) and case-level (case:priority, case:applicant_type)
- ✅ **PM4Py visualization tests**: DFG, Petri net, BPMN, process tree (6 new tests)
- ✅ **Visualization script**: `scripts/generate_visualizations.py` generates 6 PNG visualizations

**Test Coverage Summary**:
- **Overall**: 80% coverage (609 statements, 122 missed)
- **Tests**: 135 passing, 1 skipped, 1 warning
- config/loader.py: 94%
- config/validator.py: 79%
- core/generator.py: 77% (259 statements)
- exporters/csv_exporter.py: 85%
- exporters/parquet_exporter.py: 79%
- exporters/json_exporter.py: 75%
- exporters/xes_exporter.py: 79%

**PM4Py Validation** ✅ **ALL FORMATS & ALGORITHMS TESTED**:
- ✅ **CSV**: pandas read, PM4Py format/convert, DFG discovery, statistics
- ✅ **Parquet**: pandas read, PM4Py format/convert, DFG discovery, CSV equivalence
- ✅ **JSON**: pandas read (NDJSON), PM4Py format/convert, DFG discovery
- ✅ **XES**: pm4py.read_xes() reads files, full schema compliance, process discovery
- ✅ **Process Discovery**: DFG (frequency & performance), Alpha miner, Inductive miner
- ✅ **Model Types**: Petri nets, Process trees, BPMN
- ✅ **Visualization Generation**: Script creates 6 PNG files (requires Graphviz system package)
- ⏳ Custom attributes preservation (Phase 4 feature - test ready, skipped due to test format)

**Visualization Script** (scripts/generate_visualizations.py):
- Generates 100-case event log from real config (restaurant permit process)
- Creates 6 visualizations: DFG frequency, DFG performance, 2x Petri nets, Process tree, BPMN
- Saves as PNG files to visualizations/ folder
- Requires Graphviz system package: `sudo apt-get install graphviz`
- Run with: `./scripts/run_visualizations.sh` (checks dependencies, activates venv)
- See: `scripts/README.md` for full documentation

**Next**: Phase 5 - CLI & Packaging

## Phases

### ✅ Phase 0: Research & Analysis
- [x] Read and analyze PROCESS_DEFINITION.md
- [x] Conduct literature review (IEEE XES, PM4Py, synthetic generation)
- [x] Produce research_summary.md with citations
- [x] Update research_summary with PM4Py/XES compatibility requirements
- [x] Add human-centric design philosophy and semantic constraints
- [x] Clarify probability distribution formats (min/max default, typical/spread optional)
- **Expected Output**: research_summary.md ✅ **COMPLETED**

### ✅ Phase 1: Configuration Schema Design
- [x] Design process_config.yaml with human-centric chronological structure
- [x] Add rich inline comments for self-documentation
- [x] Use semantic naming (meaningful names, not codes)
- [x] Create minimal example for restaurant permit process (all 5 variants)
- [x] **NEW**: Define custom attributes schema (event & case level with XES namespaces)
- [x] Implement schema validation (pyyaml + jsonschema)
- [x] Validate PM4Py column naming conventions
- [x] **NEW**: Validate duration format (min/max OR typical/spread, not both)
- **Expected Output**: process_config.yaml (self-documenting), schema validator ✅ **COMPLETED**
- **Key Requirements**: ✅ All met
  - Activities in chronological order with step numbers
  - Inline comments explain all parameters with tuning guidance
  - Duration: ONE format per transition (min/max OR typical/spread)
  - Custom attributes section with namespace conventions (org:, cost:, location:, case:)
  - Next_steps probabilities sum to 1.0
  - Non-technical users can modify without external docs
- **Status**: 628 lines config, 508 lines validator, 50+ validation tests

### ✅ Phase 2: Architecture Design
- [x] Define module structure (config loader, generator, exporters)
- [x] Document data flow and responsibilities
- [x] Select tech stack details
- [x] **NEW**: Document PM4Py/XES column mapping strategy
- **Expected Output**: ARCHITECTURE.md ✅ **COMPLETED** (600+ lines)

### ✅ Phase 3: Minimal Generator (CSV only)
- [x] Implement seeded RNG
- [x] Build core event generation loop
- [x] Add variant selection logic
- [x] Implement basic time transitions (min/max uniform distribution)
- [x] CSV exporter with PM4Py-compatible column names (including custom attributes)
- [x] **NEW**: Handle custom event attributes with XES namespaces (org:, cost:, location:)
- [x] **NEW**: Handle case-level attributes with case: prefix
- [x] Write tests (reproducibility, schema, variant distribution)
- [x] **NEW**: Test custom attributes export correctly to CSV
- [x] **CRITICAL PM4Py Validation Tests** ✅ **ALL PASSING**:
  - [x] Test pandas can read generated CSV
  - [x] Test `pm4py.format_dataframe()` accepts generated DataFrame
  - [x] Test `pm4py.convert_to_event_log()` converts DataFrame to EventLog
  - [x] Test `pm4py.discover_dfg()` can discover process model from log
  - [x] Test `pm4py.get_start_activities()` and `pm4py.get_end_activities()` work
  - [⏳] Test custom attributes are preserved (Phase 4 feature, test ready)
- **Expected Output**: Working generator for 10 cases, pytest suite with PM4Py integration tests ✅ **COMPLETE**
- **Validation**: Generated CSV has PM4Py column names, ready for PM4Py import ✅ **VALIDATED**
- **Status**: ✅ **COMPLETE** - 83 tests passing (86% coverage), 6/6 PM4Py tests passing

### ✅ Phase 4: Full Features (COMPLETE)
- [x] Add Parquet exporter (pyarrow) with PM4Py column names + custom attributes
- [x] Add JSON exporter (NDJSON) with PM4Py field names + custom attributes
- [x] **NEW**: Add XES exporter (via pm4py.write_xes) - validates custom attributes work in XES
- [x] **CRITICAL PM4Py Validation Tests (Export Formats)**:
  - [x] Test pandas can read generated Parquet files
  - [x] Test PM4Py format_dataframe() accepts Parquet-loaded DataFrames
  - [x] Test PM4Py discover_dfg() works with Parquet format
  - [x] Test CSV-Parquet equivalence (same EventLog structure)
  - [x] Test pandas can read generated JSON files (NDJSON)
  - [x] Test PM4Py format_dataframe() accepts JSON-loaded DataFrames
  - [x] Test PM4Py discover_dfg() works with JSON format
  - [x] Test pm4py.read_xes() can read generated XES files
  - [x] Test XES schema compliance (all standard attributes)
  - [x] Test PM4Py process discovery works with XES format
- [x] Implement resource pools with performance characteristics (speed, consistency, capacity)
- [x] Add working hours/calendar logic (business hours 9-5, weekends, holidays)
- [x] Implement custom attributes (event-level: cost:amount, case-level: case:priority, case:applicant_type)
- [x] **PM4Py Process Discovery Tests**:
  - [x] Test DFG frequency discovery
  - [x] Test DFG performance discovery
  - [x] Test Petri net discovery (Alpha miner)
  - [x] Test Petri net discovery (Inductive miner)
  - [x] Test Process tree discovery
  - [x] Test BPMN discovery
- [x] **Visualization Script** (scripts/generate_visualizations.py):
  - [x] Create script to generate 6 PM4Py visualizations as PNG files
  - [x] Add wrapper script with Graphviz dependency check
  - [x] Document usage in scripts/README.md
- **Expected Output**: Complete feature set, extended tests, all exports fully PM4Py-compatible
- **Status**: ✅ **COMPLETE** - 135 tests passing (80% coverage), 6 PM4Py visualization tests + visualization script

### Phase 5: CLI & Packaging
- [ ] Create CLI with argparse
- [ ] Write comprehensive README
- [ ] Document example commands
- [ ] Create baseline vs anomaly scenarios
- **Expected Output**: CLI interface, usage documentation

### Phase 6: Final Integration
- [ ] Complete test suite (>80% coverage)
- [ ] Generate events_sample.* (50 events each format: CSV, Parquet, JSON, XES)
- [ ] **CRITICAL PM4Py Full Workflow Test**:
  - [ ] Run complete PM4Py workflow: import → discover → filter → export
  - [ ] Test `pm4py.view_dfg()` visualization works (smoke test)
  - [ ] Validate PM4Py can compute performance metrics (throughput, cycle time)
  - [ ] Document which PM4Py functions were tested in USER_GUIDE.md
- [ ] Validate acceptance criteria
- [ ] Final documentation review
- **Expected Output**: Production-ready application with proven PM4Py compatibility

## Key Design Decisions

### Technical Stack
- Python 3.10+ for modern type hints
- pandas for data manipulation (PM4Py standard)
- pyarrow for Parquet support
- pyyaml for configuration (human-readable)
- pytest for testing
- Seeded RNG for reproducibility

### PM4Py/XES Compatibility
- **Export column names**: `case:concept:name`, `concept:name`, `time:timestamp`, `org:resource`, `lifecycle:transition`
- **Internal names**: `case_id`, `activity`, `timestamp`, `resource`, `lifecycle` (mapped on export)
- **4 export formats**: CSV, Parquet, JSON (NDJSON), XES (all PM4Py-compatible)

### Configuration Design
- **Human-centric**: Chronological activity structure with rich inline comments
- **Self-documenting**: Non-technical users can modify without reading external docs
- **Semantic naming**: "intake_clerk" not "res_001", "review_duration" not "dur"
- **Duration formats**: min/max (uniform, default) OR typical/spread (normal, optional) - one per transition
- **Custom attributes**: Event-level (org:, cost:, location:) and case-level (case:) with XES namespaces

### Data Generation
- **Semantic constraints**: Resource profiles (speed, consistency, capacity), workload effects, domain knowledge
- **Realism factors**: Fatigue modeling, random delays (5%), peak times (30%), rework loops
- **Ground truth metadata**: Seed, variant assignments, config file reference for validation

## Notes
- Always test before moving to next phase
- Update this file after each completed task
- Document assumptions when design choices are ambiguous
- **CRITICAL**: All exports must be directly importable into PM4Py without user intervention
