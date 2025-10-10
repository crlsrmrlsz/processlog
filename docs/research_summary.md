# Research Summary: Process Mining Event Log Generation

**Date**: 2025-10-07
**Purpose**: Literature review and schema design for synthetic event log generator

---

## 1. Process Definition Analysis

### 1.1 Process Overview
The reference process (`PROCESS_DEFINITION.md`) models a **restaurant permit application workflow** with the following characteristics:

**Entities**:
- **10 states**: submitted, intake_validation, assigned_to_reviewer, review_in_progress, request_additional_info, applicant_provided_info, health_inspection, approved, rejected, withdrawn
- **3 resource pools**: Clerks (3), Reviewers (4), Health Inspectors (3)
- **5 process variants**: Direct Approval (58%), Request More Info (24%), Rejected at Final (10%), Withdrawn (5%), Early Rejection (3%)

**Key Characteristics**:
- **State taxonomy**: Final states (approved/rejected/withdrawn), human-performed states (intake_validation, review_in_progress, health_inspection), automatic states (submitted, assigned_to_reviewer, etc.)
- **Resource performance profiles**: Each resource has speed (0.7-1.4×), consistency (0.6-1.0), and capacity (0.8-1.5) multipliers
- **Transition times**: Range from 6 minutes (automatic assignment) to 14 days (re-review after additional info)
- **Realism factors**: Resource fatigue, random delay events (5% probability), peak time effects (30% probability), workload-based assignment

### 1.2 Traced Attributes
- **Core event fields**: case_id, activity, timestamp, attributes (flexible JSON object)
- **Resource attribute**: `attributes.resource` contains resource_id (e.g., "clerk_001") or null for automatic activities
- **Generic design**: Attribute-agnostic model allows arbitrary contextual attributes

### 1.3 Expected Statistics
- **Variant distribution**: Should match configured probabilities within ±3-5% for 3000+ cases
- **Temporal patterns**: Long-duration transitions (2-14 days for re-reviews), short transitions (6-30 min for automation)
- **Resource utilization**: High-capacity resources handle 1.2-1.5× more cases
- **Anomalies**: ~5% of transitions show 2-4× duration outliers

---

## 2. Process Mining Literature Review

### 2.1 IEEE XES Standard (1849-2023)

**Key Findings**:
- The **IEEE XES (eXtensible Event Stream) Standard 1849-2023** is the authoritative format for process mining event logs, updated from 1849-2016 and active until 2033
- **Hierarchical structure**: Log → Traces → Events, where each element can have multiple typed attributes
- **Attribute types**: Seven types (six simple + one list type) provide extensibility
- **Standard extensions**: Concept extension defines standard names (case ID for traces, activity name for events, process name for logs)
- **Tool support**: XES is natively supported by Disco, Celonis, ProM, PM4Py, Rialto Process, minit, and SNP

**Citation**:
> IEEE Task Force on Process Mining. (2023). *IEEE XES Standard 1849-2023*. Retrieved from https://www.xes-standard.org/ and https://www.tf-pm.org/resources/xes-standard

**Impact on Design**:
- Adopt XES-compatible schema with case_id, activity, and timestamp as core fields
- Use flexible attribute dictionary to support extensions
- Provide conversion path to XES if needed (via PM4Py)

### 2.2 PM4Py Conventions and CSV Format

**Key Findings**:
- **PM4Py** is the de-facto Python library for process mining, using pandas DataFrames as the primary data structure
- **Minimal CSV schema**: Requires `case:concept:name` (case ID), `concept:name` (activity), `time:timestamp` (ISO 8601 datetime)
- **Flexible import**: PM4Py's `format_dataframe()` accepts arbitrary column names and remaps them
- **Export support**: PM4Py can convert DataFrames to XES, CSV, or keep as pandas objects
- **Best practices**: Use pandas for data manipulation, convert timestamps to datetime objects, maintain chronological ordering

**Citation**:
> PM4Py Documentation. (2024). *Handling Event Data - PM4Py*. Retrieved from https://github.com/process-intelligence-solutions/pm4py

**Impact on Design**:
- Use pandas DataFrame as internal representation for compatibility
- Export CSV with standard column names: `case_id`, `activity`, `timestamp`, `resource`
- Ensure timestamps are ISO 8601 strings with timezone
- Maintain chronological sort for efficient PM4Py import

### 2.3 Synthetic Event Log Generation Techniques

**Key Findings from Recent Research (2023-2024)**:

1. **SAMPLE (2023)**: A semantic approach for multi-perspective event log generation that considers data perspective semantics. Variables are described by a meta-model including values, dependencies, and distributions, leading to realistic synthetic data.

2. **Ground Truth Approach (2024)**: Emphasizes using synthetically generated data with ground truth for evaluation. Introduces tools like Trident (GUI) and code implementations supporting advanced deviation patterns, stochastics, and time duration handling.

3. **IoT-Enriched Logs**: Research on generating sensor event logs in a non-deterministic way, allowing controlled noise addition for realistic IoT process mining.

4. **Key Challenge**: Accessibility to real-world data is severely limited. Existing approaches often generate unrealistic values because they don't consider semantic constraints beyond process model conditions.

**Citations**:
> Kallus, C., et al. (2023). "SAMPLE: A Semantic Approach for Multi-perspective Event Log Generation." *Proceedings of BPM 2023*. Springer. https://link.springer.com/chapter/10.1007/978-3-031-27815-0_24
>
> Weinzierl, S., et al. (2024). "A ground truth approach for assessing process mining techniques." *Process Science*. https://link.springer.com/article/10.1007/s44311-025-00006-8
>
> Kampik, T., et al. (2022). "Generating Synthetic Sensor Event Logs for Process Mining." *Springer*. https://link.springer.com/chapter/10.1007/978-3-031-07481-3_15

**Impact on Design**:
- Implement semantic constraints (e.g., resource performance profiles, workload fatigue) for realism
- Use distributions (uniform, normal) for transition times rather than fixed values
- Support controlled anomaly injection (delays, overload, spikes)
- Provide ground truth metadata (seed, variant assignments) for validation
- Include configurable noise/variance parameters

---

## 3. Minimal Log Schema Design

### 3.1 Core Event Schema

Based on XES standard, PM4Py conventions, and the process definition, the event schema uses **dual naming conventions**:

#### Internal Schema (Generator)
```python
{
    "case_id": str,           # Unique case identifier (e.g., "PERMIT_2024_000001")
    "activity": str,          # Activity name (e.g., "intake_validation")
    "timestamp": str,         # ISO 8601 with timezone (e.g., "2024-09-15T08:30:00+00:00")
    "resource": str | None,   # Resource ID or null for automatic activities
    "lifecycle": str,         # "complete" (default) or "start"
}
```

#### PM4Py/XES-Compatible Schema (Export)
```python
{
    "case:concept:name": str,        # Case identifier (XES standard)
    "concept:name": str,             # Activity name (XES standard)
    "time:timestamp": datetime,      # Timestamp (XES standard, pandas datetime)
    "org:resource": str | None,      # Resource/performer (XES organizational extension)
    "lifecycle:transition": str,     # Lifecycle state (XES lifecycle extension)
    # Custom attributes (examples):
    "cost:amount": float,            # Event cost (custom namespace: cost)
    "location:office": str,          # Office location (custom namespace: location)
    "case:priority": str,            # Case-level priority (case attribute)
}
```

#### Custom Attributes Support

**XES and PM4Py fully support custom attributes** at both event-level and case-level:

**Event-Level Attributes** (different value per event):
- Use namespace prefixes: `namespace:attribute_name`
- Examples: `org:resource`, `cost:amount`, `location:office`, `perf:score`
- Any DataFrame column becomes an event attribute in XES

**Case-Level Attributes** (same value for entire trace):
- Use `case:` prefix: `case:attribute_name`
- Examples: `case:priority`, `case:region`, `case:clientID`
- Applied to all events in a case

**Namespace Conventions**:
- `org:` — Organizational (e.g., `org:resource`, `org:role`, `org:group`)
- `cost:` — Cost-related (e.g., `cost:amount`, `cost:currency`)
- `location:` — Location (e.g., `location:office`, `location:city`)
- `perf:` — Performance (e.g., `perf:score`, `perf:rating`)
- `case:` — Case-level (e.g., `case:priority`, `case:type`)
- Custom namespaces allowed

#### Column Name Mapping Table

| Internal (Generator) | PM4Py/XES Export | Required | Description |
|---------------------|------------------|----------|-------------|
| `case_id` | `case:concept:name` | ✅ Yes | Unique case identifier |
| `activity` | `concept:name` | ✅ Yes | Activity/task name |
| `timestamp` | `time:timestamp` | ✅ Yes | Event occurrence time |
| `resource` | `org:resource` | ⚠️ Optional | Person/system performing activity |
| `lifecycle` | `lifecycle:transition` | ⚠️ Optional | Event lifecycle state (complete/start) |
| `{custom_attr}` | `{namespace}:{attr}` | ⚠️ Optional | Any custom attribute (user-defined) |

**Rationale**:
- **Internal schema**: Simple, readable names for generator logic
- **Export schema**: XES-compliant names with namespaces for direct PM4Py/process mining tool compatibility
- **Automatic mapping**: Generator exports in PM4Py format by default
- **Full extensibility**: Unlimited custom attributes following XES extension conventions (event & case level)

### 3.2 Export Formats

The generator exports data in **four formats**, all using PM4Py/XES-compatible column names:

**1. CSV (PM4Py-ready)**
- Columns: Required (`case:concept:name`, `concept:name`, `time:timestamp`) + Optional (`org:resource`, `lifecycle:transition`) + Custom attributes (e.g., `cost:amount`, `location:office`, `case:priority`)
- Format: Standard CSV with header row, comma-separated
- Timestamp: ISO 8601 strings (e.g., "2024-09-15T08:30:00+00:00")
- Pros: Universal compatibility, direct PM4Py import without reformatting, supports unlimited custom columns
- Cons: Flat structure (one value per cell)

**2. Parquet (Efficient Storage)**
- Schema: Columnar with typed fields (datetime for timestamps, string for others)
- Column names: Same as CSV (PM4Py-compatible)
- Pros: Fast read/write, small file size, preserves types, supports nested attributes
- Cons: Requires pyarrow, not human-readable

**3. JSON (NDJSON - Newline-Delimited)**
- Format: One JSON event object per line
- Fields: XES-compatible names (case:concept:name, concept:name, etc.)
- Pros: Preserves full nested structure, streaming-friendly, human-readable
- Cons: Larger file size than Parquet

**4. XES (IEEE Standard XML)**
- Format: XML following IEEE 1849-2023 XES standard
- Export: Via `pm4py.write_xes(dataframe, output_path)`
- Extensions: Concept, Time, Organizational, Lifecycle
- Pros: Native format for ProM, Disco, Celonis; fully standardized
- Cons: Largest file size, verbose XML

**Export Note**: All formats contain identical data, just different serialization. Users can import any format into PM4Py without column renaming.

### 3.3 Metadata Schema

Each export should include metadata:

```json
{
    "process_name": "Restaurant Permit Application",
    "generated_at": "2024-10-07T12:00:00+00:00",
    "total_cases": 3875,
    "total_events": 24500,
    "seed": 42,
    "config_file": "process_config.yaml",
    "generator_version": "0.1.0"
}
```

Store as separate `metadata.json` or embed in Parquet/XES.

---

## 4. Configuration File Design Principles

Based on literature and process definition analysis:

### 4.1 Required Configuration Sections (Human-Centric Structure)

The configuration file follows a **chronological, activity-centric structure** where each activity is self-contained with all its information in one place.

#### 1. **Process Metadata** — Global settings

```yaml
process_name: "Restaurant Permit Application"
description: "Permit application workflow from submission to approval/rejection"

# Generation settings
num_cases: 1000        # How many cases to generate
seed: 42               # Random seed for reproducibility

# Time settings
start_date: "2024-01-01"  # First case starts here
timezone: "America/New_York"
time_granularity: "seconds"  # Timestamp precision

# Working hours (applies to all activities unless overridden)
working_hours:
  days: [Monday, Tuesday, Wednesday, Thursday, Friday]
  start: "09:00"
  end: "17:00"
  holidays: ["2024-01-01", "2024-07-04", "2024-12-25"]
```

#### 2. **Activities** — Chronological process steps (MAIN SECTION)

Each activity is **self-contained** with all its properties:

```yaml
activities:
  - step: 1                    # Sequential number (for human readability)
    id: submitted              # Unique identifier
    name: "Application Submitted"
    description: "Applicant submits permit application online"
    type: automatic            # automatic | human | final

    # How long until next step? (embedded here, not in separate "transitions" section)
    duration:
      min: 24      # Hours (or use typical/spread for normal distribution)
      max: 48

    # What happens next? (embedded here, not in separate "variants" section)
    next_steps:
      - activity: intake_validation
        probability: 1.0    # 100% go here

  - step: 2
    id: intake_validation
    name: "Intake Validation"
    description: "Clerk validates application completeness"
    type: human
    resource_pool: clerks      # Which resource pool performs this

    duration:
      min: 24
      max: 72

    next_steps:
      - activity: rejected
        probability: 0.03      # 3% fail here (early rejection)
      - activity: assigned_to_reviewer
        probability: 0.97      # 97% proceed to review
```

**Key points:**
- `duration` is **inside each activity** — no separate "transitions" section
- `next_steps` with probabilities are **inside each activity** — no separate "variants" section
- Variants **emerge naturally** from the probability tree (e.g., following 0.03 probability gives early rejection variant)
- `step` numbers enforce chronological ordering for human readability

#### 3. **Resources** — Who performs the work

```yaml
resource_pools:
  clerks:
    - id: clerk_001
      name: "Alice Martinez"
      speed: 0.8         # 20% faster than baseline
      consistency: 0.9   # Low variance (predictable)
      capacity: 1.0      # Standard workload

    - id: clerk_002
      name: "Bob Chen"
      speed: 1.2         # 20% slower
      consistency: 0.7   # Higher variance
      capacity: 1.3      # Handles more cases

  reviewers:
    - id: reviewer_001
      name: "David Kim"
      speed: 0.7
      consistency: 0.9
      capacity: 0.9
```

**Performance profiles:**
- `speed`: Multiplier on duration (0.8 = faster, 1.2 = slower)
- `consistency`: How predictable (1.0 = no variance, 0.6 = ±50% swing)
- `capacity`: Workload weighting (1.5 = gets 50% more cases)

#### 4. **Custom Attributes** — Additional event/case data

```yaml
event_attributes:
  - name: cost:amount
    type: float
    description: "Cost in USD for this activity"
    generation:
      distribution: normal
      mean: 50
      std: 10

  - name: location:office
    type: string
    values: ["downtown", "suburban", "remote"]
    probabilities: [0.5, 0.3, 0.2]
    description: "Office location where activity occurred"

case_attributes:
  - name: case:priority
    type: string
    values: ["low", "normal", "high"]
    probabilities: [0.2, 0.6, 0.2]
    description: "Application priority level"

  - name: case:region
    type: string
    values: ["north", "south", "east", "west"]
    probabilities: [0.25, 0.25, 0.25, 0.25]
```

**Namespace conventions:** `org:`, `cost:`, `location:`, `perf:`, `case:`

#### 5. **Anomalies** (Optional) — Realism knobs

```yaml
anomalies:
  # Random delays
  delay_probability: 0.05       # 5% of transitions get delayed
  delay_multiplier_min: 2
  delay_multiplier_max: 4       # Delayed transitions take 2-4× longer

  # Peak times (busy periods)
  peak_time_probability: 0.30   # 30% of cases hit peak times
  peak_slowdown: 1.1            # 10% slower during peaks

  # Resource fatigue
  enable_fatigue: true          # Slows down after many cases
  fatigue_max_slowdown: 0.30    # Up to 30% slower at max fatigue
```

#### 6. **Output** — Export configuration

```yaml
output:
  formats: [csv, parquet, json, xes]  # All PM4Py-compatible
  directory: "./out"
  sample_size: 50                     # Also generate small samples for testing
```

---

**Why this structure is human-centric:**

1. **Chronological flow**: Activities ordered by `step` number (1, 2, 3...)
2. **Self-contained**: Each activity has everything (duration, next_steps) in one place
3. **No technical fragmentation**: No separate "transitions" or "variants" sections to cross-reference
4. **Natural mental model**: Matches how people describe processes ("After submission, it takes 24-48 hours to reach intake validation, then 97% proceed to review...")
5. **Variants emerge naturally**: Following probability branches gives you variants automatically

### 4.1a Implementation Notes: Self-Documenting Configuration

The structure defined in Section 4.1 becomes **self-documenting** through rich inline comments in the actual YAML file.

**Documentation Strategy:**

1. **Every parameter has an inline comment** explaining what it does and typical values
2. **Examples embedded in comments** show how to tune for different scenarios
3. **Units always specified** (hours, probability, multiplier)
4. **Choices explained** (e.g., "automatic | human | final")

**Example of fully documented activity** (from Section 4.1):
```yaml
activities:
  - step: 2                        # Sequential order (for human reading)
    id: intake_validation          # Unique ID (used in next_steps references)
    name: "Intake Validation"      # Human-readable name (appears in event log)
    description: "Clerk validates application completeness and basic requirements"
    type: human                    # automatic | human | final
    resource_pool: clerks          # Which pool performs this (see resources section)

    # How long does this step take?
    duration:
      min: 24    # Minimum: 1 day (fastest possible)
      max: 72    # Maximum: 3 days (when clerk is busy)
      # Actual time varies based on:
      # - Clerk's speed multiplier (see resources)
      # - Current workload (fatigue effect)
      # - Random delays (5% probability, see anomalies)
      # - Peak times (30% probability, see anomalies)

    # What can happen next? (probabilities must sum to 1.0)
    next_steps:
      - activity: rejected              # Early rejection (incomplete application)
        probability: 0.03               # 3% of cases fail here
      - activity: assigned_to_reviewer  # Normal flow (complete application)
        probability: 0.97               # 97% proceed to review
      # To increase rejection rate: increase first probability to 0.05, decrease second to 0.95
```

**Why this works:**

- **Non-technical users** can read the comments and understand how to tune parameters
- **No external documentation needed** — everything explained in the file
- **Tuning guidance inline** — comments show how changing values affects behavior
- **Semantic naming** — "intake_validation" not "activity_002"
- **Activity-centric** — all info about an activity in one place (no cross-referencing)

This follows the **SAMPLE semantic methodology** (Section 2.3) by encoding domain knowledge directly in the configuration, making the "what" and "why" visible to humans.

### 4.2 Duration Specification: Two Simple Formats

Each transition duration is specified in **one of two formats** (not both):

#### Format 1: Min/Max (Uniform Distribution) — DEFAULT

```yaml
duration:
  min: 24    # Minimum hours (fastest possible)
  max: 48    # Maximum hours (slowest typical case)
```

**How it works:** Generator uses `random.uniform(24, 48)` — every value between 24-48 hours is equally likely.

**When to use:**
- Simple bounded randomness
- Easy to understand from PROCESS_DEFINITION.md ranges
- Good default for most transitions

**Example interpretation:** "This step takes anywhere from 1 to 2 days, all durations equally likely"

---

#### Format 2: Typical/Spread (Normal Distribution) — OPTIONAL

```yaml
duration:
  typical: 36    # Expected/mean duration (hours)
  spread: 8      # Standard deviation (hours)
```

**How it works:** Generator uses `random.gauss(36, 8)` — creates bell curve around typical value.

**Statistical meaning:**
- ~68% of cases fall within `typical ± spread` (28-44 hours)
- ~95% of cases fall within `typical ± 2×spread` (20-52 hours)
- ~99.7% of cases fall within `typical ± 3×spread` (12-60 hours)

**When to use:**
- More realistic clustering around expected time
- When most cases should be close to typical value
- When you want natural variation with fewer extreme outliers

**Example interpretation:** "This step typically takes 36 hours, usually varies by ±8 hours, rarely exceeds 20-52 hour range"

---

#### Rules & Conversion

**Important Rule:** Specify **EITHER** min/max **OR** typical/spread per transition, not both.
- If both are present → typical/spread takes precedence (generator logs a warning)

**Conversion formulas** (if you need to switch between formats):
- `typical = (min + max) / 2` — Example: (24+48)/2 = 36
- `spread ≈ (max - min) / 6` — Example: (48-24)/6 = 4 (ensures ~99.7% within bounds)
- `min ≈ typical - 3×spread` — Example: 36 - 3×4 = 24
- `max ≈ typical + 3×spread` — Example: 36 + 3×4 = 48

---

#### Tuning Guide for Variability

**Want more outliers / extreme cases?**
- Format 1: Increase `max` significantly (e.g., min:24, max:96 instead of max:48)
- Format 2: Increase `spread` (e.g., spread:16 instead of spread:8)
- Also: Reduce resource `consistency` to 0.6-0.7

**Want tighter clustering / more predictable times?**
- Format 1: Reduce range (e.g., min:30, max:42 instead of min:24, max:48)
- Format 2: Reduce `spread` (e.g., spread:4 instead of spread:8)
- Also: Increase resource `consistency` to 0.9-1.0

**Want more random delays / bottlenecks?**
- Increase `delay_probability` from 0.05 to 0.10 or higher (in anomalies section)
- Increase `delay_multiplier_max` from 4 to 6+

**Want faster process overall?**
- Reduce both min and max proportionally (e.g., min:12, max:24 instead of min:24, max:48)
- Or reduce typical value (e.g., typical:18 instead of typical:36)

#### Resource Variability

```yaml
resources:
  - id: clerk_001
    speed: 0.8        # Multiplier on base duration (0.8 = 20% faster than baseline)
    consistency: 0.9  # How predictable (1.0 = no variance, 0.6 = ±50% swing per case)
    capacity: 1.0     # Workload weighting (1.5 = handles 50% more cases than baseline)
```

**Interpretation**:
- **Speed**: `0.8` means tasks take 80% of base time (faster worker)
- **Consistency**: `0.9` means ±10% random variation per task (predictable)
- **Capacity**: `1.2` means gets assigned 20% more cases than average
- **Fatigue**: `slowdown = 1 + (cases_handled / 50) × 0.3` (auto-applied, up to 30% slower at 50 cases)

#### Stochastic Events (Anomalies)

```yaml
anomalies:
  delay_probability: 0.05      # 5% of transitions get unexpected delays
  delay_multiplier_min: 2      # Delayed transitions take 2-4× longer
  delay_multiplier_max: 4

  peak_time_probability: 0.30  # 30% of cases hit "busy periods"
  peak_slowdown: 1.1           # 10% slower during busy periods
```

**Tuning**:
- Increase `delay_probability` to 0.10 → 10% of transitions become bottlenecks
- Increase `delay_multiplier_max` to 6 → more extreme outliers (up to 6× normal time)
- Increase `peak_slowdown` to 1.3 → busy periods are 30% slower

#### Process Structure

```yaml
variants:
  - name: request_more_info
    max_rework_loops: 2   # Allow up to 2 iterations of info request → re-review cycle
```

**Interpretation**: Cases in this variant can loop through "request info → provide info → review" up to 2 times before proceeding.

---

## 5. Technology Stack Recommendations

Based on research and requirements:

| Component | Technology | Justification |
|-----------|-----------|---------------|
| Language | Python 3.10+ | Modern type hints, broad ecosystem, PM4Py compatibility |
| Data manipulation | pandas | PM4Py standard, rich API for event log operations |
| Parquet support | pyarrow | Fast, well-maintained, pandas integration |
| YAML parsing | pyyaml | Mature, widely used |
| JSON validation | jsonschema | Validate config against schema, standard-compliant |
| Testing | pytest | Industry standard, rich plugin ecosystem |
| RNG | random.Random | Seeded for reproducibility, built-in Python |
| CLI | argparse | Built-in, sufficient for requirements |
| Time handling | datetime + pytz | Timezone-aware timestamps, XES-compatible |

---

## 6. Key Takeaways for Implementation

### 6.1 From Literature

1. **XES compatibility is essential** but CSV/Parquet are more practical for large-scale analysis
2. **PM4Py conventions** (case_id, activity, timestamp) ensure tool interoperability
3. **Semantic realism** (resource profiles, workload effects) is critical for quality synthetic data
4. **Ground truth metadata** (seed, variant labels) enables validation and benchmarking

### 6.2 From Process Definition

1. **Generic attribute model** avoids hardcoding domain-specific fields
2. **Variant-based generation** with probabilistic branching ensures realistic process mix
3. **Multi-layer variance** (resource speed, fatigue, random delays, peak times) creates realistic timing patterns
4. **Workload-aware resource assignment** produces correlated patterns found in real logs

### 6.3 Schema Simplifications

- Use **lifecycle="complete" only** (start/complete pairs add complexity without value for this use case)
- Flatten **attributes to columns** for CSV export (resource, priority, location as separate columns)
- Store **event_id as optional** (generate only if explicitly requested)
- Default **time_granularity to seconds** (ISO 8601 handles fractional seconds)

---

## 7. Design Decisions

### 7.1 Resolved Decisions

1. **Column naming convention**: Use PM4Py/XES-compatible names in exports
   - **Decision**: Export uses `case:concept:name`, `concept:name`, `time:timestamp`, `org:resource`, `lifecycle:transition`
   - **Rationale**: Direct compatibility with PM4Py, XES, ProM, Disco without user intervention

2. **Probability distribution format**: Support both min/max and typical/spread
   - **Decision**: Default to min/max (uniform), optionally support typical/spread (normal)
   - **Rationale**: Min/max matches PROCESS_DEFINITION.md and is easier for non-technical users

3. **Human-centric configuration**: Activity-centric chronological structure
   - **Decision**: Activities defined in execution order with inline comments
   - **Rationale**: Matches mental model of process designers, self-documenting

4. **Semantic constraints**: Encode domain knowledge in configuration
   - **Decision**: Include resource skill/performance profiles, workload effects, attribute dependencies
   - **Rationale**: Follows SAMPLE methodology for realistic synthetic data

### 7.2 Open Design Questions

1. **Calendar complexity**: Should we support multiple calendars (per resource pool) or single global calendar?
   - **Current**: Start with single global calendar (business hours + holidays), extend later if needed

2. **Rework loop limits**: Should max iterations be per-variant or global?
   - **Current**: Per-variant (specified in variant definition) with global fallback

3. **Anomaly application**: Should anomalies apply to specific activities, resources, or time windows?
   - **Current**: Support all three modes via configuration (activity-targeted, resource-targeted, time-window-targeted)

4. **Output file naming**: Single file vs multiple files (per variant, per time window)?
   - **Current**: Single file for all events (default), option to partition by case_id ranges for very large datasets

---

## 8. Next Steps (Phase 1)

1. Design `process_config.yaml` schema with human-centric chronological structure
2. Create minimal example configuration for restaurant permit process with rich inline comments
3. Implement YAML parser with schema validation
4. Document configuration file format in README

**Success Criteria for Phase 1**:
- [ ] Valid `process_config.yaml` loads without errors
- [ ] Schema validator catches invalid configurations
- [ ] Minimal example covers all 5 variants from PROCESS_DEFINITION.md
- [ ] Configuration is human-readable and self-documenting (non-technical user can modify it)
- [ ] Inline comments explain all parameters with examples and tuning guidance
- [ ] Structure matches chronological flow of process
- [ ] PM4Py column naming conventions documented and validated

**Validation Tests for Phase 1**:
- [ ] YAML parses successfully
- [ ] All required fields present
- [ ] Probabilities sum to 1.0 for next_steps and variants
- [ ] Duration formats validated (min/max OR typical/spread, not both)
- [ ] Resource references valid (all resource_pools exist)
- [ ] Activity references valid (all next_steps activities exist)
