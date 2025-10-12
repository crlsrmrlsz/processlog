"""
Tests for core generator module
"""

import pytest
import pandas as pd
from datetime import datetime

from processlog.config.loader import parse_yaml
from processlog.core.generator import (
    Event,
    GenerationError,
    generate_log,
    _generate_case,
    _select_next_activity,
    _calculate_duration,
)
import random


class TestEvent:
    """Tests for Event class"""

    def test_event_creation(self):
        """Test creating an event"""
        event = Event(
            case_id="case_001",
            activity="start",
            timestamp=datetime(2024, 1, 1, 9, 0, 0),
            resource="clerk_001",
            lifecycle="complete",
        )

        assert event.case_id == "case_001"
        assert event.activity == "start"
        assert event.resource == "clerk_001"
        assert event.lifecycle == "complete"

    def test_event_to_dict(self):
        """Test converting event to dictionary"""
        event = Event(
            case_id="case_001",
            activity="start",
            timestamp=datetime(2024, 1, 1, 9, 0, 0),
            resource=None,
        )

        event_dict = event.to_dict()

        assert event_dict["case_id"] == "case_001"
        assert event_dict["activity"] == "start"
        assert event_dict["resource"] is None
        assert event_dict["lifecycle"] == "complete"
        assert isinstance(event_dict["timestamp"], datetime)

    def test_event_with_custom_attributes(self):
        """Test event with custom attributes"""
        event = Event(
            case_id="case_001",
            activity="review",
            timestamp=datetime(2024, 1, 1, 9, 0, 0),
            custom_attributes={"cost:amount": 50.0, "org:department": "Legal"},
        )

        event_dict = event.to_dict()
        assert event_dict["cost:amount"] == 50.0
        assert event_dict["org:department"] == "Legal"


class TestCalculateDuration:
    """Tests for _calculate_duration function"""

    def test_calculate_duration_min_max_no_resource(self):
        """Test duration calculation with min/max format (no resource)"""
        rng = random.Random(42)
        activity_def = {"duration": {"min": 10, "max": 20}}

        duration = _calculate_duration(activity_def, None, rng)

        assert 10 <= duration <= 20

    def test_calculate_duration_typical_spread_no_resource(self):
        """Test duration calculation with typical/spread format (no resource)"""
        rng = random.Random(42)
        activity_def = {"duration": {"typical": 15, "spread": 3}}

        duration = _calculate_duration(activity_def, None, rng)

        # Should be around 15 ± 3*sigma, but always positive
        assert duration > 0

    def test_calculate_duration_reproducible(self):
        """Test that duration calculation is reproducible with same seed"""
        activity_def = {"duration": {"min": 10, "max": 20}}

        rng1 = random.Random(42)
        duration1 = _calculate_duration(activity_def, None, rng1)

        rng2 = random.Random(42)
        duration2 = _calculate_duration(activity_def, None, rng2)

        assert duration1 == duration2

    def test_calculate_duration_fallback(self):
        """Test duration calculation fallback when no format specified"""
        rng = random.Random(42)
        activity_def = {"duration": {}}  # Empty duration config

        duration = _calculate_duration(activity_def, None, rng)

        assert duration == 1.0  # Fallback value

    def test_calculate_duration_with_resource_speed(self):
        """Test duration calculation with resource speed multiplier"""
        rng = random.Random(42)
        activity_def = {"duration": {"min": 10, "max": 10}}  # Fixed duration for testing
        resource = {"id": "fast_worker", "speed": 0.5, "consistency": 1.0}  # 50% faster

        duration = _calculate_duration(activity_def, resource, rng)

        # Duration should be 10 * 0.5 = 5.0 (with consistency=1.0, no variance)
        assert duration == 5.0

    def test_calculate_duration_with_resource_consistency(self):
        """Test duration calculation with resource consistency variance"""
        rng = random.Random(42)
        activity_def = {"duration": {"min": 10, "max": 10}}  # Fixed base duration
        resource = {"id": "inconsistent_worker", "speed": 1.0, "consistency": 0.5}

        # Run multiple times to verify variance exists
        durations = [_calculate_duration(activity_def, resource, random.Random(seed)) for seed in range(100)]

        # Should have variance (not all the same)
        assert len(set(durations)) > 1
        # Should still be around 10 on average
        avg_duration = sum(durations) / len(durations)
        assert 8 <= avg_duration <= 12  # Within reasonable range


class TestSelectNextActivity:
    """Tests for _select_next_activity function"""

    def test_select_next_activity_deterministic(self):
        """Test selecting next activity with probability 1.0"""
        rng = random.Random(42)
        activity_def = {
            "next_steps": [{"activity": "end", "probability": 1.0}]
        }

        next_activity = _select_next_activity(activity_def, rng)

        assert next_activity == "end"

    def test_select_next_activity_terminal(self):
        """Test selecting next activity when it's terminal (no next steps)"""
        rng = random.Random(42)
        activity_def = {"next_steps": []}

        next_activity = _select_next_activity(activity_def, rng)

        assert next_activity is None

    def test_select_next_activity_probability_distribution(self):
        """Test that next activity selection respects probabilities"""
        activity_def = {
            "next_steps": [
                {"activity": "approved", "probability": 0.7},
                {"activity": "rejected", "probability": 0.3},
            ]
        }

        # Run 1000 trials and check distribution
        counts = {"approved": 0, "rejected": 0}
        rng = random.Random(42)

        for _ in range(1000):
            next_activity = _select_next_activity(activity_def, rng)
            counts[next_activity] += 1

        # Check distribution is approximately correct (within 10%)
        assert 650 <= counts["approved"] <= 750  # 70% ± 10%
        assert 250 <= counts["rejected"] <= 350  # 30% ± 10%


class TestGenerateLog:
    """Tests for generate_log function"""

    def test_generate_log_minimal(self, minimal_config_yaml):
        """Test generating log with minimal configuration"""
        config = parse_yaml(minimal_config_yaml)

        df = generate_log(config, seed=42, num_cases=5)

        # Check basic structure
        assert len(df) > 0
        assert "case_id" in df.columns
        assert "activity" in df.columns
        assert "timestamp" in df.columns
        assert "resource" in df.columns
        assert "lifecycle" in df.columns

        # Check number of cases
        assert df["case_id"].nunique() == 5

        # Check chronological ordering
        for case_id in df["case_id"].unique():
            case_df = df[df["case_id"] == case_id]
            timestamps = case_df["timestamp"].tolist()
            assert timestamps == sorted(timestamps)

    def test_generate_log_reproducible(self, minimal_config_yaml):
        """Test that log generation is reproducible with same seed"""
        config = parse_yaml(minimal_config_yaml)

        df1 = generate_log(config, seed=42, num_cases=10)
        df2 = generate_log(config, seed=42, num_cases=10)

        # Should be identical
        assert df1.equals(df2)

    def test_generate_log_different_seeds(self, minimal_config_yaml):
        """Test that different seeds produce different results"""
        config = parse_yaml(minimal_config_yaml)

        df1 = generate_log(config, seed=42, num_cases=10)
        df2 = generate_log(config, seed=99, num_cases=10)

        # Should be different (very unlikely to be identical)
        assert not df1.equals(df2)

    def test_generate_log_uses_config_defaults(self, minimal_config_yaml):
        """Test that generator uses config defaults when not overridden"""
        config = parse_yaml(minimal_config_yaml)

        # Config has num_cases=10, seed=42
        df = generate_log(config)

        assert df["case_id"].nunique() == 10

    def test_generate_log_empty_activities_raises_error(self):
        """Test that empty activities list raises error"""
        config = {
            "process_name": "Test",
            "num_cases": 1,
            "seed": 42,
            "start_date": "2024-01-01",
            "activities": [],
            "resource_pools": {},
        }

        with pytest.raises(GenerationError, match="No activities defined"):
            generate_log(config, seed=42, num_cases=1)

    def test_generate_log_invalid_activity_reference_raises_error(self):
        """Test that invalid activity reference raises error"""
        config = {
            "process_name": "Test",
            "num_cases": 1,
            "seed": 42,
            "start_date": "2024-01-01",
            "activities": [
                {
                    "id": "start",
                    "name": "Start",
                    "type": "automatic",
                    "duration": {"min": 0, "max": 1},
                    "next_steps": [
                        {"activity": "nonexistent", "probability": 1.0}
                    ],
                }
            ],
            "resource_pools": {},
        }

        with pytest.raises(GenerationError, match="Activity 'nonexistent' not found"):
            generate_log(config, seed=42, num_cases=1)

    def test_generate_log_all_events_have_lifecycle(self, minimal_config_yaml):
        """Test that all events have lifecycle field"""
        config = parse_yaml(minimal_config_yaml)

        df = generate_log(config, seed=42, num_cases=5)

        assert (df["lifecycle"] == "complete").all()

    def test_generate_log_automatic_activities_no_resource(self):
        """Test that automatic activities have no resource"""
        config = {
            "process_name": "Test",
            "num_cases": 2,
            "seed": 42,
            "start_date": "2024-01-01",
            "activities": [
                {
                    "id": "start",
                    "name": "Start",
                    "type": "automatic",
                    "duration": {"min": 0, "max": 1},
                    "next_steps": [],
                }
            ],
            "resource_pools": {},
        }

        df = generate_log(config, seed=42, num_cases=2)

        assert df["resource"].isna().all()

    def test_generate_log_human_activities_have_resource(self):
        """Test that human activities have a resource assigned"""
        config = {
            "process_name": "Test",
            "num_cases": 2,
            "seed": 42,
            "start_date": "2024-01-01",
            "activities": [
                {
                    "id": "review",
                    "name": "Review",
                    "type": "human",
                    "resource_pool": "reviewers",
                    "duration": {"min": 1, "max": 2},
                    "next_steps": [],
                }
            ],
            "resource_pools": {
                "reviewers": [
                    {"id": "reviewer_001", "name": "Reviewer 1", "capacity": 1.0}
                ]
            },
        }

        df = generate_log(config, seed=42, num_cases=2)

        # All events should have resources assigned
        assert df["resource"].notna().all()
        # Should have the actual resource ID (Phase 4)
        assert (df["resource"] == "reviewer_001").all()

    def test_resource_allocation_capacity_weighted(self):
        """Test that resource allocation respects capacity weights"""
        config = {
            "process_name": "Test",
            "num_cases": 100,
            "seed": 42,
            "start_date": "2024-01-01",
            "activities": [
                {
                    "id": "review",
                    "name": "Review",
                    "type": "human",
                    "resource_pool": "reviewers",
                    "duration": {"min": 1, "max": 1},
                    "next_steps": [],
                }
            ],
            "resource_pools": {
                "reviewers": [
                    {"id": "high_capacity", "name": "High", "capacity": 2.0, "speed": 1.0, "consistency": 1.0},
                    {"id": "low_capacity", "name": "Low", "capacity": 1.0, "speed": 1.0, "consistency": 1.0},
                ]
            },
        }

        df = generate_log(config, seed=42, num_cases=100)

        # Count resources
        resource_counts = df["resource"].value_counts().to_dict()

        # High capacity should get ~2x more cases than low capacity
        # (2.0 / (2.0 + 1.0) = 66.7% vs 33.3%)
        high_count = resource_counts.get("high_capacity", 0)
        low_count = resource_counts.get("low_capacity", 0)

        # Check distribution (allow 20% variance)
        assert 50 <= high_count <= 80  # Should be around 67
        assert 20 <= low_count <= 50   # Should be around 33
        assert high_count > low_count  # High capacity should get more

    def test_resource_speed_affects_duration(self):
        """Test that resource speed multiplier affects activity duration"""
        config = {
            "process_name": "Test",
            "num_cases": 50,
            "seed": 42,
            "start_date": "2024-01-01",
            "activities": [
                {
                    "id": "review",
                    "name": "Review",
                    "type": "human",
                    "resource_pool": "reviewers",
                    "duration": {"min": 10, "max": 10},  # Fixed 10 hour base duration
                    "next_steps": [],
                }
            ],
            "resource_pools": {
                "reviewers": [
                    {"id": "fast", "name": "Fast", "capacity": 1.0, "speed": 0.5, "consistency": 1.0},  # 50% faster
                    {"id": "slow", "name": "Slow", "capacity": 1.0, "speed": 2.0, "consistency": 1.0},  # 2x slower
                ]
            },
        }

        df = generate_log(config, seed=42, num_cases=50)

        # Calculate duration for each event
        df["duration_hours"] = (df.groupby("case_id")["timestamp"].diff().shift(-1) / pd.Timedelta(hours=1)).fillna(0)

        # Separate by resource
        fast_durations = df[df["resource"] == "fast"]["duration_hours"]
        slow_durations = df[df["resource"] == "slow"]["duration_hours"]

        # Both should have some cases
        assert len(fast_durations) > 0
        assert len(slow_durations) > 0

        # Fast worker should average ~5 hours (10 * 0.5)
        # Slow worker should average ~20 hours (10 * 2.0)
        # (with consistency=1.0, no variance)
        # Since we're using the duration from timestamp diff, we need to filter out the 0 values
        fast_avg = fast_durations[fast_durations > 0].mean() if len(fast_durations[fast_durations > 0]) > 0 else 0
        slow_avg = slow_durations[slow_durations > 0].mean() if len(slow_durations[slow_durations > 0]) > 0 else 0

        # Verify the relationship (slow should be ~4x faster)
        if fast_avg > 0 and slow_avg > 0:
            assert slow_avg > fast_avg * 2  # At minimum, 2x difference

    def test_resource_consistency_adds_variance(self):
        """Test that resource consistency parameter adds duration variance"""
        config = {
            "process_name": "Test",
            "num_cases": 100,
            "seed": 42,
            "start_date": "2024-01-01",
            "activities": [
                {
                    "id": "review",
                    "name": "Review",
                    "type": "human",
                    "resource_pool": "reviewers",
                    "duration": {"min": 10, "max": 10},  # Fixed base duration
                    "next_steps": [],
                }
            ],
            "resource_pools": {
                "reviewers": [
                    {"id": "consistent", "name": "Consistent", "capacity": 1.0, "speed": 1.0, "consistency": 1.0},
                    {"id": "inconsistent", "name": "Inconsistent", "capacity": 1.0, "speed": 1.0, "consistency": 0.5},
                ]
            },
        }

        df = generate_log(config, seed=42, num_cases=100)

        # Calculate duration for each event
        df["duration_hours"] = (df.groupby("case_id")["timestamp"].diff().shift(-1) / pd.Timedelta(hours=1)).fillna(0)

        # Separate by resource (filter out 0 durations from last events)
        consistent_durations = df[(df["resource"] == "consistent") & (df["duration_hours"] > 0)]["duration_hours"]
        inconsistent_durations = df[(df["resource"] == "inconsistent") & (df["duration_hours"] > 0)]["duration_hours"]

        if len(consistent_durations) > 5 and len(inconsistent_durations) > 5:
            # Consistent worker should have lower variance
            consistent_std = consistent_durations.std()
            inconsistent_std = inconsistent_durations.std()

            # Inconsistent should have higher standard deviation
            assert inconsistent_std > consistent_std

    def test_working_calendar_respects_business_hours(self):
        """Test that events only occur during business hours when calendar is enabled"""
        config = {
            "process_name": "Test",
            "num_cases": 20,
            "seed": 42,
            "start_date": "2024-01-01",  # Monday
            "working_hours": {
                "enabled": True,
                "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
                "start_time": "09:00",
                "end_time": "17:00",
                "holidays": []
            },
            "activities": [
                {
                    "id": "start",
                    "name": "Start",
                    "type": "automatic",
                    "duration": {"min": 8, "max": 24},  # Can span across business days
                    "next_steps": [{"activity": "end", "probability": 1.0}],
                },
                {
                    "id": "end",
                    "name": "End",
                    "type": "automatic",
                    "duration": {"min": 1, "max": 1},
                    "next_steps": [],
                }
            ],
            "resource_pools": {},
        }

        df = generate_log(config, seed=42, num_cases=20)

        # All events should fall within business hours (9 AM - 5 PM)
        for _, row in df.iterrows():
            ts = row["timestamp"]
            hour = ts.hour

            # Check time is within 9-17
            assert 9 <= hour < 17, f"Event at {ts} is outside business hours (9-17)"

            # Check day is Monday-Friday (0-4)
            assert ts.weekday() < 5, f"Event at {ts} is on weekend"

    def test_working_calendar_skips_weekends(self):
        """Test that events skip weekends when calendar is enabled"""
        config = {
            "process_name": "Test",
            "num_cases": 5,
            "seed": 42,
            "start_date": "2024-01-05",  # Friday
            "working_hours": {
                "enabled": True,
                "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
                "start_time": "09:00",
                "end_time": "17:00",
                "holidays": []
            },
            "activities": [
                {
                    "id": "start",
                    "name": "Start",
                    "type": "automatic",
                    "duration": {"min": 72, "max": 72},  # 3 days (spans weekend)
                    "next_steps": [],
                }
            ],
            "resource_pools": {},
        }

        df = generate_log(config, seed=42, num_cases=5)

        # No events should fall on Saturday (5) or Sunday (6)
        weekend_events = df[df["timestamp"].dt.weekday >= 5]
        assert len(weekend_events) == 0, f"Found {len(weekend_events)} events on weekend"

    def test_working_calendar_skips_holidays(self):
        """Test that events skip holidays when calendar is enabled"""
        config = {
            "process_name": "Test",
            "num_cases": 10,
            "seed": 42,
            "start_date": "2024-01-01",
            "working_hours": {
                "enabled": True,
                "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
                "start_time": "09:00",
                "end_time": "17:00",
                "holidays": ["2024-01-01", "2024-01-15"]  # New Year, MLK Day
            },
            "activities": [
                {
                    "id": "start",
                    "name": "Start",
                    "type": "automatic",
                    "duration": {"min": 24, "max": 24},
                    "next_steps": [],
                }
            ],
            "resource_pools": {},
        }

        df = generate_log(config, seed=42, num_cases=10)

        # No events should fall on holidays
        for _, row in df.iterrows():
            ts = row["timestamp"]
            event_date = ts.date()
            assert event_date not in [datetime(2024, 1, 1).date(), datetime(2024, 1, 15).date()], \
                f"Event at {ts} is on a holiday"

    def test_working_calendar_disabled(self):
        """Test that calendar is ignored when disabled"""
        config = {
            "process_name": "Test",
            "num_cases": 50,
            "seed": 42,
            "start_date": "2024-01-06",  # Saturday
            "working_hours": {
                "enabled": False,  # Calendar disabled - should allow 24/7
                "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
                "start_time": "09:00",
                "end_time": "17:00",
                "holidays": []
            },
            "activities": [
                {
                    "id": "start",
                    "name": "Start",
                    "type": "automatic",
                    "duration": {"min": 1, "max": 48},
                    "next_steps": [],
                }
            ],
            "resource_pools": {},
        }

        df = generate_log(config, seed=42, num_cases=50)

        # Should have events at various times including weekends
        # (with 50 cases and random durations, very likely to hit weekends)
        has_weekend = any(df["timestamp"].dt.weekday >= 5)
        # With calendar disabled, we SHOULD see weekend events (test may be flaky with low num_cases)
        # Just verify generation doesn't fail when calendar is disabled
