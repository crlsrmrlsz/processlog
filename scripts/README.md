# Visualization Scripts

This directory contains scripts for generating PM4Py visualizations from event logs.

## Requirements

### System Package (Required)
PM4Py visualizations require the **Graphviz** system package to render graphs as PNG images.

**Install on Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install graphviz
```

**Install on macOS:**
```bash
brew install graphviz
```

**Install on Windows:**
Download and install from: https://graphviz.org/download/

After installation, verify with:
```bash
dot -V
```

### Python Environment
Ensure you have the virtual environment activated and dependencies installed:
```bash
source venv/bin/activate  # Or: venv\Scripts\activate on Windows
pip install -e .
```

## Usage

### Option 1: Run with wrapper script (recommended)
The wrapper script checks all prerequisites automatically:
```bash
./scripts/run_visualizations.sh
```

### Option 2: Run directly with Python
If you prefer to run the Python script directly:

**Step 1: Verify Graphviz is installed**
```bash
dot -V
# Should output: dot - graphviz version X.Y.Z
```

**Step 2: Activate virtual environment**
```bash
source venv/bin/activate  # Or: venv\Scripts\activate on Windows
```

**Step 3: Run the script**
```bash
python3 scripts/generate_visualizations.py
```

**Alternative: Make executable and run**
```bash
chmod +x scripts/generate_visualizations.py
./scripts/generate_visualizations.py
```

## Output

The script generates 6 PNG visualizations in the `visualizations/` folder:

1. **01_dfg_frequency.png** - Directly-Follows Graph showing activity frequencies
2. **02_dfg_performance.png** - DFG with performance metrics (durations)
3. **03_petri_net_inductive.png** - Petri net discovered with Inductive Miner
4. **04_petri_net_alpha.png** - Petri net discovered with Alpha Miner
5. **05_process_tree.png** - Process tree representation
6. **06_bpmn.png** - BPMN diagram

## What it Does

1. Loads `configs/process_config.yaml` (restaurant permit process)
2. Generates 100 realistic cases with:
   - Resource allocation (capacity-weighted selection)
   - Working calendar (business hours, weekends, holidays)
   - Custom attributes (cost, priority, applicant type)
3. Exports to CSV and reloads with PM4Py
4. Discovers 6 different process models
5. Saves visualizations as PNG images

## Event Log Statistics

With the default configuration (100 cases, seed=42):
- **Total events**: ~700-750 events
- **Unique activities**: 14 activities (from permit process)
- **Variants**: 5 different process variants (standard, expedited, etc.)
- **Date range**: Spans several weeks (depends on calendar settings)

## Troubleshooting

### Error: "failed to execute PosixPath('dot')"
**Cause**: Graphviz system package not installed.
**Solution**: Install Graphviz (see Requirements above).

### Error: "ModuleNotFoundError: No module named 'pandas'"
**Cause**: Virtual environment not activated or dependencies not installed.
**Solution**: Run `source venv/bin/activate && pip install -e .`

### Error: "FileNotFoundError: process_config.yaml"
**Cause**: Running from wrong directory.
**Solution**: Run from project root, or use the wrapper script.

## Notes

- Visualization generation can take 10-30 seconds depending on log size
- PNG files are typically 50-200 KB each
- Larger event logs (more cases) produce more complex visualizations
- Change `num_cases` in the script to generate different log sizes
