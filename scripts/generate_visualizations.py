#!/usr/bin/env python3
"""
Generate PM4Py visualizations from event log

This script generates a realistic event log using the restaurant permit process
configuration and creates 6 different PM4Py visualizations:
1. DFG (Directly-Follows Graph) - Frequency
2. DFG - Performance
3. Petri Net - Inductive Miner
4. Petri Net - Alpha Miner
5. Process Tree
6. BPMN

All visualizations are saved as PNG files in the visualizations/ folder.
"""

import sys
from pathlib import Path
import tempfile

# Add src to path so we can import event_log_gen
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pandas as pd
import pm4py
from event_log_gen.config import parse_yaml
from event_log_gen.core.generator import generate_log
from event_log_gen.exporters.csv_exporter import export_csv


def main():
    """Generate event log and create visualizations"""

    # Configuration
    config_path = Path(__file__).parent.parent / "configs" / "process_config.yaml"
    output_dir = Path(__file__).parent.parent / "visualizations"
    num_cases = 100
    seed = 42

    print(f"Event Log Visualization Generator")
    print(f"=" * 80)
    print(f"Config: {config_path}")
    print(f"Output directory: {output_dir}")
    print(f"Number of cases: {num_cases}")
    print(f"Random seed: {seed}")
    print()

    # Create output directory
    output_dir.mkdir(exist_ok=True)
    print(f"✓ Created output directory: {output_dir}")

    # Load configuration
    print(f"Loading configuration...")
    with open(config_path, "r") as f:
        config_yaml = f.read()
    config = parse_yaml(config_yaml)
    print(f"✓ Configuration loaded")

    # Generate event log
    print(f"Generating event log ({num_cases} cases, seed={seed})...")
    df = generate_log(config, seed=seed, num_cases=num_cases)
    print(f"✓ Generated {len(df)} events across {df['case_id'].nunique()} cases")

    # Export to CSV and reload with PM4Py
    print(f"Exporting to CSV...")
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = Path(tmpdir) / "events.csv"
        export_csv(df, csv_path)

        print(f"Loading with PM4Py...")
        df_imported = pd.read_csv(str(csv_path))
        df_formatted = pm4py.format_dataframe(
            df_imported,
            case_id='case:concept:name',
            activity_key='concept:name',
            timestamp_key='time:timestamp'
        )
        event_log = pm4py.convert_to_event_log(df_formatted)
        print(f"✓ Event log loaded into PM4Py")

    print()
    print(f"Generating visualizations...")
    print(f"-" * 80)

    # 1. DFG - Frequency
    print(f"1/6 DFG (Frequency)...", end=" ", flush=True)
    dfg_freq, sa_freq, ea_freq = pm4py.discover_dfg(event_log)
    pm4py.save_vis_dfg(
        dfg_freq, sa_freq, ea_freq,
        str(output_dir / "01_dfg_frequency.png")
    )
    print(f"✓")

    # 2. DFG - Performance
    print(f"2/6 DFG (Performance)...", end=" ", flush=True)
    dfg_perf, sa_perf, ea_perf = pm4py.discover_performance_dfg(event_log)
    pm4py.save_vis_performance_dfg(
        dfg_perf, sa_perf, ea_perf,
        str(output_dir / "02_dfg_performance.png")
    )
    print(f"✓")

    # 3. Petri Net - Inductive Miner
    print(f"3/6 Petri Net (Inductive Miner)...", end=" ", flush=True)
    net_ind, im_ind, fm_ind = pm4py.discover_petri_net_inductive(event_log)
    pm4py.save_vis_petri_net(
        net_ind, im_ind, fm_ind,
        str(output_dir / "03_petri_net_inductive.png")
    )
    print(f"✓")

    # 4. Petri Net - Alpha Miner
    print(f"4/6 Petri Net (Alpha Miner)...", end=" ", flush=True)
    net_alpha, im_alpha, fm_alpha = pm4py.discover_petri_net_alpha(event_log)
    pm4py.save_vis_petri_net(
        net_alpha, im_alpha, fm_alpha,
        str(output_dir / "04_petri_net_alpha.png")
    )
    print(f"✓")

    # 5. Process Tree
    print(f"5/6 Process Tree...", end=" ", flush=True)
    tree = pm4py.discover_process_tree_inductive(event_log)
    pm4py.save_vis_process_tree(
        tree,
        str(output_dir / "05_process_tree.png")
    )
    print(f"✓")

    # 6. BPMN
    print(f"6/6 BPMN...", end=" ", flush=True)
    bpmn = pm4py.discover_bpmn_inductive(event_log)
    pm4py.save_vis_bpmn(
        bpmn,
        str(output_dir / "06_bpmn.png")
    )
    print(f"✓")

    print()
    print(f"=" * 80)
    print(f"SUCCESS! All visualizations generated:")
    print()
    print(f"  {output_dir}/01_dfg_frequency.png")
    print(f"  {output_dir}/02_dfg_performance.png")
    print(f"  {output_dir}/03_petri_net_inductive.png")
    print(f"  {output_dir}/04_petri_net_alpha.png")
    print(f"  {output_dir}/05_process_tree.png")
    print(f"  {output_dir}/06_bpmn.png")
    print()
    print(f"Event log statistics:")
    print(f"  Total events: {len(df)}")
    print(f"  Total cases: {df['case_id'].nunique()}")
    print(f"  Unique activities: {df['activity'].nunique()}")
    print(f"  Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    print()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
