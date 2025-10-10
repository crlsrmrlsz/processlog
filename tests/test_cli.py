"""
CLI Tests

Tests for the command-line interface (event-log-gen command).
Tests all three subcommands: generate, validate, and info.
"""

import pytest
from pathlib import Path
import tempfile
import subprocess
import sys
import os


class TestCLIGenerate:
    """Test the 'generate' subcommand"""

    def test_generate_csv_default(self, tmp_path):
        """Test generating CSV with default parameters"""
        result = subprocess.run(
            [sys.executable, "-m", "event_log_gen.cli", "generate",
             "-c", "configs/examples/simple_process.yaml",
             "-n", "10",
             "-f", "csv",
             "-o", str(tmp_path / "output")],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        assert "Generated 30 events" in result.stdout or "events across" in result.stdout
        assert (tmp_path / "output" / "events.csv").exists()

    def test_generate_all_formats(self, tmp_path):
        """Test generating all formats at once"""
        result = subprocess.run(
            [sys.executable, "-m", "event_log_gen.cli", "generate",
             "-c", "configs/examples/simple_process.yaml",
             "-n", "5",
             "-f", "all",
             "-o", str(tmp_path / "all_formats")],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, f"CLI failed: {result.stderr}"

        output_dir = tmp_path / "all_formats"
        assert (output_dir / "events.csv").exists()
        assert (output_dir / "events.parquet").exists()
        assert (output_dir / "events.json").exists()
        assert (output_dir / "events.xes").exists()

    def test_generate_with_custom_seed(self, tmp_path):
        """Test generating with custom seed for reproducibility"""
        seed = 12345
        output1 = tmp_path / "seed1"
        output2 = tmp_path / "seed2"

        # Generate twice with same seed
        for output_dir in [output1, output2]:
            result = subprocess.run(
                [sys.executable, "-m", "event_log_gen.cli", "generate",
                 "-c", "configs/examples/simple_process.yaml",
                 "-n", "5",
                 "-s", str(seed),
                 "-f", "csv",
                 "-o", str(output_dir)],
                capture_output=True,
                text=True
            )
            assert result.returncode == 0

        # Compare generated files - should be identical
        with open(output1 / "events.csv") as f1, open(output2 / "events.csv") as f2:
            assert f1.read() == f2.read(), "Same seed should produce identical output"

    def test_generate_invalid_config(self):
        """Test error handling with invalid config path"""
        result = subprocess.run(
            [sys.executable, "-m", "event_log_gen.cli", "generate",
             "-c", "nonexistent_config.yaml",
             "-n", "10"],
            capture_output=True,
            text=True
        )

        assert result.returncode != 0
        # CLI prints errors to stdout
        assert "Error" in result.stdout or "not found" in result.stdout.lower()

    def test_generate_output_to_current_dir(self, tmp_path):
        """Test generating to current directory (default)"""
        # Need absolute path to config when running from different directory
        import os
        config_path = os.path.abspath("configs/examples/simple_process.yaml")

        result = subprocess.run(
            [sys.executable, "-m", "event_log_gen.cli", "generate",
             "-c", config_path,
             "-n", "5",
             "-f", "csv"],
            capture_output=True,
            text=True,
            cwd=str(tmp_path)
        )

        assert result.returncode == 0
        # Should create output/ subdirectory
        assert (tmp_path / "output" / "events.csv").exists()

    def test_generate_multiple_formats(self, tmp_path):
        """Test generating multiple specific formats"""
        result = subprocess.run(
            [sys.executable, "-m", "event_log_gen.cli", "generate",
             "-c", "configs/examples/simple_process.yaml",
             "-n", "10",
             "-f", "csv", "parquet",
             "-o", str(tmp_path / "multi")],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0

        output_dir = tmp_path / "multi"
        assert (output_dir / "events.csv").exists()
        assert (output_dir / "events.parquet").exists()
        assert not (output_dir / "events.json").exists()  # Not requested
        assert not (output_dir / "events.xes").exists()   # Not requested


class TestCLIValidate:
    """Test the 'validate' subcommand"""

    def test_validate_valid_config(self):
        """Test validating a valid configuration"""
        result = subprocess.run(
            [sys.executable, "-m", "event_log_gen.cli", "validate",
             "-c", "configs/examples/simple_process.yaml"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "valid" in result.stdout.lower() or "✓" in result.stdout

    def test_validate_full_config(self):
        """Test validating the full process config"""
        result = subprocess.run(
            [sys.executable, "-m", "event_log_gen.cli", "validate",
             "-c", "configs/process_config.yaml"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        # May have warnings but should be valid
        assert "valid" in result.stdout.lower() or "✓" in result.stdout

    def test_validate_nonexistent_file(self):
        """Test validating nonexistent file"""
        result = subprocess.run(
            [sys.executable, "-m", "event_log_gen.cli", "validate",
             "-c", "nonexistent.yaml"],
            capture_output=True,
            text=True
        )

        assert result.returncode != 0
        # CLI prints errors to stdout
        assert "Error" in result.stdout or "not found" in result.stdout.lower()

    def test_validate_invalid_yaml(self, tmp_path):
        """Test validating invalid YAML syntax"""
        invalid_yaml = tmp_path / "invalid.yaml"
        invalid_yaml.write_text("process_name: test\nactivities: [broken yaml")

        result = subprocess.run(
            [sys.executable, "-m", "event_log_gen.cli", "validate",
             "-c", str(invalid_yaml)],
            capture_output=True,
            text=True
        )

        assert result.returncode != 0
        assert "Error" in result.stderr or "error" in result.stdout.lower()


class TestCLIInfo:
    """Test the 'info' subcommand"""

    def test_info_simple_process(self):
        """Test displaying info for simple process"""
        result = subprocess.run(
            [sys.executable, "-m", "event_log_gen.cli", "info",
             "-c", "configs/examples/simple_process.yaml"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "Simple Order Processing" in result.stdout
        assert "Activities" in result.stdout
        assert "order_received" in result.stdout
        assert "payment_validated" in result.stdout

    def test_info_full_config(self):
        """Test displaying info for full config"""
        result = subprocess.run(
            [sys.executable, "-m", "event_log_gen.cli", "info",
             "-c", "configs/process_config.yaml"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "Restaurant Permit" in result.stdout
        assert "Activities" in result.stdout
        assert "Resource Pools" in result.stdout

    def test_info_nonexistent_file(self):
        """Test info command with nonexistent file"""
        result = subprocess.run(
            [sys.executable, "-m", "event_log_gen.cli", "info",
             "-c", "nonexistent.yaml"],
            capture_output=True,
            text=True
        )

        assert result.returncode != 0


class TestCLIHelp:
    """Test help and error messages"""

    def test_help_main(self):
        """Test main help message"""
        result = subprocess.run(
            [sys.executable, "-m", "event_log_gen.cli", "--help"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "event-log-gen" in result.stdout or "Event Log Generator" in result.stdout
        assert "generate" in result.stdout
        assert "validate" in result.stdout
        assert "info" in result.stdout

    def test_help_generate(self):
        """Test generate subcommand help"""
        result = subprocess.run(
            [sys.executable, "-m", "event_log_gen.cli", "generate", "--help"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "--config" in result.stdout or "-c" in result.stdout
        assert "--cases" in result.stdout or "-n" in result.stdout
        assert "--seed" in result.stdout or "-s" in result.stdout
        assert "--format" in result.stdout or "-f" in result.stdout

    def test_help_validate(self):
        """Test validate subcommand help"""
        result = subprocess.run(
            [sys.executable, "-m", "event_log_gen.cli", "validate", "--help"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "--config" in result.stdout or "-c" in result.stdout

    def test_help_info(self):
        """Test info subcommand help"""
        result = subprocess.run(
            [sys.executable, "-m", "event_log_gen.cli", "info", "--help"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "--config" in result.stdout or "-c" in result.stdout

    def test_no_subcommand(self):
        """Test running without subcommand shows help"""
        result = subprocess.run(
            [sys.executable, "-m", "event_log_gen.cli"],
            capture_output=True,
            text=True
        )

        # Should show help or error
        assert result.returncode != 0 or "usage" in result.stdout.lower()


class TestCLIIntegration:
    """Integration tests combining multiple CLI operations"""

    def test_validate_then_generate(self, tmp_path):
        """Test workflow: validate config, then generate logs"""
        # First validate
        validate_result = subprocess.run(
            [sys.executable, "-m", "event_log_gen.cli", "validate",
             "-c", "configs/examples/simple_process.yaml"],
            capture_output=True,
            text=True
        )
        assert validate_result.returncode == 0

        # Then generate
        generate_result = subprocess.run(
            [sys.executable, "-m", "event_log_gen.cli", "generate",
             "-c", "configs/examples/simple_process.yaml",
             "-n", "10",
             "-f", "csv",
             "-o", str(tmp_path / "integrated")],
            capture_output=True,
            text=True
        )
        assert generate_result.returncode == 0
        assert (tmp_path / "integrated" / "events.csv").exists()

    def test_info_then_generate(self, tmp_path):
        """Test workflow: check info, then generate logs"""
        # Check info
        info_result = subprocess.run(
            [sys.executable, "-m", "event_log_gen.cli", "info",
             "-c", "configs/examples/simple_process.yaml"],
            capture_output=True,
            text=True
        )
        assert info_result.returncode == 0

        # Generate based on info
        generate_result = subprocess.run(
            [sys.executable, "-m", "event_log_gen.cli", "generate",
             "-c", "configs/examples/simple_process.yaml",
             "-n", "20",
             "-o", str(tmp_path / "after_info")],
            capture_output=True,
            text=True
        )
        assert generate_result.returncode == 0
