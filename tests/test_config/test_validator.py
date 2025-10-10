"""
Tests for configuration validator module
"""

import pytest

from event_log_gen.config.loader import parse_yaml
from event_log_gen.config.validator import (
    validate_config,
    ValidationResult,
)


class TestValidationResult:
    """Tests for ValidationResult class"""

    def test_validation_result_starts_valid(self):
        """Test that ValidationResult starts as valid with no errors/warnings"""
        result = ValidationResult()
        assert result.valid is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 0

    def test_add_error_marks_invalid(self):
        """Test that adding an error marks validation as invalid"""
        result = ValidationResult()
        result.add_error("Test error")

        assert result.valid is False
        assert len(result.errors) == 1
        assert result.errors[0] == "Test error"

    def test_add_warning_keeps_valid(self):
        """Test that adding a warning doesn't mark validation as invalid"""
        result = ValidationResult()
        result.add_warning("Test warning")

        assert result.valid is True
        assert len(result.warnings) == 1
        assert result.warnings[0] == "Test warning"

    def test_string_representation_valid(self):
        """Test string representation of valid result"""
        result = ValidationResult()
        assert "valid" in str(result).lower()

    def test_string_representation_invalid(self):
        """Test string representation of invalid result"""
        result = ValidationResult()
        result.add_error("Error 1")
        result.add_error("Error 2")

        string_repr = str(result).lower()
        assert "invalid" in string_repr
        assert "2" in string_repr  # Number of errors


class TestValidateConfig:
    """Tests for validate_config function"""

    def test_validate_valid_config(self, minimal_config_yaml):
        """Test validating a completely valid configuration"""
        config = parse_yaml(minimal_config_yaml)
        result = validate_config(config)

        assert result.valid is True
        assert len(result.errors) == 0

    def test_validate_missing_required_fields(self):
        """Test validation fails when required fields are missing"""
        config = {
            'process_name': 'Test'
            # Missing: num_cases, seed, start_date, activities, resource_pools
        }
        result = validate_config(config)

        assert result.valid is False
        assert any('num_cases' in err for err in result.errors)
        assert any('seed' in err for err in result.errors)
        assert any('start_date' in err for err in result.errors)
        assert any('activities' in err for err in result.errors)
        assert any('resource_pools' in err for err in result.errors)

    def test_validate_wrong_field_types(self):
        """Test validation fails when field types are incorrect"""
        yaml_str = """
        process_name: 123  # Should be string
        num_cases: "ten"  # Should be int
        seed: 42
        start_date: "2024-01-01"
        activities: {}  # Should be list
        resource_pools: []  # Should be dict
        """
        config = parse_yaml(yaml_str)
        result = validate_config(config)

        assert result.valid is False
        assert any('process_name' in err for err in result.errors)
        assert any('num_cases' in err for err in result.errors)
        assert any('activities' in err for err in result.errors)
        assert any('resource_pools' in err for err in result.errors)

    def test_validate_invalid_num_cases(self):
        """Test validation fails when num_cases <= 0"""
        yaml_str = """
        process_name: "Test"
        num_cases: 0
        seed: 42
        start_date: "2024-01-01"
        activities: []
        resource_pools: {}
        """
        config = parse_yaml(yaml_str)
        result = validate_config(config)

        assert result.valid is False
        assert any('num_cases' in err and '> 0' in err for err in result.errors)


class TestValidateActivities:
    """Tests for activity validation"""

    def test_validate_empty_activities(self):
        """Test validation fails when activities list is empty"""
        yaml_str = """
        process_name: "Test"
        num_cases: 10
        seed: 42
        start_date: "2024-01-01"
        activities: []
        resource_pools: {}
        """
        config = parse_yaml(yaml_str)
        result = validate_config(config)

        assert result.valid is False
        assert any('Activities list is empty' in err for err in result.errors)

    def test_validate_duplicate_activity_ids(self):
        """Test validation fails when activity IDs are duplicated"""
        yaml_str = """
        process_name: "Test"
        num_cases: 10
        seed: 42
        start_date: "2024-01-01"
        activities:
          - id: start
            name: "Start 1"
            type: automatic
            duration:
              min: 0
              max: 1
            next_steps:
              - activity: end
                probability: 1.0
          - id: start  # Duplicate!
            name: "Start 2"
            type: automatic
            duration:
              min: 0
              max: 1
            next_steps:
              - activity: end
                probability: 1.0
          - id: end
            name: "End"
            type: automatic
            duration:
              min: 0
              max: 1
            next_steps: []
        resource_pools: {}
        """
        config = parse_yaml(yaml_str)
        result = validate_config(config)

        assert result.valid is False
        assert any('Duplicate activity ID' in err and 'start' in err for err in result.errors)

    def test_validate_invalid_activity_type(self):
        """Test validation fails for invalid activity types"""
        yaml_str = """
        process_name: "Test"
        num_cases: 10
        seed: 42
        start_date: "2024-01-01"
        activities:
          - id: start
            name: "Start"
            type: invalid_type
            duration:
              min: 0
              max: 1
            next_steps: []
        resource_pools: {}
        """
        config = parse_yaml(yaml_str)
        result = validate_config(config)

        assert result.valid is False
        assert any('type must be' in err and 'invalid_type' in err for err in result.errors)


class TestValidateDuration:
    """Tests for duration format validation"""

    def test_validate_both_duration_formats(self, invalid_duration_yaml):
        """Test validation fails when both min/max and typical/spread are present"""
        config = parse_yaml(invalid_duration_yaml)
        result = validate_config(config)

        assert result.valid is False
        assert any('cannot have both min/max and typical/spread' in err for err in result.errors)

    def test_validate_neither_duration_format(self):
        """Test validation fails when neither duration format is present"""
        yaml_str = """
        process_name: "Test"
        num_cases: 10
        seed: 42
        start_date: "2024-01-01"
        activities:
          - id: start
            name: "Start"
            type: automatic
            duration:
              some_other_field: 10
            next_steps: []
        resource_pools: {}
        """
        config = parse_yaml(yaml_str)
        result = validate_config(config)

        assert result.valid is False
        assert any('must have either (min, max) or (typical, spread)' in err for err in result.errors)

    def test_validate_min_greater_than_max(self):
        """Test validation fails when min >= max"""
        yaml_str = """
        process_name: "Test"
        num_cases: 10
        seed: 42
        start_date: "2024-01-01"
        activities:
          - id: start
            name: "Start"
            type: automatic
            duration:
              min: 100
              max: 50
            next_steps: []
        resource_pools: {}
        """
        config = parse_yaml(yaml_str)
        result = validate_config(config)

        assert result.valid is False
        assert any('min' in err and 'must be <' in err and 'max' in err for err in result.errors)

    def test_validate_negative_duration(self):
        """Test validation fails when duration values are < 0"""
        yaml_str = """
        process_name: "Test"
        num_cases: 10
        seed: 42
        start_date: "2024-01-01"
        activities:
          - id: start
            name: "Start"
            type: automatic
            duration:
              min: -10
              max: 20
            next_steps: []
        resource_pools: {}
        """
        config = parse_yaml(yaml_str)
        result = validate_config(config)

        assert result.valid is False
        assert any('min' in err and 'must be >= 0' in err for err in result.errors)


class TestValidateNextSteps:
    """Tests for next_steps validation"""

    def test_validate_probabilities_dont_sum_to_one(self, invalid_probabilities_yaml):
        """Test validation fails when probabilities don't sum to 1.0"""
        config = parse_yaml(invalid_probabilities_yaml)
        result = validate_config(config)

        assert result.valid is False
        assert any('probabilities sum to' in err and 'expected 1.0' in err for err in result.errors)

    def test_validate_probability_out_of_range(self):
        """Test validation fails when probability is not between 0 and 1"""
        yaml_str = """
        process_name: "Test"
        num_cases: 10
        seed: 42
        start_date: "2024-01-01"
        activities:
          - id: start
            name: "Start"
            type: automatic
            duration:
              min: 0
              max: 1
            next_steps:
              - activity: end
                probability: 1.5  # Invalid: > 1
          - id: end
            name: "End"
            type: automatic
            duration:
              min: 0
              max: 1
            next_steps: []
        resource_pools: {}
        """
        config = parse_yaml(yaml_str)
        result = validate_config(config)

        assert result.valid is False
        assert any('probability must be between 0 and 1' in err for err in result.errors)

    def test_validate_empty_next_steps(self):
        """Test validation allows empty next_steps (terminal activity)"""
        yaml_str = """
        process_name: "Test"
        num_cases: 10
        seed: 42
        start_date: "2024-01-01"
        activities:
          - id: start
            name: "Start"
            type: automatic
            duration:
              min: 0
              max: 1
            next_steps: []  # Terminal activity - this is valid
        resource_pools:
          clerks:
            - id: clerk_001
              name: "Clerk 1"
        """
        config = parse_yaml(yaml_str)
        result = validate_config(config)

        # Empty next_steps is valid for terminal activities
        assert result.valid is True


class TestValidateResources:
    """Tests for resource validation"""

    def test_validate_empty_resource_pools(self):
        """Test validation fails when resource_pools is empty"""
        yaml_str = """
        process_name: "Test"
        num_cases: 10
        seed: 42
        start_date: "2024-01-01"
        activities:
          - id: start
            name: "Start"
            type: automatic
            duration:
              min: 0
              max: 1
            next_steps: []
        resource_pools: {}
        """
        config = parse_yaml(yaml_str)
        result = validate_config(config)

        assert result.valid is False
        assert any('Resource pools dictionary is empty' in err for err in result.errors)

    def test_validate_duplicate_resource_ids(self):
        """Test validation fails when resource IDs are duplicated across pools"""
        yaml_str = """
        process_name: "Test"
        num_cases: 10
        seed: 42
        start_date: "2024-01-01"
        activities:
          - id: start
            name: "Start"
            type: automatic
            duration:
              min: 0
              max: 1
            next_steps: []
        resource_pools:
          clerks:
            - id: resource_001
              name: "Clerk 1"
          reviewers:
            - id: resource_001  # Duplicate across pools!
              name: "Reviewer 1"
        """
        config = parse_yaml(yaml_str)
        result = validate_config(config)

        assert result.valid is False
        assert any('Duplicate resource ID' in err and 'resource_001' in err for err in result.errors)

    def test_validate_negative_performance_metrics(self):
        """Test validation fails when performance metrics are <= 0"""
        yaml_str = """
        process_name: "Test"
        num_cases: 10
        seed: 42
        start_date: "2024-01-01"
        activities:
          - id: start
            name: "Start"
            type: automatic
            duration:
              min: 0
              max: 1
            next_steps: []
        resource_pools:
          clerks:
            - id: clerk_001
              name: "Clerk 1"
              speed: -0.5  # Invalid
              consistency: 0.0  # Invalid
        """
        config = parse_yaml(yaml_str)
        result = validate_config(config)

        assert result.valid is False
        assert any('speed' in err and 'must be > 0' in err for err in result.errors)
        assert any('consistency' in err and 'must be > 0' in err for err in result.errors)


class TestValidateCrossReferences:
    """Tests for cross-reference validation"""

    def test_validate_missing_resource_pool_reference(self, missing_resource_pool_yaml):
        """Test validation fails when activity references non-existent resource pool"""
        config = parse_yaml(missing_resource_pool_yaml)
        result = validate_config(config)

        assert result.valid is False
        assert any('resource_pool' in err and 'nonexistent_pool' in err and 'not found' in err for err in result.errors)

    def test_validate_missing_activity_reference(self):
        """Test validation fails when next_step references non-existent activity"""
        yaml_str = """
        process_name: "Test"
        num_cases: 10
        seed: 42
        start_date: "2024-01-01"
        activities:
          - id: start
            name: "Start"
            type: automatic
            duration:
              min: 0
              max: 1
            next_steps:
              - activity: nonexistent_activity
                probability: 1.0
        resource_pools:
          clerks:
            - id: clerk_001
              name: "Clerk 1"
        """
        config = parse_yaml(yaml_str)
        result = validate_config(config)

        assert result.valid is False
        assert any('nonexistent_activity' in err and 'unknown activity' in err for err in result.errors)


class TestValidateAnomalies:
    """Tests for anomalies validation"""

    def test_validate_invalid_delay_probability(self):
        """Test validation fails when delay probability is out of range"""
        yaml_str = """
        process_name: "Test"
        num_cases: 10
        seed: 42
        start_date: "2024-01-01"
        activities:
          - id: start
            name: "Start"
            type: automatic
            duration:
              min: 0
              max: 1
            next_steps: []
        resource_pools:
          clerks:
            - id: clerk_001
              name: "Clerk 1"
        anomalies:
          random_delays:
            probability: 1.5  # Invalid: > 1
            multiplier_min: 2.0
            multiplier_max: 4.0
        """
        config = parse_yaml(yaml_str)
        result = validate_config(config)

        assert result.valid is False
        assert any('random_delays probability' in err and 'between 0 and 1' in err for err in result.errors)

    def test_validate_invalid_delay_multipliers(self):
        """Test validation fails when multiplier_min >= multiplier_max"""
        yaml_str = """
        process_name: "Test"
        num_cases: 10
        seed: 42
        start_date: "2024-01-01"
        activities:
          - id: start
            name: "Start"
            type: automatic
            duration:
              min: 0
              max: 1
            next_steps: []
        resource_pools:
          clerks:
            - id: clerk_001
              name: "Clerk 1"
        anomalies:
          random_delays:
            probability: 0.05
            multiplier_min: 4.0
            multiplier_max: 2.0  # Invalid: < min
        """
        config = parse_yaml(yaml_str)
        result = validate_config(config)

        assert result.valid is False
        assert any('multiplier_min' in err and 'must be <' in err and 'multiplier_max' in err for err in result.errors)
