# Example Process Configurations

This directory contains example YAML configurations demonstrating different use cases and process types.

## Available Examples

### 1. Simple Process (`simple_process.yaml`)
**Purpose**: Learning and quick testing

A minimal 3-activity order processing flow with basic branching:
- 1 automatic start activity
- 1 human validation activity
- 2 terminal outcomes (95% success, 5% cancellation)

**Ideal for**:
- Learning YAML configuration syntax
- Quick sanity checks
- Understanding basic process structure
- Testing with minimal complexity

**Generate**:
```bash
event-log-gen generate -c configs/examples/simple_process.yaml -n 100
```

---

### 2. Baseline Process (`baseline_process.yaml`)
**Purpose**: Regression testing and benchmarking

A stable, predictable invoice processing flow:
- Single process variant (100% success rate)
- Consistent resource performance (high consistency values)
- No anomalies or calendar restrictions
- Low variance durations for predictability

**Ideal for**:
- Regression testing (consistent results with same seed)
- Performance benchmarking
- Algorithm validation with known ground truth
- Creating reference datasets

**Generate**:
```bash
event-log-gen generate -c configs/examples/baseline_process.yaml -n 1000 -s 42
```

**Expected Characteristics**:
- All cases follow identical path
- Predictable total duration (~1.6 hours per case)
- High conformance rate (>99%)
- Minimal performance variance

---

### 3. High Variance Process (`high_variance_process.yaml`)
**Purpose**: Anomaly detection and performance analysis

A complex loan application process with high variability:
- 3 process variants with different probabilities
- Resources with widely different speeds (0.5x to 1.8x)
- Peak time effects (30% slower during rush hours)
- Random delays (5% probability)
- Business hours and holiday restrictions
- Wide duration ranges

**Ideal for**:
- Testing anomaly detection algorithms
- Performance analysis and optimization
- Resource behavior modeling
- Time-based pattern recognition
- Evaluating process mining robustness

**Generate**:
```bash
event-log-gen generate -c configs/examples/high_variance_process.yaml -n 500
```

**Expected Characteristics**:
- Multiple process paths (85% approved, 15% rejected at first step)
- High duration variance (0.5-12 hours for some activities)
- Resource-dependent performance
- Calendar gaps (weekends, holidays)
- Occasional random delays

---

## Configuration Comparison

| Feature | Simple | Baseline | High Variance |
|---------|--------|----------|---------------|
| **Activities** | 4 | 5 | 9 |
| **Variants** | 2 | 1 | 3 |
| **Resources** | 1 | 4 | 8 |
| **Resource Pools** | 1 | 2 | 3 |
| **Working Calendar** | No | No | Yes (9-5, weekends off) |
| **Anomalies** | No | No | Yes (delays + peak times) |
| **Variance** | Medium | Low | High |
| **Complexity** | Minimal | Low | High |

## Usage Tips

### Quick Validation
Before generating, validate your configuration:
```bash
event-log-gen validate -c configs/examples/simple_process.yaml
```

### View Process Information
Get a summary without generating:
```bash
event-log-gen info -c configs/examples/baseline_process.yaml
```

### Generate All Formats
Create CSV, Parquet, JSON, and XES at once:
```bash
event-log-gen generate -c configs/examples/high_variance_process.yaml -n 200 -f all
```

### Reproducible Generation
Use a fixed seed for identical results:
```bash
event-log-gen generate -c configs/examples/baseline_process.yaml -n 100 -s 42
```

## Creating Your Own Configuration

Start with `simple_process.yaml` and incrementally add:
1. More activities and transitions
2. Additional resource pools
3. Custom attributes (event/case level)
4. Working calendar restrictions
5. Anomaly behaviors

See the full configuration example in `../process_config.yaml` for all available options.

## Testing with PM4Py

All generated logs are directly PM4Py-compatible:

```python
import pm4py

# Load and analyze
log = pm4py.read_csv('output/events.csv')
dfg, start, end = pm4py.discover_dfg(log)
pm4py.view_dfg(dfg, start, end)
```

## Support

For detailed documentation, see:
- Configuration reference: `../process_config.yaml` (fully annotated)
- Architecture design: `../../docs/ARCHITECTURE.md`
- Main README: `../../README.md`
