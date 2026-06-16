# Process Definition: Generic Event Log Generation

## Overview

This document defines a comprehensive, **code-agnostic** business process model for generating event log data. The process model represents a permit application workflow where cases flow through various states from submission to final outcomes.

This definition serves as a **generic specification** that can be implemented by any event log generator to produce realistic process mining datasets. The event log data model is designed to be **attribute-agnostic**, allowing any number of contextual attributes per event.

---

## 1. Process States

### 1.1 Complete State List

The process contains **10 distinct states**:

1. **submitted** - Initial state when application is received
2. **intake_validation** - Clerk validates completeness and basic requirements
3. **assigned_to_reviewer** - System automatically assigns to available reviewer
4. **review_in_progress** - Reviewer evaluates application details
5. **request_additional_info** - Reviewer requests more information from applicant
6. **applicant_provided_info** - Applicant submits requested information
7. **health_inspection** - Health inspector conducts site inspection
8. **approved** - Application approved (final state)
9. **rejected** - Application rejected (final state)
10. **withdrawn** - Application withdrawn by applicant (final state)

### 1.2 State Taxonomy

States are classified into three categories:

#### Final States (Terminal)
- `approved`
- `rejected`
- `withdrawn`

**Rule**: Every case MUST end in exactly one of these states.

#### Human-Performed States
States requiring human activity/decision:
- `intake_validation` - Performed by clerks
- `review_in_progress` - Performed by reviewers
- `health_inspection` - Performed by health inspectors

**Rule**: These states must have a `performer` (resource) assigned.

#### Automatic States
States that occur automatically without human intervention:
- `submitted`
- `assigned_to_reviewer`
- `request_additional_info`
- `applicant_provided_info`

**Rule**: These states have `performer = null`.

---

## 2. Process Variants

### 2.1 Variant Definition Structure

Each variant represents a distinct path through the process with:
- **Sequence**: Ordered list of states
- **Probability**: Likelihood of occurrence (must sum to 1.0 across all variants)
- **Name**: Human-readable identifier

### 2.2 Defined Variants

#### Variant 1: Direct Approval (Happy Path)
- **Name**: Direct Approval
- **Probability**: 58%
- **Sequence**:
  ```
  submitted → intake_validation → assigned_to_reviewer →
  review_in_progress → health_inspection → approved
  ```
- **Description**: Optimal path with no complications

#### Variant 2: Request More Info
- **Name**: Request More Info
- **Probability**: 24%
- **Sequence**:
  ```
  submitted → intake_validation → assigned_to_reviewer →
  review_in_progress → request_additional_info →
  applicant_provided_info → review_in_progress →
  health_inspection → approved
  ```
- **Description**: Single loop for additional information
- **Note**: Contains loop (`review_in_progress` appears twice)

#### Variant 3: Rejected at Final
- **Name**: Rejected at Final
- **Probability**: 10%
- **Sequence**:
  ```
  submitted → intake_validation → assigned_to_reviewer →
  review_in_progress → health_inspection → rejected
  ```
- **Description**: Full process ending in rejection

#### Variant 4: Withdrawn
- **Name**: Withdrawn
- **Probability**: 5%
- **Sequence**:
  ```
  submitted → intake_validation → assigned_to_reviewer →
  review_in_progress → request_additional_info → withdrawn
  ```
- **Description**: Applicant withdraws after information request

#### Variant 5: Early Rejection
- **Name**: Early Rejection
- **Probability**: 3%
- **Sequence**:
  ```
  submitted → intake_validation → rejected
  ```
- **Description**: Application fails basic requirements during initial validation

### 2.3 Variant Generation Rules

1. **Probability Normalization**: If probabilities don't sum to 1.0, normalize by dividing each by the total
2. **Variant Selection**: Use weighted random selection based on normalized probabilities
3. **Sequence Integrity**: Each generated case must follow exactly one variant sequence
4. **Variant Overrides**: Allow external configuration to override default probabilities

---

## 3. Transition Time Specifications

### 3.1 Time Range Format

Each transition between states has expected processing time ranges (in hours):

```
transition_key: { min: <hours>, max: <hours> }
```

**Key Format**: `"source_state->target_state"` (note the `->` arrow)

### 3.2 Complete Transition Time Ranges

| Transition | Min (hours) | Max (hours) | Business Days | Description |
|------------|-------------|-------------|---------------|-------------|
| `submitted->intake_validation` | 24 | 48 | 1-2 days | Batch processing delay |
| `intake_validation->rejected` | 24 | 72 | 1-3 days | Early rejection decision |
| `intake_validation->assigned_to_reviewer` | 0.1 | 0.5 | 6-30 min | Automatic assignment |
| `assigned_to_reviewer->review_in_progress` | 48 | 120 | 2-5 days | Reviewer workload dependent |
| `review_in_progress->health_inspection` | 24 | 168 | 1-7 days | Scheduling coordination |
| `review_in_progress->request_additional_info` | 24 | 168 | 1-7 days | Complex case analysis |
| `request_additional_info->applicant_provided_info` | 48 | 72 | 2-3 days | External dependency |
| `applicant_provided_info->review_in_progress` | 48 | 336 | 2-14 days | Re-review after additional info - typically delayed as re-reviews are deprioritized |
| `health_inspection->approved` | 24 | 120 | 1-5 days | Final paperwork |
| `health_inspection->rejected` | 24 | 120 | 1-5 days | Rejection documentation |
| `request_additional_info->withdrawn` | 12 | 48 | 0.5-2 days | Applicant abandons process |

### 3.3 Time Calculation Rules

**Base Duration**: Random value between `min` and `max` for the transition

**Fallback**: If transition not defined, use default range of 1-24 hours

---

## 4. Resource Configuration

### 4.1 Resource Types & Pools

Three resource types with distinct pools:

#### Clerks (Intake Processing)
- `clerk_001` - Alice Martinez
- `clerk_002` - Bob Chen
- `clerk_003` - Carol Johnson

**Assigned to**: `intake_validation` state

#### Reviewers (Main Processing)
- `reviewer_001` - David Kim
- `reviewer_002` - Emma Wilson
- `reviewer_003` - Frank Rodriguez
- `reviewer_004` - Grace O'Brien

**Assigned to**: `review_in_progress` state

#### Health Inspectors (Final Inspection)
- `inspector_001` - Henry Patel
- `inspector_002` - Iris Thompson
- `inspector_003` - Jack Anderson

**Assigned to**: `health_inspection` state

### 4.2 Resource Assignment Rules

1. **State-Resource Mapping**: Each human state has a predefined resource pool
2. **Workload-Based Selection**: Resources are selected based on capacity and current workload (see Section 5)
3. **Null Resources**: Automatic states have no resource assigned

### 4.3 Resource Naming Convention

Each resource has:
- **Resource ID**: Unique identifier (e.g., `clerk_001`, `reviewer_003`)
- **Display Name**: Human-readable name for UI display (e.g., "Alice Martinez", "Frank Rodriguez")

**Note**: Display names are optional for event log generation but recommended for downstream visualization and analysis.

---

## 5. Resource Performance Characteristics

### 5.1 Performance Profile Structure

Each resource has three performance attributes:

- **Speed**: Processing time multiplier
  - Range: 0.7 - 1.4
  - 1.0 = baseline, <1.0 = faster, >1.0 = slower
  - Applied to base transition time

- **Consistency**: Performance variability
  - Range: 0.6 - 1.0
  - 1.0 = highly consistent, lower = more variance
  - Affects random variation in processing time

- **Capacity**: Relative workload capability
  - Range: 0.8 - 1.5
  - Higher capacity = more cases assigned
  - Used for workload distribution

### 5.2 Resource Performance Profiles

#### Clerks

| Resource ID | Display Name | Speed | Consistency | Capacity | Profile Description |
|-------------|--------------|-------|-------------|----------|---------------------|
| clerk_001 | Alice Martinez | 0.8 | 0.9 | 1.0 | Fast and consistent |
| clerk_002 | Bob Chen | 1.2 | 0.7 | 1.3 | Slower but handles more cases |
| clerk_003 | Carol Johnson | 1.0 | 1.0 | 0.8 | Average performer |

#### Reviewers

| Resource ID | Display Name | Speed | Consistency | Capacity | Profile Description |
|-------------|--------------|-------|-------------|----------|---------------------|
| reviewer_001 | David Kim | 0.7 | 0.9 | 0.9 | Fast but selective workload |
| reviewer_002 | Emma Wilson | 1.4 | 0.6 | 1.5 | Slow and inconsistent, high workload |
| reviewer_003 | Frank Rodriguez | 1.0 | 1.0 | 1.0 | Average performer |
| reviewer_004 | Grace O'Brien | 1.1 | 0.8 | 1.2 | Slightly slower, more cases |

#### Health Inspectors

| Resource ID | Display Name | Speed | Consistency | Capacity | Profile Description |
|-------------|--------------|-------|-------------|----------|---------------------|
| inspector_001 | Henry Patel | 0.9 | 0.8 | 1.0 | Fast but variable |
| inspector_002 | Iris Thompson | 1.3 | 0.9 | 1.1 | Slower but consistent |
| inspector_003 | Jack Anderson | 1.0 | 1.0 | 0.9 | Average performer |

---

## 6. Event Log Data Model (Output Specification)

### 6.1 Generic Event Structure

The event log uses a **generic, attribute-agnostic data model** to ensure flexibility across different process types.

#### Core Event Fields (Required)

Each event **must** contain these core fields:

```
{
  case_id: string,           // Unique case identifier
  activity: string,          // Activity/state name
  timestamp: string,         // ISO 8601 datetime (e.g., "2024-09-15T08:30:00Z")
  attributes: object         // Key-value pairs for contextual data
}
```

#### Attributes Field (Flexible Schema)

The `attributes` object contains **zero or more** contextual attributes specific to the process domain. This design allows:

- **Domain Independence**: Different processes can include different attributes
- **Extensibility**: New attributes can be added without schema changes
- **Type Flexibility**: Values can be strings, numbers, booleans, or null

**Common Attribute Examples**:
- `resource`: Person/system performing the activity (string or null)
- `location`: Office, city, or facility (string)
- `department`: Organizational unit (string)
- `cost`: Activity cost (number)
- `quality_score`: Quality metric (number)
- `priority`: Case priority level (string/number)

#### Event Structure for This Process

For the permit application process, each event uses a **single attribute**:

```json
{
  "case_id": "PERMIT_2024_000001",
  "activity": "intake_validation",
  "timestamp": "2024-09-16T14:30:00Z",
  "attributes": {
    "resource": "clerk_001"
  }
}
```

**Attribute Definition**:
- **`resource`**: Resource ID performing the activity (string) or `null` for automated activities
- **Mapping**: This corresponds to the "performer" concept in process mining terminology

**Important**: Downstream consumers of the event log (visualization, analysis tools) must be **attribute-agnostic** and not hardcode attribute names like "resource" or "performer". Instead, they should:
1. Accept configuration specifying which attribute represents the resource dimension
2. Support multiple attributes for multi-dimensional analysis
3. Handle missing attributes gracefully

### 6.2 Event Log Container Structure

The complete event log contains:

```json
{
  "events": [
    // Array of event objects (see 6.1)
  ],
  "metadata": {
    "generated_at": "string",    // ISO 8601 timestamp of generation
    "total_cases": "number",     // Total number of cases in the log
    "seed": "number"             // Random seed for reproducibility
  }
}
```

### 6.3 Case Generation Process

#### Step 1: Variant Selection
1. Generate random value R between 0 and 1
2. Iterate through variants calculating cumulative probability
3. Select first variant where R ≤ cumulative probability

#### Step 2: Case ID Generation
- Format: `PERMIT_YYYY_NNNNNN`
- YYYY = year (e.g., 2024)
- NNNNNN = zero-padded sequence number (e.g., 000001)

#### Step 3: Timestamp Initialization
- Start with random timestamp within desired time window
- Default: Last 6 months, ending at least 30 days before current date
- Ensures completed cases

#### Step 4: Event Generation Loop
For each state in the variant sequence:

1. **Create Event**:
   - `case_id`: Assigned case ID
   - `activity`: Current state name
   - `timestamp`: Current timestamp (ISO 8601)
   - `attributes.resource`: Assigned resource ID (if human state) or null

2. **Resource Assignment** (if human state):
   - Identify resource pool for state
   - Calculate selection weights based on:
     - Capacity factor
     - Current workload penalty: `max(0.3, 1 - caseCount/100)`
     - Weight = `capacity × workloadPenalty`
   - Weighted random selection

3. **Transition Time Calculation**:
   - Get base duration from transition time range (random between min/max)
   - Apply resource speed multiplier (if human state)
   - Apply consistency variance: `1 + ((1 - consistency) × random(-0.5, 0.5))`
   - Apply fatigue effect: `1 + (fatigueLevel × 0.3)`
   - Random delay event (5% chance): multiply by 2-4× (simulates unexpected delays)
   - Peak time effect (30% chance): multiply by 1.1× (simulates busy periods)
   - Ensure minimum 0.1 hours (6 minutes)

4. **Update Timestamp**:
   - Add calculated duration to current timestamp

5. **Update Workload Tracking**:
   - Increment resource's case count
   - Add duration to total time
   - Update fatigue level: `min(1.0, caseCount / 50)`

#### Step 5: Event Log Assembly
1. Combine all events from all cases
2. Sort by timestamp (chronological order)
3. Add metadata:
   - `generated_at`: Current timestamp
   - `total_cases`: Number of cases generated
   - `seed`: Random seed (for reproducibility)

### 6.4 Workload Tracking

Maintain state for each resource:

```
{
  caseCount: number,     // Total cases assigned
  totalTime: number,     // Cumulative processing hours
  fatigueLevel: number   // 0.0 to 1.0, increases with caseCount
}
```

**Initialization**: All resources start with `{caseCount: 0, totalTime: 0, fatigueLevel: 0}`

**Fatigue Calculation**: `min(1.0, caseCount / 50)`
- At 50+ cases, resource reaches maximum fatigue

---

## 7. Random Variance & Realism Factors

### 7.1 Seeded Random Number Generation

**Purpose**: Ensure reproducible datasets

**Requirements**:
- Deterministic random sequence based on integer seed
- Uniform distribution [0, 1)
- Support for:
  - `nextFloat(min, max)`: Random float in range
  - `nextInt(min, max)`: Random integer in range
  - `choice(array)`: Random element from array

**Recommended Algorithm**: Linear Congruential Generator (LCG)
```
seed = (seed × 9301 + 49297) mod 233280
random = seed / 233280
```

### 7.2 Variance Components

#### Resource Speed Variance
- **Formula**: `baseDuration × resourceSpeed`
- **Effect**: Consistent resource-specific bias

#### Consistency Variance
- **Formula**: `1 + ((1 - consistency) × random(-0.5, 0.5))`
- **Effect**: Random variation within each case
- **Range**: ±50% variation for consistency = 0, no variation for consistency = 1.0

#### Fatigue Effect
- **Formula**: `1 + (fatigueLevel × 0.3)`
- **Effect**: Up to 30% slowdown at maximum fatigue
- **Progression**: Gradual increase with case count

#### Random Delay Events
- **Probability**: 5% of all transitions
- **Formula**: `baseDuration × random(2, 4)`
- **Effect**: 2-4× longer processing (simulates unexpected delays, resource unavailability, etc.)

#### Peak Time Effects
- **Probability**: 30% of all cases
- **Formula**: `baseDuration × 1.1`
- **Effect**: 10% slowdown during busy periods

### 7.3 Time Range Constraints

- **Minimum Duration**: 0.1 hours (6 minutes) - prevents zero/negative times
- **Temporal Coherence**: Each event timestamp must be ≥ previous event timestamp
- **Realistic Bounds**: Generated times should fall within defined min/max ranges (before variance)

---

## 8. Validation Rules

### 8.1 Event-Level Validation

Each event must satisfy:

1. **case_id**: Non-empty string
2. **activity**: Non-empty string, must be one of defined states
3. **timestamp**: Valid ISO 8601 datetime string
4. **attributes**: Object (can be empty `{}`)
5. **attributes.resource** (if present): Either string (resource ID) or null

### 8.2 Case-Level Validation

Each case (group of events with same case_id) must satisfy:

1. **Chronological Order**: Events sorted by timestamp (ascending)
2. **Final State**: Last activity must be one of: `approved`, `rejected`, `withdrawn`
3. **Valid Sequence**: Activity sequence must match one of the defined variants
4. **Resource Consistency**:
   - Human states have non-null `attributes.resource`
   - Automatic states have null `attributes.resource`

### 8.3 Log-Level Validation

The complete event log must satisfy:

1. **Global Chronological Order**: All events sorted by timestamp
2. **Metadata Presence**:
   - `generated_at`: ISO 8601 timestamp
   - `total_cases`: Positive integer
   - `seed`: Integer (for reproducibility)
3. **Case Completeness**: All cases have at least 2 events (start + end)
4. **Variant Distribution**: Actual variant counts should approximate expected probabilities (within statistical variance)

---

## 9. Configuration Parameters

### 9.1 Generator Configuration

Minimum required parameters:

```
{
  totalCases: integer,           // Number of cases to generate (recommended: 3000-5000 for realistic datasets)
  seed: integer,                 // Random seed for reproducibility (any integer)
  variantOverrides?: {           // Optional probability overrides
    variant_key: probability
  }
}
```

**Recommended Defaults**:
- `totalCases`: 3875 (provides sufficient statistical diversity)
- `seed`: 42 (conventional default for reproducibility)

### 9.2 Example Configurations

#### Standard Dataset (Recommended)
```
totalCases: 3875
seed: 42
```

#### Custom Variant Distribution
```
totalCases: 5000
seed: 12345
variantOverrides: {
  direct_approval: 0.70,    // Increase happy path to 70%
  info_loop: 0.15,          // Reduce rework to 15%
  rejected: 0.10,           // Keep rejections at 10%
  withdrawn: 0.03,          // Reduce withdrawals to 3%
  early_rejection: 0.02     // Reduce early rejections to 2%
}
```

**Note**: When using `variantOverrides`, probabilities are automatically normalized if they don't sum to 1.0.

---

## 10. Happy Path Configuration

### 10.1 Definition

The **Happy Path** represents the ideal process flow with:
- No loops or rework
- No delays or bottlenecks
- Optimal resource utilization
- Positive outcome (approval)

### 10.2 Current Happy Path

**Sequence**: `direct_approval` variant
```
submitted → intake_validation → assigned_to_reviewer →
review_in_progress → health_inspection → approved
```

**Usage**:
- Process visualization (green highlighting)
- Performance benchmarking
- Process improvement target

**Flexibility**: Can be configured to reference any variant or custom sequence

---

## 11. Process Characteristics & Analysis Considerations

### 11.1 Expected Timing Patterns

The process exhibits realistic timing variance with the following characteristics:

1. **Long-Duration Transitions**:
   - `applicant_provided_info->review_in_progress`: 2-14 days (re-review delay)
   - `assigned_to_reviewer->review_in_progress`: 2-5 days (queue time)
   - `review_in_progress->health_inspection`: 1-7 days (scheduling dependent)

2. **Short-Duration Transitions**:
   - `intake_validation->assigned_to_reviewer`: 6-30 minutes (automated)
   - `submitted->intake_validation`: 1-2 days (batch processing)

3. **Variance Sources**:
   - Resource speed differences (0.7-1.4× baseline)
   - Workload-based fatigue effects (up to 30% slowdown)
   - Random delay events (5% probability, 2-4× duration)
   - Peak time effects (30% probability, 10% slowdown)

### 11.2 Statistical Distribution Expectations

For a properly generated event log with recommended size (3000-5000 cases):

- **Variant Distribution**: Should approximate configured probabilities within ±3%
- **Timing Outliers**: ~5% of transitions will exhibit 2-4× longer durations (random delays)
- **Resource Utilization**: High-capacity resources will handle 1.2-1.5× more cases than low-capacity
- **Temporal Spread**: Cases distributed over 6-month window with 30-day completion buffer

---

## 12. Extension Points

### 12.1 Customization Options

To adapt this process definition:

1. **Add/Remove States**: Modify state list and update variant sequences
2. **Define New Variants**: Create new sequence paths with probabilities
3. **Adjust Transition Times**: Update min/max ranges based on domain
4. **Configure Resources**: Add/remove performers and adjust profiles
5. **Modify Variance Rules**: Tune bottleneck probability, peak time effects, etc.

### 12.2 Domain Adaptation

This process models **permit applications**, but the structure applies to:

- Insurance claim processing
- Loan approval workflows
- Customer support ticket handling
- Manufacturing quality control
- Healthcare patient pathways
- IT service request management

**Adaptation Steps**:
1. Replace state names with domain-specific activities
2. Define domain-specific variants and probabilities
3. Configure realistic transition times for the domain
4. Map resource types to domain roles
5. Adjust variance factors to match domain characteristics

---

## 13. Implementation Checklist

To implement an event log generator from this definition:

- [ ] Implement seeded random number generator
- [ ] Define all process states and classifications
- [ ] Configure variant sequences and probabilities
- [ ] Set up transition time ranges
- [ ] Configure performer pools and profiles
- [ ] Implement workload tracking system
- [ ] Build performer selection algorithm (capacity-based)
- [ ] Implement transition time calculation (with variance)
- [ ] Create event generation loop
- [ ] Add timestamp progression logic
- [ ] Implement fatigue and bottleneck effects
- [ ] Sort events chronologically
- [ ] Generate metadata
- [ ] Validate event log structure
- [ ] Validate case completeness
- [ ] Verify variant distribution

---

## 14. Quality Metrics

### 14.1 Expected Output Characteristics

A properly generated event log should exhibit:

1. **Variant Distribution**: Matches configured probabilities (±3-5% for datasets with 3000+ cases)
2. **Temporal Realism**: No negative time intervals, realistic progression
3. **Resource Utilization**: Workload distributed according to capacity profiles
4. **Process Flow Patterns**: Identifiable timing patterns matching configured ranges
5. **Completeness**: All cases end in final states
6. **Consistency**: Same seed produces identical output

### 14.2 Validation Metrics

Calculate these metrics to verify quality:

- **Variant Accuracy**: `|actual_probability - expected_probability| < 0.05`
- **Time Range Compliance**: 95% of base transition times fall within defined ranges (before variance multipliers)
- **Resource Balance**: Resource case counts correlate with capacity (Pearson r > 0.7)
- **Temporal Order**: 100% of events chronologically ordered within each case
- **Completeness**: 100% of cases have final state
- **Reproducibility**: Same seed produces identical event timestamps and resource assignments

---

## Appendix A: Quick Reference

### State Categories
- **Final**: approved, rejected, withdrawn
- **Human**: intake_validation, review_in_progress, health_inspection
- **Automatic**: submitted, assigned_to_reviewer, request_additional_info, applicant_provided_info

### Variant Summary
- Direct Approval: 58% (6 activities)
- Request More Info: 24% (9 activities, contains loop)
- Rejected at Final: 10% (6 activities)
- Withdrawn: 5% (6 activities)
- Early Rejection: 3% (3 activities)

### Resource Pools
- Clerks: 3 resources (Alice Martinez, Bob Chen, Carol Johnson)
- Reviewers: 4 resources (David Kim, Emma Wilson, Frank Rodriguez, Grace O'Brien)
- Health Inspectors: 3 resources (Henry Patel, Iris Thompson, Jack Anderson)

### Longest-Duration Transition
- **Transition**: applicant_provided_info → review_in_progress
- **Expected Time**: 2-14 days (48-336 hours)
- **Reason**: Re-reviews typically deprioritized vs. new cases
- **Impact**: Affects 24%+ of cases (info_loop variant)

### Time Multipliers
- Resource Speed: 0.7-1.4×
- Consistency Variance: ±50% max
- Fatigue Effect: +0-30%
- Random Delay Event: 2-4× (5% probability)
- Peak Time: +10% (30% probability)

---

## Appendix B: Example Event Log

### Case Example: Direct Approval Variant (Generic Format)

```json
{
  "events": [
    {
      "case_id": "PERMIT_2024_000001",
      "activity": "submitted",
      "timestamp": "2024-09-15T08:30:00Z",
      "attributes": {
        "resource": null
      }
    },
    {
      "case_id": "PERMIT_2024_000001",
      "activity": "intake_validation",
      "timestamp": "2024-09-16T14:30:00Z",
      "attributes": {
        "resource": "clerk_001"
      }
    },
    {
      "case_id": "PERMIT_2024_000001",
      "activity": "assigned_to_reviewer",
      "timestamp": "2024-09-16T14:42:00Z",
      "attributes": {
        "resource": null
      }
    },
    {
      "case_id": "PERMIT_2024_000001",
      "activity": "review_in_progress",
      "timestamp": "2024-09-19T10:15:00Z",
      "attributes": {
        "resource": "reviewer_003"
      }
    },
    {
      "case_id": "PERMIT_2024_000001",
      "activity": "health_inspection",
      "timestamp": "2024-09-23T09:00:00Z",
      "attributes": {
        "resource": "inspector_002"
      }
    },
    {
      "case_id": "PERMIT_2024_000001",
      "activity": "approved",
      "timestamp": "2024-09-26T16:30:00Z",
      "attributes": {
        "resource": null
      }
    }
  ],
  "metadata": {
    "generated_at": "2024-10-06T12:00:00Z",
    "total_cases": 1,
    "seed": 42
  }
}
```

**Case Characteristics**:
- **Variant**: Direct Approval (happy path)
- **Duration**: 11 days, 8 hours
- **Resources**: 3 unique resources (clerk_001, reviewer_003, inspector_002)
- **Activities**: 6 (minimum for successful approval)
- **Outcome**: Approved

### Example with Multiple Attributes (Extended Schema)

To demonstrate the generic attribute model, here's how the same event could include additional contextual attributes:

```json
{
  "case_id": "PERMIT_2024_000001",
  "activity": "intake_validation",
  "timestamp": "2024-09-16T14:30:00Z",
  "attributes": {
    "resource": "clerk_001",
    "location": "Downtown Office",
    "priority": "normal",
    "application_type": "food_service"
  }
}
```

**Note**: For the current process definition, only the `resource` attribute is used. Other attributes are optional extensions for domain-specific requirements.

---

## Version History

- **v1.0** (2024-10-06): Initial comprehensive process definition
