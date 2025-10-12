"""
Core generator module

Main orchestration for generating synthetic process event logs.
"""

import random
from datetime import datetime, timedelta, time
from typing import Any, Dict, List

import pandas as pd

from ..config.loader import ConfigDict


class Event:
    """
    Represents a single event in the process log

    Attributes:
        case_id: Unique identifier for the case (trace)
        activity: Activity name
        timestamp: Event timestamp
        resource: Resource that performed the activity (None for automatic)
        lifecycle: Lifecycle state (default: 'complete')
        custom_attributes: Dictionary of custom event attributes
    """

    def __init__(
        self,
        case_id: str,
        activity: str,
        timestamp: datetime,
        resource: str | None = None,
        lifecycle: str = "complete",
        custom_attributes: Dict[str, Any] | None = None,
    ):
        self.case_id = case_id
        self.activity = activity
        self.timestamp = timestamp
        self.resource = resource
        self.lifecycle = lifecycle
        self.custom_attributes = custom_attributes or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary (internal schema)"""
        event_dict = {
            "case_id": self.case_id,
            "activity": self.activity,
            "timestamp": self.timestamp,
            "resource": self.resource,
            "lifecycle": self.lifecycle,
        }
        # Add custom attributes
        event_dict.update(self.custom_attributes)
        return event_dict

    def __repr__(self) -> str:
        return f"Event(case={self.case_id}, activity={self.activity}, timestamp={self.timestamp})"


class GenerationError(Exception):
    """Raised when event generation fails"""

    pass


def generate_log(
    config: ConfigDict,
    seed: int | None = None,
    num_cases: int | None = None,
    return_metadata: bool = False
) -> pd.DataFrame | tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Generate complete event log from configuration

    This is the main entry point for event log generation.

    Args:
        config: Validated configuration dictionary
        seed: Random seed for reproducibility (overrides config if provided)
        num_cases: Number of cases to generate (overrides config if provided)
        return_metadata: If True, return (dataframe, metadata) tuple

    Returns:
        If return_metadata=False: DataFrame with internal schema
        If return_metadata=True: Tuple of (DataFrame, metadata dict)

    Raises:
        GenerationError: If generation fails

    Example:
        >>> from processlog.config import load_config, validate_config
        >>> config = load_config('configs/process_config.yaml')
        >>> result = validate_config(config)
        >>> if result.valid:
        ...     df, metadata = generate_log(config, seed=42, num_cases=100, return_metadata=True)
        ...     print(f"Generated {len(df)} events for {df['case_id'].nunique()} cases")
    """
    # Use config values if not overridden
    if seed is None:
        seed = config.get("seed", 42)
    if num_cases is None:
        num_cases = config.get("num_cases", 100)

    # Track generation start time
    generation_start = datetime.now()

    # Initialize seeded RNG
    rng = random.Random(seed)

    # Parse start date
    start_date_str = config.get("start_date", "2024-01-01")
    start_date = datetime.fromisoformat(start_date_str)

    # Initialize resource tracking (Phase 4)
    resource_tracker = _initialize_resource_tracker(config)

    # Collect all events
    all_events: List[Event] = []

    # Generate each case
    for case_num in range(1, num_cases + 1):
        case_id = f"case_{case_num:04d}"

        # Generate case-level attributes (Phase 4: Custom Attributes)
        case_attributes = _generate_case_attributes(config, rng)

        # Generate events for this case
        try:
            case_events = _generate_case(case_id, config, start_date, rng, resource_tracker, case_attributes)
            all_events.extend(case_events)
        except Exception as e:
            raise GenerationError(f"Failed to generate case '{case_id}': {e}") from e

    # Convert to DataFrame
    df = _events_to_dataframe(all_events)

    # Build metadata if requested
    if return_metadata:
        generation_end = datetime.now()
        metadata = _build_metadata(
            config=config,
            df=df,
            seed=seed,
            num_cases=num_cases,
            generation_start=generation_start,
            generation_end=generation_end,
            resource_tracker=resource_tracker
        )
        return df, metadata

    return df


def _generate_case(
    case_id: str, config: ConfigDict, start_date: datetime, rng: random.Random,
    resource_tracker: Dict[str, Any], case_attributes: Dict[str, Any]
) -> List[Event]:
    """
    Generate events for a single case

    Args:
        case_id: Unique case identifier
        config: Configuration dictionary
        start_date: Starting timestamp for the process
        rng: Random number generator
        resource_tracker: Resource workload tracking dictionary
        case_attributes: Case-level attributes (same for all events in case)

    Returns:
        List of Event objects for this case, chronologically ordered
    """
    events: List[Event] = []

    # Ensure start timestamp is within business hours
    current_timestamp = _advance_to_business_hours(start_date, config)

    # Get activities lookup
    activities = config.get("activities", [])
    activity_map = {act["id"]: act for act in activities}

    # Find start activity (first activity in list)
    if not activities:
        raise GenerationError(f"No activities defined in configuration")

    current_activity_id = activities[0]["id"]

    # Limit iterations to prevent infinite loops
    max_iterations = 1000
    iteration = 0

    # Generate events following the process flow
    while current_activity_id and iteration < max_iterations:
        iteration += 1

        # Get activity definition
        activity_def = activity_map.get(current_activity_id)
        if not activity_def:
            raise GenerationError(f"Activity '{current_activity_id}' not found in configuration")

        # Generate event (with resource allocation and custom attributes)
        event, selected_resource = _create_event(
            case_id, activity_def, current_timestamp, rng, config, resource_tracker, case_attributes
        )
        events.append(event)

        # Calculate duration (with resource performance)
        duration_hours = _calculate_duration(activity_def, selected_resource, rng)
        current_timestamp = current_timestamp + timedelta(hours=duration_hours)

        # Advance to business hours if needed (Phase 4: Calendar)
        current_timestamp = _advance_to_business_hours(current_timestamp, config)

        # Select next activity
        current_activity_id = _select_next_activity(activity_def, rng)

    # Check for infinite loop
    if iteration >= max_iterations:
        raise GenerationError(
            f"Case '{case_id}' exceeded {max_iterations} iterations, possible infinite loop"
        )

    return events


def _create_event(
    case_id: str, activity_def: Dict[str, Any], timestamp: datetime, rng: random.Random,
    config: ConfigDict, resource_tracker: Dict[str, Any], case_attributes: Dict[str, Any]
) -> tuple[Event, Dict[str, Any] | None]:
    """
    Create a single event from activity definition

    Args:
        case_id: Case identifier
        activity_def: Activity definition from config
        timestamp: Event timestamp
        rng: Random number generator
        config: Full configuration dictionary
        resource_tracker: Resource workload tracking
        case_attributes: Case-level attributes to include in event

    Returns:
        Tuple of (Event object, selected resource dict or None)
    """
    activity_id = activity_def["id"]
    activity_type = activity_def.get("type", "automatic")

    # Determine resource (None for automatic activities)
    resource = None
    selected_resource = None

    if activity_type == "human":
        # Phase 4: Capacity-weighted resource allocation
        resource_pool_name = activity_def.get("resource_pool")
        if resource_pool_name:
            selected_resource = _select_resource(resource_pool_name, config, resource_tracker, rng)
            if selected_resource:
                resource = selected_resource["id"]
                # Track workload
                resource_tracker["workload"][resource] = resource_tracker["workload"].get(resource, 0) + 1
            else:
                # Fallback if pool is empty
                resource = f"{resource_pool_name}_placeholder"
        else:
            # No resource pool specified
            resource = "unassigned"

    # Generate event-level attributes (Phase 4: Custom Attributes)
    event_attributes = _generate_event_attributes(activity_type, config, rng)

    # Merge case and event attributes
    custom_attributes = {**case_attributes, **event_attributes}

    # Create event
    event = Event(
        case_id=case_id,
        activity=activity_id,
        timestamp=timestamp,
        resource=resource,
        lifecycle="complete",
        custom_attributes=custom_attributes,
    )

    return event, selected_resource


def _calculate_duration(activity_def: Dict[str, Any], resource: Dict[str, Any] | None, rng: random.Random) -> float:
    """
    Calculate activity duration with resource performance characteristics (Phase 4)

    Pipeline:
    1. Sample base duration from min/max or typical/spread
    2. Apply resource speed multiplier (if resource provided)
    3. Apply resource consistency variance (if resource provided)

    Args:
        activity_def: Activity definition from config
        resource: Selected resource dict (None for automatic activities)
        rng: Random number generator

    Returns:
        Duration in hours
    """
    duration_config = activity_def.get("duration", {})

    # STEP 1: Sample base duration
    # Min/max format (uniform distribution)
    if "min" in duration_config and "max" in duration_config:
        min_hours = duration_config["min"]
        max_hours = duration_config["max"]
        base_duration = rng.uniform(min_hours, max_hours)

    # Typical/spread format (normal distribution)
    elif "typical" in duration_config and "spread" in duration_config:
        typical_hours = duration_config["typical"]
        spread_hours = duration_config["spread"]
        base_duration = rng.gauss(typical_hours, spread_hours)
        base_duration = max(0.1, base_duration)  # Ensure positive

    else:
        # Fallback: 1 hour
        base_duration = 1.0

    # If no resource (automatic activity), return base duration
    if not resource:
        return base_duration

    # STEP 2: Apply resource speed multiplier
    speed = resource.get("speed", 1.0)
    duration = base_duration * speed

    # STEP 3: Apply resource consistency variance
    consistency = resource.get("consistency", 1.0)
    # Formula: duration × (1 + (1 - consistency) × random(-0.5, 0.5))
    # consistency=1.0 → no variance, consistency=0.5 → ±50% variance
    variance_factor = (1 - consistency) * rng.uniform(-0.5, 0.5)
    duration = duration * (1 + variance_factor)

    # Ensure positive duration
    return max(0.1, duration)


def _select_next_activity(activity_def: Dict[str, Any], rng: random.Random) -> str | None:
    """
    Select next activity based on next_steps probabilities

    Args:
        activity_def: Activity definition from config
        rng: Random number generator

    Returns:
        Next activity ID, or None if terminal activity
    """
    next_steps = activity_def.get("next_steps", [])

    if not next_steps:
        return None  # Terminal activity

    # Build cumulative probability distribution
    activities = []
    cumulative_probs = []
    cumulative = 0.0

    for next_step in next_steps:
        activity = next_step.get("activity")
        probability = next_step.get("probability", 0.0)

        activities.append(activity)
        cumulative += probability
        cumulative_probs.append(cumulative)

    # Sample from distribution
    rand_val = rng.random()

    for i, cum_prob in enumerate(cumulative_probs):
        if rand_val <= cum_prob:
            return activities[i]

    # Fallback: last activity (shouldn't happen if probabilities sum to 1.0)
    return activities[-1] if activities else None


def _events_to_dataframe(events: List[Event]) -> pd.DataFrame:
    """
    Convert list of events to pandas DataFrame

    Args:
        events: List of Event objects

    Returns:
        DataFrame with internal schema (case_id, activity, timestamp, resource, lifecycle, ...)
    """
    if not events:
        # Return empty DataFrame with correct schema
        return pd.DataFrame(
            columns=["case_id", "activity", "timestamp", "resource", "lifecycle"]
        )

    # Convert events to dictionaries
    event_dicts = [event.to_dict() for event in events]

    # Create DataFrame
    df = pd.DataFrame(event_dicts)

    # Sort by case_id and timestamp (chronological order)
    df = df.sort_values(by=["case_id", "timestamp"]).reset_index(drop=True)

    return df


# ============================================================================
# Phase 4: Resource Management Functions
# ============================================================================

def _initialize_resource_tracker(config: ConfigDict) -> Dict[str, Any]:
    """
    Initialize resource tracking data structure

    Args:
        config: Configuration dictionary

    Returns:
        Resource tracker dictionary with workload counters
    """
    resource_pools = config.get("resource_pools", {})

    # Build flat list of all resources
    all_resources = []
    for pool_name, resources in resource_pools.items():
        for resource in resources:
            # Add pool name for reference
            resource_copy = resource.copy()
            resource_copy["pool"] = pool_name
            all_resources.append(resource_copy)

    tracker = {
        "resources": all_resources,
        "workload": {},  # resource_id → case count
        "pools": resource_pools,  # pool_name → [resources]
    }

    return tracker


def _select_resource(
    pool_name: str, config: ConfigDict, resource_tracker: Dict[str, Any], rng: random.Random
) -> Dict[str, Any] | None:
    """
    Select a resource from a pool using capacity-weighted selection

    Resources with higher capacity values are more likely to be selected.
    Formula: weight = capacity (no fatigue in Phase 4 Step 1)

    Args:
        pool_name: Resource pool name
        config: Configuration dictionary
        resource_tracker: Resource tracking data
        rng: Random number generator

    Returns:
        Selected resource dict, or None if pool is empty
    """
    # Get pool resources
    pools = resource_tracker["pools"]
    if pool_name not in pools:
        return None

    resources = pools[pool_name]
    if not resources:
        return None

    # Build capacity-weighted distribution
    weights = []
    for resource in resources:
        capacity = resource.get("capacity", 1.0)
        weights.append(capacity)

    # Normalize weights to probabilities
    total_weight = sum(weights)
    if total_weight == 0:
        # Equal probability fallback
        return rng.choice(resources)

    probabilities = [w / total_weight for w in weights]

    # Weighted random selection
    cumulative_probs = []
    cumulative = 0.0
    for prob in probabilities:
        cumulative += prob
        cumulative_probs.append(cumulative)

    rand_val = rng.random()
    for i, cum_prob in enumerate(cumulative_probs):
        if rand_val <= cum_prob:
            return resources[i]

    # Fallback: last resource
    return resources[-1]


# ============================================================================
# Phase 4: Calendar Management Functions
# ============================================================================

def _advance_to_business_hours(timestamp: datetime, config: ConfigDict) -> datetime:
    """
    Advance timestamp to next business hours if outside working calendar

    If working_hours is disabled in config, returns timestamp unchanged.
    Otherwise, advances timestamp to:
    - Next working day if it falls on weekend/holiday
    - Next business day start time if outside working hours

    Args:
        timestamp: Current timestamp to check
        config: Configuration dictionary with working_hours settings

    Returns:
        Adjusted timestamp within business hours

    Example:
        >>> # Friday 6 PM → Monday 9 AM (if weekend not working)
        >>> # Tuesday 7 PM → Wednesday 9 AM (if hours are 9-5)
    """
    working_hours_config = config.get("working_hours", {})

    # If calendar disabled, return timestamp unchanged
    if not working_hours_config.get("enabled", False):
        return timestamp

    # Parse working hours configuration
    working_days = working_hours_config.get("days", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
    start_time_str = working_hours_config.get("start_time", "09:00")
    end_time_str = working_hours_config.get("end_time", "17:00")
    holidays = working_hours_config.get("holidays", [])

    # Convert start/end times to time objects
    start_hour, start_minute = map(int, start_time_str.split(":"))
    end_hour, end_minute = map(int, end_time_str.split(":"))
    start_time = time(start_hour, start_minute)
    end_time = time(end_hour, end_minute)

    # Convert holidays to date objects for comparison
    holiday_dates = []
    for holiday_str in holidays:
        try:
            holiday_date = datetime.fromisoformat(holiday_str).date()
            holiday_dates.append(holiday_date)
        except ValueError:
            pass  # Skip invalid holiday dates

    # Map day names to weekday numbers (Monday=0, Sunday=6)
    day_name_to_num = {
        "Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
        "Friday": 4, "Saturday": 5, "Sunday": 6
    }
    working_day_nums = [day_name_to_num[day] for day in working_days if day in day_name_to_num]

    # Advance timestamp until it falls within business hours
    max_iterations = 365  # Prevent infinite loops (should never need this many)
    iterations = 0

    while iterations < max_iterations:
        iterations += 1

        # Check if current day is a working day
        if timestamp.weekday() not in working_day_nums:
            # Advance to next day at start time
            timestamp = timestamp.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
            timestamp += timedelta(days=1)
            continue

        # Check if current day is a holiday
        if timestamp.date() in holiday_dates:
            # Advance to next day at start time
            timestamp = timestamp.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
            timestamp += timedelta(days=1)
            continue

        # Check if time is before business hours start
        if timestamp.time() < start_time:
            # Advance to start of business hours today
            timestamp = timestamp.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
            break

        # Check if time is after business hours end
        if timestamp.time() >= end_time:
            # Advance to next day at start time
            timestamp = timestamp.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
            timestamp += timedelta(days=1)
            continue

        # Timestamp is within business hours - we're done
        break

    return timestamp


# ============================================================================
# Phase 4: Custom Attributes Functions
# ============================================================================

def _generate_case_attributes(config: ConfigDict, rng: random.Random) -> Dict[str, Any]:
    """
    Generate case-level custom attributes

    Case attributes are the same for all events within a case.

    Args:
        config: Configuration dictionary
        rng: Random number generator

    Returns:
        Dictionary of case-level attributes

    Example:
        >>> # Config has: case_attributes with case:priority = ["low", "normal", "high"]
        >>> attrs = _generate_case_attributes(config, rng)
        >>> attrs  # {'case:priority': 'normal', 'case:applicant_type': 'new_business'}
    """
    case_attrs = {}

    case_attributes_config = config.get("case_attributes", [])
    for attr_def in case_attributes_config:
        attr_name = attr_def.get("name")
        attr_type = attr_def.get("type")

        if attr_type == "string":
            # Categorical attribute with probabilities
            values = attr_def.get("values", [])
            probabilities = attr_def.get("probabilities", [])

            if values and probabilities and len(values) == len(probabilities):
                # Weighted random selection
                cumulative_probs = []
                cumulative = 0.0
                for prob in probabilities:
                    cumulative += prob
                    cumulative_probs.append(cumulative)

                rand_val = rng.random()
                for i, cum_prob in enumerate(cumulative_probs):
                    if rand_val <= cum_prob:
                        case_attrs[attr_name] = values[i]
                        break
                else:
                    # Fallback to last value
                    case_attrs[attr_name] = values[-1]

        # Add other types as needed (int, float, etc.)

    return case_attrs


def _generate_event_attributes(activity_type: str, config: ConfigDict, rng: random.Random) -> Dict[str, Any]:
    """
    Generate event-level custom attributes

    Event attributes vary per event based on activity type and configuration.

    Args:
        activity_type: Activity type (e.g., "human", "automatic")
        config: Configuration dictionary
        rng: Random number generator

    Returns:
        Dictionary of event-level attributes

    Example:
        >>> # Config has: event_attributes with cost:amount (normal distribution)
        >>> attrs = _generate_event_attributes("human", config, rng)
        >>> attrs  # {'cost:amount': 52.3}
    """
    event_attrs = {}

    event_attributes_config = config.get("event_attributes", [])
    for attr_def in event_attributes_config:
        attr_name = attr_def.get("name")
        attr_type = attr_def.get("type")
        apply_to_types = attr_def.get("apply_to_types", [])

        # Skip if attribute doesn't apply to this activity type
        if apply_to_types and activity_type not in apply_to_types:
            # Set to 0 for numeric types, None otherwise
            if attr_type == "float" or attr_type == "int":
                event_attrs[attr_name] = 0.0 if attr_type == "float" else 0
            continue

        # Generate based on type
        if attr_type == "float":
            generation = attr_def.get("generation", {})
            distribution = generation.get("distribution", "normal")

            if distribution == "normal":
                mean = generation.get("mean", 0.0)
                std = generation.get("std", 1.0)
                min_val = generation.get("min", None)
                max_val = generation.get("max", None)

                # Sample from normal distribution
                value = rng.gauss(mean, std)

                # Apply min/max bounds
                if min_val is not None:
                    value = max(min_val, value)
                if max_val is not None:
                    value = min(max_val, value)

                event_attrs[attr_name] = round(value, 2)

        elif attr_type == "int":
            generation = attr_def.get("generation", {})
            min_val = generation.get("min", 0)
            max_val = generation.get("max", 100)
            value = rng.randint(min_val, max_val)
            event_attrs[attr_name] = value

    return event_attrs


# ============================================================================
# Metadata Generation
# ============================================================================

def _build_metadata(
    config: ConfigDict,
    df: pd.DataFrame,
    seed: int,
    num_cases: int,
    generation_start: datetime,
    generation_end: datetime,
    resource_tracker: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Build comprehensive metadata about the generated event log

    Args:
        config: Configuration dictionary
        df: Generated event log dataframe
        seed: Random seed used
        num_cases: Number of cases generated
        generation_start: Generation start timestamp
        generation_end: Generation end timestamp
        resource_tracker: Resource tracking data

    Returns:
        Metadata dictionary

    Example metadata structure:
        {
            "generation": {...},
            "process": {...},
            "statistics": {...},
            "resource_utilization": {...}
        }
    """
    from .. import __version__

    # Generation metadata
    generation_duration = (generation_end - generation_start).total_seconds()

    metadata = {
        "generator_version": __version__,
        "generated_at": generation_end.isoformat(),
        "generation_duration_seconds": round(generation_duration, 2),
        "seed": seed,
        "process_name": config.get("process_name", "Unnamed Process"),
        "num_cases": num_cases,
        "num_events": len(df),
        "start_date": config.get("start_date"),
        "end_date": config.get("end_date"),
        "timezone": config.get("timezone", "UTC"),
    }

    # Statistics
    if not df.empty:
        # Calculate cycle times (first to last event per case)
        case_times = df.groupby('case_id')['timestamp'].agg(['min', 'max'])
        case_times['duration_hours'] = (case_times['max'] - case_times['min']).dt.total_seconds() / 3600

        metadata["statistics"] = {
            "mean_cycle_time_hours": round(case_times['duration_hours'].mean(), 2),
            "median_cycle_time_hours": round(case_times['duration_hours'].median(), 2),
            "min_cycle_time_hours": round(case_times['duration_hours'].min(), 2),
            "max_cycle_time_hours": round(case_times['duration_hours'].max(), 2),
            "std_cycle_time_hours": round(case_times['duration_hours'].std(), 2),
            "mean_events_per_case": round(df.groupby('case_id').size().mean(), 2),
        }

        # Activity distribution
        activity_counts = df['activity'].value_counts().to_dict()
        metadata["activity_distribution"] = activity_counts

        # Resource utilization
        if 'resource' in df.columns:
            resource_counts = df[df['resource'].notna()]['resource'].value_counts().to_dict()
            metadata["resource_utilization"] = resource_counts

    return metadata
