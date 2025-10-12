# Event Log Output Format Specification

**Document Version**: 1.0
**Last Updated**: 2025-10-12
**Purpose**: Interface specification for process flow diagram renderers and process mining tools

---

## Overview

This document describes the structure and content of event logs generated for process mining and visualization. Event logs represent **business process executions** as sequences of timestamped activities (events) grouped by cases.

**Key Concepts**:
- **Case**: A single process instance (e.g., one permit application, one order, one patient visit)
- **Event**: A single activity execution within a case (e.g., "Application Submitted", "Review in Progress")
- **Trace**: The complete sequence of events for one case, ordered chronologically
- **Resource**: The person, system, or role that performed an activity
- **Lifecycle**: The state of an event (typically "complete", sometimes "start", "suspend", etc.)

---

## Output Formats

Event logs are available in **4 standard formats**, all containing identical data:

| Format | File Extension | Description | Use Case |
|--------|---------------|-------------|----------|
| **CSV** | `.csv` | Comma-separated values | Spreadsheets, simple tools, human inspection |
| **Parquet** | `.parquet` | Columnar binary format | Large datasets, analytics, data warehouses |
| **JSON** | `.json` | NDJSON (newline-delimited) | Web APIs, streaming, JavaScript applications |
| **XES** | `.xes` | XML-based IEEE standard | PM4Py, ProM, Disco, process mining research |

**Compatibility**: All formats follow the **IEEE 1849-2023 XES standard** naming conventions and are directly importable into **PM4Py** without preprocessing.

---

## Data Structure

### Core Schema (Required Fields)

Every event log contains these **5 mandatory columns/fields**:

| Field Name | XES/PM4Py Name | Type | Description | Example |
|------------|----------------|------|-------------|---------|
| **Case ID** | `case:concept:name` | String | Unique identifier for the case | `"case_0001"`, `"order_12345"` |
| **Activity** | `concept:name` | String | Name of the activity performed | `"Application Submitted"`, `"Payment Processed"` |
| **Timestamp** | `time:timestamp` | ISO 8601 DateTime | When the event occurred | `"2024-01-02 09:00:00.000000"` |
| **Resource** | `org:resource` | String (optional) | Who/what performed the activity | `"Alice Martinez"`, `"clerk_002"`, `""` (empty for automatic) |
| **Lifecycle** | `lifecycle:transition` | String | Event state (usually "complete") | `"complete"`, `"start"`, `"suspend"` |

**Notes**:
- Resource is **empty** for automatic/system activities (no human involvement)
- Timestamps include microsecond precision but may use lower granularity (seconds, minutes, hours)
- All timestamps are in a single timezone (specified in configuration)

---

### Custom Attributes (Optional Fields)

Event logs may include **additional domain-specific attributes** with XES namespace prefixes:

#### Common Namespaces:
- `case:*` - Case-level attributes (same value for all events in a case)
- `cost:*` - Cost-related data (e.g., `cost:amount`)
- `org:*` - Organizational data (e.g., `org:department`, `org:role`)
- `perf:*` - Performance metrics (e.g., `perf:duration`)
- `location:*` - Geographic data (e.g., `location:city`)

#### Examples:

**Case-Level Attributes** (constant per case):
```csv
case:priority         # "low", "normal", "high"
case:applicant_type   # "new_business", "existing_business", "renewal"
case:region          # "north", "south", "east", "west"
case:channel         # "online", "phone", "in_person"
```

**Event-Level Attributes** (vary per event):
```csv
cost:amount          # 45.32, 67.89 (processing cost in currency units)
org:department       # "sales", "finance", "operations"
org:role            # "clerk", "manager", "inspector"
```

**Data Types**:
- String: `"value"`
- Float: `45.32`
- Integer: `100`
- Boolean: `true` / `false`
- DateTime: ISO 8601 format

---

## CSV Format Details (Primary Format)

### Structure

**Header Row**: Column names (XES standard names)
**Data Rows**: One row per event, sorted chronologically within each case

### Example

```csv
case:concept:name,concept:name,time:timestamp,org:resource,lifecycle:transition,case:priority,case:applicant_type,cost:amount
case_0001,submitted,2024-01-02 09:00:00.000000,,complete,normal,new_business,0.0
case_0001,intake_validation,2024-01-03 15:36:02.533107,clerk_002,complete,normal,new_business,35.93
case_0001,review_in_progress,2024-01-08 09:22:25.844521,reviewer_004,complete,normal,new_business,50.50
case_0001,health_inspection,2024-01-11 11:32:40.285949,inspector_003,complete,normal,new_business,53.80
case_0001,approved,2024-01-18 09:00:00.000000,,complete,normal,new_business,0.0
case_0002,submitted,2024-01-02 09:00:00.000000,,complete,high,renewal,0.0
case_0002,intake_validation,2024-01-03 13:46:19.573019,clerk_001,complete,high,renewal,21.64
case_0002,rejected,2024-01-05 09:00:00.000000,,complete,high,renewal,0.0
```

### Characteristics

- **Character Encoding**: UTF-8
- **Line Endings**: Unix (`\n`) or Windows (`\r\n`)
- **Delimiter**: Comma (`,`)
- **Quoting**: Fields with commas/quotes are quoted with double quotes (`"`)
- **Empty Fields**: Represented as empty string (e.g., `,,` for missing resource)
- **Sorting**: Events are sorted by case ID (ascending), then timestamp (ascending)

---

## Process Structure Information

### Cases and Traces

**Case Grouping**: Events with the same `case:concept:name` form a single trace (process instance)

**Trace Example** (case_0001):
```
submitted → intake_validation → review_in_progress → health_inspection → approved
```

**Trace Characteristics**:
- **Start Activity**: First event in the trace (e.g., `"submitted"`)
- **End Activity**: Last event in the trace (e.g., `"approved"`, `"rejected"`, `"withdrawn"`)
- **Cycle Time**: Duration from start to end timestamp
- **Event Count**: Number of activities in the trace (typically 3-15 events)

### Process Variants

**Definition**: Unique sequences of activities across cases

**Common Patterns**:
1. **Happy Path**: Direct flow with no rework (e.g., `submitted → review → inspection → approved`)
2. **Rework Loops**: Activities repeated (e.g., `review → request_info → review → request_info → review`)
3. **Early Termination**: Process ends before typical completion (e.g., `submitted → rejected`)
4. **Alternative Paths**: Different branches (e.g., `approved` vs `rejected` vs `withdrawn`)

**Variant Distribution**: Typically 3-10 major variants representing 80%+ of cases

---

## Data Characteristics

### Volume

- **Cases**: Typically 100 - 10,000+ per file
- **Events**: Typically 500 - 100,000+ per file
- **Events per Case**: Average 5-10 events, range 2-30 events

### Temporal Properties

**Timestamps**:
- Strictly increasing within each case (chronological order)
- May overlap across cases (parallel execution)
- Include business hours effects (e.g., no events on weekends/holidays)
- Duration between events: seconds to weeks

**Working Calendar Effects**:
- Events may cluster at business hours (e.g., 9 AM - 5 PM, Monday-Friday)
- Gaps during nights, weekends, holidays
- Timezone-aware (typically single timezone per log)

### Resources

**Resource Assignment**:
- Human activities have assigned resources (e.g., `"clerk_002"`, `"Alice Martinez"`)
- Automatic/system activities have empty resources (`""`)
- Resources may be IDs (`"clerk_002"`) or names (`"Alice Martinez"`)
- Same resource may appear across multiple cases (workload distribution)

**Resource Behavior**:
- Performance varies (some faster/slower)
- Capacity varies (some handle more cases)
- Fatigue effects (slower over time)

### Anomalies and Realism

**Realistic Variability**:
- **Most events**: Predictable durations (e.g., 1-3 days for review)
- **Rare delays**: ~5% of events take 2-4x longer (bottlenecks, exceptions)
- **Peak times**: ~30% of cases experience 10-20% slowdown (busy periods)
- **Outliers**: <1% of events have extreme durations (perfect storm scenarios)

**Cost Distribution** (if present):
- Follows normal distribution with occasional outliers
- Zero cost for automatic activities
- Positive cost for human activities

---

## PM4Py Integration

### Direct Import

All formats can be imported directly into PM4Py:

```python
import pm4py

# CSV format
log = pm4py.read_csv('events.csv')

# XES format
log = pm4py.read_xes('events.xes')

# Parquet format
import pandas as pd
df = pd.read_parquet('events.parquet')
log = pm4py.convert_to_event_log(df)
```

### Supported Analyses

**Process Discovery**:
- Directly Follows Graphs (DFG)
- Petri nets (Alpha Miner, Inductive Miner)
- BPMN diagrams
- Process trees

**Conformance Checking**:
- Token replay
- Alignment-based conformance

**Performance Analysis**:
- Cycle time analysis
- Bottleneck detection
- Resource utilization

**Filtering**:
- Time range filters
- Activity filters
- Variant filters
- Attribute filters

---

## Process Flow Diagram Rendering - Key Data Points

### Node (Activity) Information

**From `concept:name` field**:
- Activity name (e.g., `"Application Submitted"`, `"Review in Progress"`)
- Frequency: Count of events with this activity name
- Resources: Set of unique resources performing this activity

**Suggested Visual Encoding**:
- Node size: Frequency (more frequent = larger)
- Node color: Activity type (start=green, end=red, intermediate=blue)
- Node label: Activity name + frequency count

### Edge (Transition) Information

**Derived from consecutive events within each case**:
- From Activity → To Activity
- Frequency: Count of case transitions between activities
- Average Duration: Mean time between activities
- Duration Range: Min/max time between activities

**Example**:
```
From: "Review in Progress"
To: "Health Inspection"
Frequency: 847 cases
Avg Duration: 2.3 days
Min/Max: 1.2 / 8.5 days
```

**Suggested Visual Encoding**:
- Edge thickness: Frequency (more frequent = thicker)
- Edge color: Average duration (fast=green, slow=red)
- Edge label: Frequency or avg duration

### Start and End Activities

**Start Activities**: Activities that begin cases (first event per case)
- Identify: `MIN(time:timestamp) GROUP BY case:concept:name`
- Typically 1 start activity (e.g., `"submitted"`)

**End Activities**: Activities that terminate cases (last event per case)
- Identify: `MAX(time:timestamp) GROUP BY case:concept:name`
- Typically 2-5 end activities (e.g., `"approved"`, `"rejected"`, `"withdrawn"`)

### Process Variants (Paths)

**Extraction**:
1. Group events by `case:concept:name`
2. Sort by `time:timestamp` (ascending)
3. Extract activity sequence: `[activity_1, activity_2, ..., activity_n]`
4. Group cases by identical sequences

**Example Variants**:
```
Variant 1 (58%): submitted → intake → review → inspection → approved
Variant 2 (24%): submitted → intake → review → request_info → review → inspection → approved
Variant 3 (10%): submitted → intake → review → inspection → rejected
Variant 4 (5%): submitted → intake → review → request_info → withdrawn
Variant 5 (3%): submitted → intake → rejected
```

**Use for Visualization**:
- Highlight most common path (happy path)
- Show variant splits/merges
- Animate case flow along paths

### Loops and Rework

**Detection**: Same activity appears multiple times in a trace

**Example**:
```
case_0005: submitted → intake → review → request_info → applicant_provided → review → request_info → applicant_provided → review → inspection → approved
                                          ↑                                           ↑
                                          └───────────────── LOOP 1 ─────────────────┘
```

**Metrics**:
- Loop count: Number of times activity repeats
- Rework percentage: Cases with loops / total cases
- Loop duration: Time spent in rework cycles

---

## Example Use Cases

### 1. Process Flow Diagram
- **Nodes**: Unique activities from `concept:name`
- **Edges**: Transitions between consecutive events
- **Metrics**: Frequency, avg duration, bottlenecks

### 2. Timeline Visualization
- **X-axis**: `time:timestamp`
- **Y-axis**: Cases (`case:concept:name`)
- **Events**: Dots/bars colored by activity

### 3. Resource Workload Dashboard
- **Resources**: Unique values from `org:resource`
- **Metrics**: Cases per resource, avg handling time
- **Filters**: Time range, activity type

### 4. Variant Analysis
- **Paths**: Extract trace sequences per case
- **Metrics**: Variant frequency, cycle time by variant
- **Comparison**: Happy path vs rework variants

### 5. Bottleneck Detection
- **Duration**: Time between consecutive events
- **Outliers**: Events with duration > 95th percentile
- **Visualization**: Heatmap of slow transitions

---

## File Naming Convention

**Standard Pattern**: `{prefix}_{format}.{extension}`

**Examples**:
```
events.csv           # Main CSV output
events.parquet       # Main Parquet output
events.json          # Main JSON output
events.xes           # Main XES output
events_sample.csv    # Small sample (first 50 events) for preview
metadata.json        # Generation metadata (optional companion file)
```

**Metadata File** (optional companion):
```json
{
  "generator_version": "1.0.0",
  "process_name": "Restaurant Permit Application",
  "num_cases": 1000,
  "num_events": 7234,
  "seed": 42,
  "generated_at": "2024-10-12T14:32:18Z",
  "variant_distribution": {
    "variant_1_direct_approval": {"percentage": 0.58, "count": 580},
    "variant_2_request_info": {"percentage": 0.24, "count": 240},
    "variant_3_rejected": {"percentage": 0.10, "count": 100}
  },
  "summary_statistics": {
    "mean_cycle_time_days": 12.4,
    "median_cycle_time_days": 9.8,
    "min_cycle_time_days": 3.2,
    "max_cycle_time_days": 45.7
  }
}
```

---

## Quality Guarantees

**Data Integrity**:
- ✅ All cases have at least one event
- ✅ Timestamps are chronologically ordered within cases
- ✅ All required fields are present (no null values in core schema)
- ✅ Case IDs are unique per case, consistent across events
- ✅ Activity names are non-empty strings

**Semantic Validity**:
- ✅ Each case has exactly one start activity
- ✅ Each case has exactly one end activity
- ✅ All transitions between activities are logically valid (no impossible flows)
- ✅ Resource assignments are consistent (resources don't switch mid-activity)

**Reproducibility**:
- ✅ Same configuration = identical output (seeded generation)
- ✅ Metadata tracks generation parameters

---

## Technical Notes

### Parsing Considerations

**CSV Parsing**:
- Use UTF-8 encoding
- Handle quoted fields (RFC 4180 compliant)
- Empty resource fields are valid (automatic activities)
- Timestamp parsing: ISO 8601 format with microseconds

**Memory Efficiency**:
- CSV: Text-based, ~50-100 MB per 1M events
- Parquet: Binary, ~10-20 MB per 1M events (5-10x compression)
- JSON: Text-based, ~80-120 MB per 1M events
- XES: XML-based, ~100-150 MB per 1M events

**Streaming**:
- CSV/JSON: Can be read line-by-line (streaming)
- Parquet: Columnar, supports chunk reading
- XES: XML requires full parsing (not streaming-friendly)


---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-10-12 | Initial specification |

---

## Contact & Support

This specification is designed to be **tool-agnostic** and follows **IEEE 1849-2023 XES standard** conventions for maximum compatibility with process mining tools.

For questions or clarifications, refer to:
- **XES Standard**: IEEE 1849-2023
- **PM4Py Documentation**: https://pm4py.fit.fraunhofer.de/
- **Process Mining Book**: "Process Mining: Data Science in Action" by Wil van der Aalst
