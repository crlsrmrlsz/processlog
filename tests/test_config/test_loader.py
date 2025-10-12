"""
Tests for configuration loader module
"""

import pytest
from pathlib import Path
import tempfile

from processlog.config.loader import (
    load_config,
    parse_yaml,
    ConfigurationError,
)


class TestLoadConfig:
    """Tests for load_config function"""

    def test_load_valid_config_file(self, minimal_config_yaml):
        """Test loading a valid configuration file"""
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(minimal_config_yaml)
            temp_path = f.name

        try:
            config = load_config(temp_path)

            # Check basic structure
            assert isinstance(config, dict)
            assert config['process_name'] == "Test Process"
            assert config['num_cases'] == 10
            assert config['seed'] == 42
            assert 'activities' in config
            assert 'resource_pools' in config
        finally:
            Path(temp_path).unlink()

    def test_load_nonexistent_file(self):
        """Test loading a non-existent file raises ConfigurationError"""
        with pytest.raises(ConfigurationError, match="Configuration file not found"):
            load_config('/nonexistent/path/config.yaml')

    def test_load_directory_not_file(self, tmp_path):
        """Test loading a directory raises ConfigurationError"""
        with pytest.raises(ConfigurationError, match="Path is not a file"):
            load_config(tmp_path)

    def test_load_invalid_yaml(self):
        """Test loading invalid YAML raises ConfigurationError"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [unclosed")
            temp_path = f.name

        try:
            with pytest.raises(ConfigurationError, match="Failed to parse YAML file"):
                load_config(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_load_empty_file(self):
        """Test loading empty file raises ConfigurationError"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("")
            temp_path = f.name

        try:
            with pytest.raises(ConfigurationError, match="Configuration file is empty"):
                load_config(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_load_non_dict_yaml(self):
        """Test loading YAML that's not a dictionary raises ConfigurationError"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("- item1\n- item2\n- item3")  # YAML list, not dict
            temp_path = f.name

        try:
            with pytest.raises(ConfigurationError, match="Configuration must be a YAML dictionary"):
                load_config(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_load_config_with_path_object(self, minimal_config_yaml):
        """Test loading config using Path object (not string)"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(minimal_config_yaml)
            temp_path = Path(f.name)

        try:
            config = load_config(temp_path)
            assert isinstance(config, dict)
            assert config['process_name'] == "Test Process"
        finally:
            temp_path.unlink()


class TestParseYaml:
    """Tests for parse_yaml function"""

    def test_parse_valid_yaml_string(self, minimal_config_yaml):
        """Test parsing a valid YAML string"""
        config = parse_yaml(minimal_config_yaml)

        assert isinstance(config, dict)
        assert config['process_name'] == "Test Process"
        assert config['num_cases'] == 10
        assert 'activities' in config

    def test_parse_empty_string(self):
        """Test parsing empty string raises ConfigurationError"""
        with pytest.raises(ConfigurationError, match="YAML string is empty"):
            parse_yaml("")

    def test_parse_invalid_yaml_string(self):
        """Test parsing invalid YAML string raises ConfigurationError"""
        with pytest.raises(ConfigurationError, match="Failed to parse YAML string"):
            parse_yaml("invalid: yaml: [unclosed")

    def test_parse_non_dict_yaml_string(self):
        """Test parsing YAML list (not dict) raises ConfigurationError"""
        with pytest.raises(ConfigurationError, match="Configuration must be a YAML dictionary"):
            parse_yaml("- item1\n- item2")

    def test_parse_minimal_yaml(self):
        """Test parsing minimal valid YAML"""
        yaml_str = """
        process_name: "Minimal"
        num_cases: 1
        seed: 1
        start_date: "2024-01-01"
        activities: []
        resource_pools: {}
        """
        config = parse_yaml(yaml_str)

        assert config['process_name'] == "Minimal"
        assert config['num_cases'] == 1
        assert config['activities'] == []
        assert config['resource_pools'] == {}

    def test_parse_yaml_with_comments(self):
        """Test parsing YAML with comments"""
        yaml_str = """
        # This is a comment
        process_name: "Test"  # inline comment
        num_cases: 10
        """
        config = parse_yaml(yaml_str)

        assert config['process_name'] == "Test"
        assert config['num_cases'] == 10

    def test_parse_yaml_preserves_types(self):
        """Test that YAML type parsing works correctly"""
        yaml_str = """
        string_field: "text"
        int_field: 42
        float_field: 3.14
        bool_field: true
        list_field: [1, 2, 3]
        dict_field:
          nested: value
        """
        config = parse_yaml(yaml_str)

        assert isinstance(config['string_field'], str)
        assert isinstance(config['int_field'], int)
        assert isinstance(config['float_field'], float)
        assert isinstance(config['bool_field'], bool)
        assert isinstance(config['list_field'], list)
        assert isinstance(config['dict_field'], dict)
