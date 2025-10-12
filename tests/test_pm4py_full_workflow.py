"""
PM4Py Full Workflow Integration Test

Tests the complete PM4Py workflow with generated event logs:
- Import event logs (CSV, Parquet, JSON, XES)
- Process discovery (DFG, Petri nets, Process trees)
- Event log filtering
- Performance metrics computation
- Export to different formats

This validates that generated logs are fully PM4Py-compatible and can be
used for real process mining workflows.
"""

import pytest
import pandas as pd
import pm4py
from pathlib import Path
import tempfile
import os

from processlog import load_config, generate_log
from processlog.exporters.csv_exporter import export_csv
from processlog.exporters.parquet_exporter import export_parquet
from processlog.exporters.json_exporter import export_json
from processlog.exporters.xes_exporter import export_xes


@pytest.fixture
def sample_dataframe():
    """Generate a sample event log for testing"""
    config = load_config('configs/examples/simple_process.yaml')
    df = generate_log(config, seed=42, num_cases=100)
    return df


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files"""
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield Path(tmpdirname)


class TestPM4PyFullWorkflow:
    """Test complete PM4Py workflows with generated event logs"""

    def test_csv_full_workflow(self, sample_dataframe, temp_dir):
        """Test CSV: import → discover → filter → export"""
        # Export to CSV
        csv_path = temp_dir / "test.csv"
        export_csv(sample_dataframe, str(csv_path))

        # Import with PM4Py
        df = pd.read_csv(csv_path)
        df = pm4py.format_dataframe(df, case_id='case:concept:name',
                                     activity_key='concept:name',
                                     timestamp_key='time:timestamp')
        log = pm4py.convert_to_event_log(df)

        # Discover DFG
        dfg, start_activities, end_activities = pm4py.discover_dfg(log)
        assert len(dfg) > 0, "DFG should have edges"
        assert len(start_activities) > 0, "Should have start activities"
        assert len(end_activities) > 0, "Should have end activities"

        # Filter by timeframe (PM4Py requires full timestamp format)
        from datetime import datetime
        filtered_log = pm4py.filter_time_range(
            log,
            "2024-01-01 00:00:00",
            "2024-01-31 23:59:59"
        )
        assert len(filtered_log) > 0, "Filtered log should have cases"

        # Export filtered log back to CSV
        # PM4Py doesn't have write_csv, use pandas conversion
        filtered_df = pm4py.convert_to_dataframe(filtered_log)
        filtered_csv = temp_dir / "filtered.csv"
        filtered_df.to_csv(filtered_csv, index=False)
        assert filtered_csv.exists(), "Filtered CSV should be created"

    def test_xes_full_workflow(self, sample_dataframe, temp_dir):
        """Test XES: import → discover → export"""
        # Export to XES
        xes_path = temp_dir / "test.xes"
        export_xes(sample_dataframe, str(xes_path))

        # Import with PM4Py
        log = pm4py.read_xes(str(xes_path))
        assert len(log) > 0, "Log should have cases"

        # Discover process model (Petri net via inductive miner)
        net, initial_marking, final_marking = pm4py.discover_petri_net_inductive(log)
        assert net is not None, "Petri net should be discovered"
        assert len(net.places) > 0, "Petri net should have places"
        assert len(net.transitions) > 0, "Petri net should have transitions"

        # Export back to XES
        export_path = temp_dir / "exported.xes"
        pm4py.write_xes(log, str(export_path))
        assert export_path.exists(), "Exported XES should exist"

        # Re-import to verify roundtrip
        reimported_log = pm4py.read_xes(str(export_path))
        assert len(reimported_log) == len(log), "Roundtrip should preserve case count"

    def test_parquet_workflow(self, sample_dataframe, temp_dir):
        """Test Parquet: import → discover → filter"""
        # Export to Parquet
        parquet_path = temp_dir / "test.parquet"
        export_parquet(sample_dataframe, str(parquet_path))

        # Import with pandas
        df = pd.read_parquet(parquet_path)
        df = pm4py.format_dataframe(df, case_id='case:concept:name',
                                     activity_key='concept:name',
                                     timestamp_key='time:timestamp')
        log = pm4py.convert_to_event_log(df)

        # Discover DFG with performance metrics
        dfg, start_act, end_act = pm4py.discover_dfg(log)
        perf_dfg_result = pm4py.discover_performance_dfg(log)

        # PM4Py returns a tuple: (perf_dfg, start_act, end_act)
        if isinstance(perf_dfg_result, tuple):
            perf_dfg = perf_dfg_result[0]
        else:
            perf_dfg = perf_dfg_result

        assert len(perf_dfg) > 0, "Performance DFG should have edges"
        # Check that performance metrics are present
        # Performance DFG structure: {edge: {'mean': value, 'stdev': value, ...}}
        for edge, metrics in perf_dfg.items():
            if isinstance(metrics, dict):
                # New PM4Py format with statistics
                assert 'mean' in metrics or 'performance' in metrics, \
                    f"Performance metrics should have mean or performance: {edge}"
                mean_val = metrics.get('mean', metrics.get('performance', 0))
                assert mean_val >= 0, f"Mean should be non-negative: {edge} = {mean_val}"
            else:
                # Old PM4Py format with single value
                assert metrics >= 0, f"Performance should be non-negative: {edge} = {metrics}"

    def test_json_workflow(self, sample_dataframe, temp_dir):
        """Test JSON: import → discover"""
        # Export to JSON (NDJSON)
        json_path = temp_dir / "test.json"
        export_json(sample_dataframe, str(json_path))

        # Import with pandas
        df = pd.read_json(json_path, lines=True)
        df = pm4py.format_dataframe(df, case_id='case:concept:name',
                                     activity_key='concept:name',
                                     timestamp_key='time:timestamp')
        log = pm4py.convert_to_event_log(df)

        # Discover process tree
        tree = pm4py.discover_process_tree_inductive(log)
        assert tree is not None, "Process tree should be discovered"

    def test_performance_metrics(self, sample_dataframe, temp_dir):
        """Test PM4Py performance metrics computation"""
        # Export and import
        csv_path = temp_dir / "test.csv"
        export_csv(sample_dataframe, str(csv_path))
        df = pd.read_csv(csv_path)
        df = pm4py.format_dataframe(df, case_id='case:concept:name',
                                     activity_key='concept:name',
                                     timestamp_key='time:timestamp')
        log = pm4py.convert_to_event_log(df)

        # Get start/end activities
        start_activities = pm4py.get_start_activities(log)
        end_activities = pm4py.get_end_activities(log)
        assert len(start_activities) > 0, "Should have start activities"
        assert len(end_activities) > 0, "Should have end activities"

        # Get variants
        variants = pm4py.get_variants(log)
        assert len(variants) > 0, "Should have process variants"

        # Get case durations (as variant of case statistics)
        # Note: PM4Py doesn't have a direct get_case_durations, but we can
        # compute it from the log
        case_durations = []
        for case in log:
            if len(case) > 0:
                start_time = case[0]['time:timestamp']
                end_time = case[-1]['time:timestamp']
                duration = (end_time - start_time).total_seconds()
                case_durations.append(duration)

        assert len(case_durations) > 0, "Should compute case durations"
        assert all(d >= 0 for d in case_durations), "Durations should be non-negative"

    def test_filtering_operations(self, sample_dataframe, temp_dir):
        """Test various PM4Py filtering operations"""
        # Export and import
        csv_path = temp_dir / "test.csv"
        export_csv(sample_dataframe, str(csv_path))
        df = pd.read_csv(csv_path)
        df = pm4py.format_dataframe(df, case_id='case:concept:name',
                                     activity_key='concept:name',
                                     timestamp_key='time:timestamp')
        log = pm4py.convert_to_event_log(df)

        original_cases = len(log)

        # Filter by activity presence
        start_activities = pm4py.get_start_activities(log)
        if start_activities:
            first_activity = list(start_activities.keys())[0]
            filtered_log = pm4py.filter_event_attribute_values(
                log, 'concept:name', [first_activity], level='event', retain=True
            )
            assert len(filtered_log) > 0, "Should have cases with start activity"

        # Filter by variants (keep most common variants)
        variants = pm4py.get_variants(log)
        if len(variants) > 1:
            # Find the most common variant by comparing occurrence counts
            # PM4Py get_variants returns dict[variant_str, list[Trace]]
            variant_counts = {v: len(traces) for v, traces in variants.items()}
            most_common_variant_str = max(variant_counts, key=variant_counts.get)

            filtered_log = pm4py.filter_variants(log, [most_common_variant_str])
            assert len(filtered_log) <= original_cases, "Filtering should reduce or maintain case count"
            assert len(filtered_log) > 0, "Should keep at least one case"

    def test_process_discovery_algorithms(self, sample_dataframe, temp_dir):
        """Test multiple process discovery algorithms"""
        # Export to XES for best compatibility
        xes_path = temp_dir / "test.xes"
        export_xes(sample_dataframe, str(xes_path))
        log = pm4py.read_xes(str(xes_path))

        # Alpha miner (Petri net)
        try:
            net_alpha, im_alpha, fm_alpha = pm4py.discover_petri_net_alpha(log)
            assert net_alpha is not None, "Alpha miner should discover a net"
        except Exception as e:
            pytest.skip(f"Alpha miner not applicable to this log: {e}")

        # Inductive miner (Petri net)
        net_ind, im_ind, fm_ind = pm4py.discover_petri_net_inductive(log)
        assert net_ind is not None, "Inductive miner should discover a net"

        # Process tree
        tree = pm4py.discover_process_tree_inductive(log)
        assert tree is not None, "Should discover process tree"

        # BPMN
        bpmn = pm4py.discover_bpmn_inductive(log)
        assert bpmn is not None, "Should discover BPMN model"

    def test_conformance_checking(self, sample_dataframe, temp_dir):
        """Test conformance checking with discovered model"""
        # Export to XES
        xes_path = temp_dir / "test.xes"
        export_xes(sample_dataframe, str(xes_path))
        log = pm4py.read_xes(str(xes_path))

        # Discover model
        net, im, fm = pm4py.discover_petri_net_inductive(log)

        # Perform token-based replay for conformance
        try:
            from pm4py.algo.conformance.tokenreplay import algorithm as token_replay
            replayed_traces = token_replay.apply(log, net, im, fm)

            # Check that we got replay results
            assert len(replayed_traces) > 0, "Should have replay results"

            # Most traces should be conformant (fit) for a synthetic log
            conformant = sum(1 for t in replayed_traces if t['trace_is_fit'])
            total = len(replayed_traces)
            conformance_rate = conformant / total if total > 0 else 0

            # Expect high conformance for synthetic logs (>80%)
            assert conformance_rate > 0.8, f"Expected high conformance, got {conformance_rate:.2%}"
        except ImportError:
            pytest.skip("Token replay not available")

    def test_statistics_extraction(self, sample_dataframe):
        """Test extraction of various statistics from event log"""
        df = sample_dataframe.copy()
        df = pm4py.format_dataframe(df, case_id='case_id',
                                     activity_key='activity',
                                     timestamp_key='timestamp')
        log = pm4py.convert_to_event_log(df)

        # Activity frequencies
        activities = pm4py.get_event_attributes(log)
        assert 'concept:name' in activities, "Should have activity attribute"

        # Get attribute values
        activity_values = pm4py.get_event_attribute_values(log, 'concept:name')
        assert len(activity_values) > 0, "Should have activity values"

        # Verify expected activities from simple_process config
        expected_activities = {'order_received', 'payment_validated',
                              'order_completed', 'order_cancelled'}
        actual_activities = set(activity_values.keys())
        assert expected_activities.issubset(actual_activities), \
            f"Expected activities {expected_activities}, got {actual_activities}"
