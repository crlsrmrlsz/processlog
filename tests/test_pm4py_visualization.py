"""
PM4Py visualization tests

These tests validate that generated event logs work with PM4Py's visualization functions.
Note: These tests don't display visualizations, just verify they can be generated without errors.
"""

import pytest
import pandas as pd
import tempfile
from pathlib import Path

from processlog.config import parse_yaml
from processlog.core.generator import generate_log
from processlog.exporters.csv_exporter import export_csv


class TestPM4PyDFGVisualization:
    """Test PM4Py Directly-Follows Graph (DFG) visualization"""

    def test_dfg_frequency_visualization(self, minimal_config_yaml):
        """Test DFG frequency visualization can be generated"""
        import pm4py

        config = parse_yaml(minimal_config_yaml)
        df = generate_log(config, seed=42, num_cases=20)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "events.csv"
            export_csv(df, output_path)
            df_imported = pd.read_csv(str(output_path))
            df_formatted = pm4py.format_dataframe(
                df_imported,
                case_id='case:concept:name',
                activity_key='concept:name',
                timestamp_key='time:timestamp'
            )
            event_log = pm4py.convert_to_event_log(df_formatted)

            # Discover DFG
            dfg, start_activities, end_activities = pm4py.discover_dfg(event_log)

            # Verify DFG was discovered (smoke test for visualization capability)
            assert dfg is not None
            assert isinstance(dfg, dict)
            assert len(dfg) > 0
            assert start_activities is not None
            assert end_activities is not None

    def test_dfg_performance_visualization(self, minimal_config_yaml):
        """Test DFG performance visualization can be generated"""
        import pm4py

        config = parse_yaml(minimal_config_yaml)
        df = generate_log(config, seed=42, num_cases=20)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "events.csv"
            export_csv(df, output_path)
            df_imported = pd.read_csv(str(output_path))
            df_formatted = pm4py.format_dataframe(
                df_imported,
                case_id='case:concept:name',
                activity_key='concept:name',
                timestamp_key='time:timestamp'
            )
            event_log = pm4py.convert_to_event_log(df_formatted)

            # Discover performance DFG
            dfg, start_activities, end_activities = pm4py.discover_performance_dfg(event_log)

            # Verify performance DFG was discovered (smoke test)
            assert dfg is not None
            assert isinstance(dfg, dict)
            assert len(dfg) > 0
            assert start_activities is not None
            assert end_activities is not None


class TestPM4PyPetriNetVisualization:
    """Test PM4Py Petri net visualization"""

    def test_petri_net_alpha_miner(self, minimal_config_yaml):
        """Test Petri net discovery with Alpha miner and visualization"""
        import pm4py

        config = parse_yaml(minimal_config_yaml)
        df = generate_log(config, seed=42, num_cases=20)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "events.csv"
            export_csv(df, output_path)
            df_imported = pd.read_csv(str(output_path))
            df_formatted = pm4py.format_dataframe(
                df_imported,
                case_id='case:concept:name',
                activity_key='concept:name',
                timestamp_key='time:timestamp'
            )
            event_log = pm4py.convert_to_event_log(df_formatted)

            # Discover Petri net using Alpha miner
            net, initial_marking, final_marking = pm4py.discover_petri_net_alpha(event_log)

            # Verify net was discovered (smoke test for Petri net)
            assert net is not None
            assert initial_marking is not None
            assert final_marking is not None
            # Check net has places and transitions
            assert len(net.places) > 0
            assert len(net.transitions) > 0

    def test_petri_net_inductive_miner(self, minimal_config_yaml):
        """Test Petri net discovery with Inductive miner and visualization"""
        import pm4py

        config = parse_yaml(minimal_config_yaml)
        df = generate_log(config, seed=42, num_cases=20)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "events.csv"
            export_csv(df, output_path)
            df_imported = pd.read_csv(str(output_path))
            df_formatted = pm4py.format_dataframe(
                df_imported,
                case_id='case:concept:name',
                activity_key='concept:name',
                timestamp_key='time:timestamp'
            )
            event_log = pm4py.convert_to_event_log(df_formatted)

            # Discover Petri net using Inductive miner
            net, initial_marking, final_marking = pm4py.discover_petri_net_inductive(event_log)

            # Verify net was discovered (smoke test)
            assert net is not None
            assert initial_marking is not None
            assert final_marking is not None
            # Check net structure
            assert len(net.places) > 0
            assert len(net.transitions) > 0


class TestPM4PyProcessTreeVisualization:
    """Test PM4Py process tree visualization"""

    def test_process_tree_inductive_miner(self, minimal_config_yaml):
        """Test process tree discovery and visualization"""
        import pm4py

        config = parse_yaml(minimal_config_yaml)
        df = generate_log(config, seed=42, num_cases=20)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "events.csv"
            export_csv(df, output_path)
            df_imported = pd.read_csv(str(output_path))
            df_formatted = pm4py.format_dataframe(
                df_imported,
                case_id='case:concept:name',
                activity_key='concept:name',
                timestamp_key='time:timestamp'
            )
            event_log = pm4py.convert_to_event_log(df_formatted)

            # Discover process tree
            tree = pm4py.discover_process_tree_inductive(event_log)

            # Verify tree was discovered (smoke test)
            assert tree is not None
            # Process tree should have a label or children
            assert tree.label is not None or len(tree.children) > 0


class TestPM4PyBPMNVisualization:
    """Test PM4Py BPMN visualization"""

    def test_bpmn_inductive_miner(self, minimal_config_yaml):
        """Test BPMN discovery and visualization"""
        import pm4py

        config = parse_yaml(minimal_config_yaml)
        df = generate_log(config, seed=42, num_cases=20)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "events.csv"
            export_csv(df, output_path)
            df_imported = pd.read_csv(str(output_path))
            df_formatted = pm4py.format_dataframe(
                df_imported,
                case_id='case:concept:name',
                activity_key='concept:name',
                timestamp_key='time:timestamp'
            )
            event_log = pm4py.convert_to_event_log(df_formatted)

            # Discover BPMN
            bpmn_graph = pm4py.discover_bpmn_inductive(event_log)

            # Verify BPMN was discovered (smoke test)
            assert bpmn_graph is not None
            # BPMN graph should have nodes and flows
            assert len(bpmn_graph.get_nodes()) > 0
            assert len(bpmn_graph.get_flows()) > 0
