"""
Configuration validator module

Validates YAML configuration for schema compliance and semantic constraints.
"""

from typing import Any, Dict, List, Set, Tuple

from .loader import ConfigDict, ConfigurationError


class ValidationResult:
    """
    Result of configuration validation

    Attributes:
        valid: True if configuration is valid (no errors)
        errors: List of error messages (critical, stop execution)
        warnings: List of warning messages (non-critical, continue execution)
    """

    def __init__(self) -> None:
        self.valid: bool = True
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def add_error(self, message: str) -> None:
        """Add an error message and mark validation as failed"""
        self.valid = False
        self.errors.append(message)

    def add_warning(self, message: str) -> None:
        """Add a warning message (does not fail validation)"""
        self.warnings.append(message)

    def __str__(self) -> str:
        """String representation of validation result"""
        if self.valid:
            msg = "✓ Configuration is valid"
            if self.warnings:
                msg += f" ({len(self.warnings)} warnings)"
            return msg
        else:
            msg = f"✗ Configuration is invalid ({len(self.errors)} errors"
            if self.warnings:
                msg += f", {len(self.warnings)} warnings"
            msg += ")"
            return msg


def validate_config(config: ConfigDict) -> ValidationResult:
    """
    Validate configuration for schema and semantic correctness

    Validation checks:
    1. Required top-level fields exist
    2. Field types are correct
    3. Activities structure is valid
    4. Resources structure is valid
    5. Probabilities sum to 1.0
    6. Duration formats are valid (min/max OR typical/spread)
    7. Activity IDs are unique
    8. Referenced resource pools exist
    9. Custom attribute namespaces are valid

    Args:
        config: Configuration dictionary from loader

    Returns:
        ValidationResult: Validation result with errors/warnings

    Example:
        >>> config = load_config('process_config.yaml')
        >>> result = validate_config(config)
        >>> if not result.valid:
        ...     print("Errors:", result.errors)
        ...     raise ConfigurationError("Invalid configuration")
    """
    result = ValidationResult()

    # 1. Validate required top-level fields
    _validate_required_fields(config, result)

    # 2. Validate field types
    _validate_field_types(config, result)

    # If basic structure is invalid, stop here
    if not result.valid:
        return result

    # 3. Validate activities structure
    _validate_activities(config.get('activities', []), result)

    # 4. Validate resources structure
    _validate_resources(config.get('resource_pools', {}), result)

    # 5. Validate cross-references (activities → resources)
    _validate_cross_references(config, result)

    # 6. Validate anomalies structure (if present)
    if 'anomalies' in config:
        _validate_anomalies(config['anomalies'], result)

    return result


def _validate_required_fields(config: ConfigDict, result: ValidationResult) -> None:
    """Validate that required top-level fields exist"""
    required_fields = [
        'process_name',
        'num_cases',
        'seed',
        'start_date',
        'activities',
        'resource_pools'
    ]

    for field in required_fields:
        if field not in config:
            result.add_error(f"Missing required field: '{field}'")


def _validate_field_types(config: ConfigDict, result: ValidationResult) -> None:
    """Validate that field types are correct"""
    type_checks = {
        'process_name': str,
        'num_cases': int,
        'seed': int,
        'start_date': str,
        'activities': list,
        'resource_pools': dict
    }

    for field, expected_type in type_checks.items():
        if field in config:
            value = config[field]
            if not isinstance(value, expected_type):
                result.add_error(
                    f"Field '{field}' must be {expected_type.__name__}, "
                    f"got {type(value).__name__}"
                )

    # Validate num_cases > 0
    if 'num_cases' in config and isinstance(config['num_cases'], int):
        if config['num_cases'] <= 0:
            result.add_error(f"Field 'num_cases' must be > 0, got {config['num_cases']}")


def _validate_activities(activities: List[Dict[str, Any]], result: ValidationResult) -> None:
    """
    Validate activities structure

    Checks:
    - Each activity has required fields (id, name, type, duration, next_steps)
    - Activity IDs are unique
    - Step numbers are sequential (if present)
    - Duration format is valid (min/max OR typical/spread)
    - Next_steps probabilities sum to 1.0
    - Activity types are valid (human, automatic)
    """
    if not activities:
        result.add_error("Activities list is empty")
        return

    activity_ids: Set[str] = set()
    step_numbers: List[int] = []

    for i, activity in enumerate(activities):
        if not isinstance(activity, dict):
            result.add_error(f"Activity at index {i} must be a dictionary")
            continue

        # Check required fields
        required_fields = ['id', 'name', 'type', 'duration', 'next_steps']
        for field in required_fields:
            if field not in activity:
                result.add_error(f"Activity at index {i} missing required field: '{field}'")

        # Check activity ID uniqueness
        activity_id = activity.get('id')
        if activity_id:
            if activity_id in activity_ids:
                result.add_error(f"Duplicate activity ID: '{activity_id}'")
            activity_ids.add(activity_id)

        # Track step numbers (convert to int if possible)
        if 'step' in activity:
            step_value = activity['step']
            if isinstance(step_value, int):
                step_numbers.append(step_value)
            elif isinstance(step_value, str):
                # Accept string step values (e.g., "5a", "7b" for parallel/variant steps)
                # Only track numeric-only strings for sequence validation
                if step_value.isdigit():
                    step_numbers.append(int(step_value))
                # No warning for non-numeric strings - they're valid for documentation
            else:
                result.add_warning(
                    f"Activity '{activity_id}': step should be an integer or string, got {type(step_value).__name__}"
                )

        # Validate activity type
        activity_type = activity.get('type')
        if activity_type and activity_type not in ['human', 'automatic', 'final']:
            result.add_error(
                f"Activity '{activity_id}': type must be 'human', 'automatic', or 'final', "
                f"got '{activity_type}'"
            )

        # Validate duration format
        duration = activity.get('duration')
        if duration:
            _validate_duration_format(activity_id, duration, result)

        # Validate next_steps
        next_steps = activity.get('next_steps')
        if next_steps:
            _validate_next_steps(activity_id, next_steps, result)

        # Validate resource_pool for human activities
        if activity_type == 'human' and 'resource_pool' not in activity:
            result.add_warning(
                f"Activity '{activity_id}': human activity should have 'resource_pool'"
            )

    # Check step numbers are sequential (if present)
    if step_numbers and len(step_numbers) == len(activities):
        expected_steps = list(range(1, len(activities) + 1))
        if sorted(step_numbers) != expected_steps:
            result.add_warning(
                f"Activity step numbers are not sequential: {sorted(step_numbers)}"
            )


def _validate_duration_format(activity_id: str, duration: Dict[str, Any], result: ValidationResult) -> None:
    """
    Validate duration format

    Must have EITHER (min, max) OR (typical, spread), not both
    """
    if not isinstance(duration, dict):
        result.add_error(f"Activity '{activity_id}': duration must be a dictionary")
        return

    has_min_max = 'min' in duration and 'max' in duration
    has_typical_spread = 'typical' in duration and 'spread' in duration

    if has_min_max and has_typical_spread:
        result.add_error(
            f"Activity '{activity_id}': duration cannot have both min/max and typical/spread. "
            f"Use one format only."
        )
    elif not has_min_max and not has_typical_spread:
        result.add_error(
            f"Activity '{activity_id}': duration must have either (min, max) or (typical, spread)"
        )

    # Validate min < max and min >= 0
    if has_min_max:
        min_val = duration.get('min')
        max_val = duration.get('max')
        if isinstance(min_val, (int, float)) and isinstance(max_val, (int, float)):
            if min_val >= max_val:
                result.add_error(
                    f"Activity '{activity_id}': duration min ({min_val}) must be < max ({max_val})"
                )
            if min_val < 0:
                result.add_error(
                    f"Activity '{activity_id}': duration min ({min_val}) must be >= 0"
                )

    # Validate typical > 0, spread > 0
    if has_typical_spread:
        typical_val = duration.get('typical')
        spread_val = duration.get('spread')
        if isinstance(typical_val, (int, float)) and typical_val <= 0:
            result.add_error(
                f"Activity '{activity_id}': duration typical ({typical_val}) must be > 0"
            )
        if isinstance(spread_val, (int, float)) and spread_val <= 0:
            result.add_error(
                f"Activity '{activity_id}': duration spread ({spread_val}) must be > 0"
            )


def _validate_next_steps(activity_id: str, next_steps: List[Dict[str, Any]], result: ValidationResult) -> None:
    """
    Validate next_steps structure

    Checks:
    - Each next_step has 'activity' and 'probability'
    - Probabilities sum to 1.0 (±0.001 tolerance)
    - Probabilities are between 0 and 1

    Note: Empty next_steps list is valid (terminal activity)
    """
    if not isinstance(next_steps, list):
        result.add_error(f"Activity '{activity_id}': next_steps must be a list")
        return

    # Empty next_steps is valid - this is a terminal activity
    if not next_steps:
        return

    probabilities = []

    for i, next_step in enumerate(next_steps):
        if not isinstance(next_step, dict):
            result.add_error(
                f"Activity '{activity_id}': next_step at index {i} must be a dictionary"
            )
            continue

        # Check required fields
        if 'activity' not in next_step:
            result.add_error(
                f"Activity '{activity_id}': next_step at index {i} missing 'activity'"
            )
        if 'probability' not in next_step:
            result.add_error(
                f"Activity '{activity_id}': next_step at index {i} missing 'probability'"
            )

        # Validate probability value
        prob = next_step.get('probability')
        if prob is not None:
            if not isinstance(prob, (int, float)):
                result.add_error(
                    f"Activity '{activity_id}': next_step probability must be a number, "
                    f"got {type(prob).__name__}"
                )
            elif prob < 0 or prob > 1:
                result.add_error(
                    f"Activity '{activity_id}': next_step probability must be between 0 and 1, "
                    f"got {prob}"
                )
            else:
                probabilities.append(prob)

    # Check probabilities sum to 1.0
    if probabilities:
        total = sum(probabilities)
        if abs(total - 1.0) > 0.001:
            result.add_error(
                f"Activity '{activity_id}': next_steps probabilities sum to {total:.4f}, "
                f"expected 1.0 (±0.001 tolerance)"
            )


def _validate_resources(resource_pools: Dict[str, List[Dict[str, Any]]], result: ValidationResult) -> None:
    """
    Validate resources structure

    Checks:
    - Each resource pool is a list
    - Each resource has required fields (id, name)
    - Resource IDs are unique within pool
    - Performance profiles are valid (speed, consistency, capacity > 0)
    """
    if not resource_pools:
        result.add_error("Resource pools dictionary is empty")
        return

    all_resource_ids: Set[str] = set()

    for pool_name, resources in resource_pools.items():
        if not isinstance(resources, list):
            result.add_error(
                f"Resource pool '{pool_name}' must be a list, got {type(resources).__name__}"
            )
            continue

        if not resources:
            result.add_warning(f"Resource pool '{pool_name}' is empty")
            continue

        for i, resource in enumerate(resources):
            if not isinstance(resource, dict):
                result.add_error(
                    f"Resource pool '{pool_name}': resource at index {i} must be a dictionary"
                )
                continue

            # Check required fields
            if 'id' not in resource:
                result.add_error(
                    f"Resource pool '{pool_name}': resource at index {i} missing 'id'"
                )
            if 'name' not in resource:
                result.add_error(
                    f"Resource pool '{pool_name}': resource at index {i} missing 'name'"
                )

            # Check resource ID uniqueness across all pools
            resource_id = resource.get('id')
            if resource_id:
                if resource_id in all_resource_ids:
                    result.add_error(f"Duplicate resource ID across pools: '{resource_id}'")
                all_resource_ids.add(resource_id)

            # Validate performance profiles (if present)
            for metric in ['speed', 'consistency', 'capacity']:
                if metric in resource:
                    value = resource[metric]
                    if not isinstance(value, (int, float)):
                        result.add_error(
                            f"Resource '{resource_id}': {metric} must be a number, "
                            f"got {type(value).__name__}"
                        )
                    elif value <= 0:
                        result.add_error(
                            f"Resource '{resource_id}': {metric} must be > 0, got {value}"
                        )


def _validate_cross_references(config: ConfigDict, result: ValidationResult) -> None:
    """
    Validate cross-references between sections

    Checks:
    - Activity resource_pool references exist in resource_pools
    - Activity next_steps reference valid activity IDs
    """
    activities = config.get('activities', [])
    resource_pools = config.get('resource_pools', {})

    # Get all valid activity IDs
    activity_ids = {activity.get('id') for activity in activities if 'id' in activity}

    # Get all valid resource pool names
    pool_names = set(resource_pools.keys())

    for activity in activities:
        activity_id = activity.get('id')

        # Check resource_pool references
        if activity.get('type') == 'human':
            resource_pool = activity.get('resource_pool')
            if resource_pool and resource_pool not in pool_names:
                result.add_error(
                    f"Activity '{activity_id}': resource_pool '{resource_pool}' not found in "
                    f"resource_pools. Available pools: {sorted(pool_names)}"
                )

        # Check next_steps activity references
        next_steps = activity.get('next_steps', [])
        for next_step in next_steps:
            next_activity = next_step.get('activity')
            if next_activity and next_activity not in activity_ids:
                result.add_error(
                    f"Activity '{activity_id}': next_step references unknown activity '{next_activity}'. "
                    f"Available activities: {sorted(activity_ids)}"
                )


def _validate_anomalies(anomalies: Dict[str, Any], result: ValidationResult) -> None:
    """
    Validate anomalies structure (optional section)

    Checks:
    - random_delays structure (probability, multiplier_min, multiplier_max)
    - peak_times structure (probability, slowdown_factor)
    """
    if not isinstance(anomalies, dict):
        result.add_error("Anomalies must be a dictionary")
        return

    # Validate random_delays
    if 'random_delays' in anomalies:
        delays = anomalies['random_delays']
        if not isinstance(delays, dict):
            result.add_error("Anomalies random_delays must be a dictionary")
        else:
            # Check probability
            if 'probability' in delays:
                prob = delays['probability']
                if not isinstance(prob, (int, float)) or not (0 <= prob <= 1):
                    result.add_error(
                        f"Anomalies random_delays probability must be between 0 and 1, got {prob}"
                    )

            # Check multipliers
            if 'multiplier_min' in delays and 'multiplier_max' in delays:
                min_mult = delays['multiplier_min']
                max_mult = delays['multiplier_max']
                if isinstance(min_mult, (int, float)) and isinstance(max_mult, (int, float)):
                    if min_mult >= max_mult:
                        result.add_error(
                            f"Anomalies random_delays multiplier_min ({min_mult}) must be < "
                            f"multiplier_max ({max_mult})"
                        )
                    if min_mult < 1.0:
                        result.add_warning(
                            f"Anomalies random_delays multiplier_min ({min_mult}) is < 1.0, "
                            f"delays usually increase duration"
                        )

    # Validate peak_times
    if 'peak_times' in anomalies:
        peaks = anomalies['peak_times']
        if not isinstance(peaks, dict):
            result.add_error("Anomalies peak_times must be a dictionary")
        else:
            # Check probability
            if 'probability' in peaks:
                prob = peaks['probability']
                if not isinstance(prob, (int, float)) or not (0 <= prob <= 1):
                    result.add_error(
                        f"Anomalies peak_times probability must be between 0 and 1, got {prob}"
                    )

            # Check slowdown_factor
            if 'slowdown_factor' in peaks:
                factor = peaks['slowdown_factor']
                if not isinstance(factor, (int, float)):
                    result.add_error(
                        f"Anomalies peak_times slowdown_factor must be a number, got {type(factor).__name__}"
                    )
                elif factor < 1.0:
                    result.add_warning(
                        f"Anomalies peak_times slowdown_factor ({factor}) is < 1.0, "
                        f"peak times usually slow down processes"
                    )
