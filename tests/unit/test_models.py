"""Unit tests for domain models.

Tests for Phase 0 Defect C-1: TokenUsage.cost property fix.
Converts property to method calculate_cost().
"""
from decimal import Decimal

import pytest

from neural_terminal.domain.models import TokenUsage


class TestTokenUsage:
    """Tests for TokenUsage model."""

    def test_calculate_cost_with_known_values(self):
        """Test cost calculation with known token counts and pricing.
        
        Scenario:
        - 1000 prompt tokens at $0.0015/1K = $0.0015
        - 500 completion tokens at $0.002/1K = $0.001
        - Total expected: $0.0025
        """
        usage = TokenUsage(
            prompt_tokens=1000,
            completion_tokens=500,
            total_tokens=1500
        )
        
        cost = usage.calculate_cost(
            price_per_1k_prompt=Decimal("0.0015"),
            price_per_1k_completion=Decimal("0.002")
        )
        
        assert cost == Decimal("0.0025")
    
    def test_calculate_cost_with_zero_tokens(self):
        """Test cost calculation with zero tokens returns zero."""
        usage = TokenUsage(
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0
        )
        
        cost = usage.calculate_cost(
            price_per_1k_prompt=Decimal("0.0015"),
            price_per_1k_completion=Decimal("0.002")
        )
        
        assert cost == Decimal("0")
    
    def test_calculate_cost_decimal_precision(self):
        """Test that Decimal precision is preserved (no float conversion)."""
        usage = TokenUsage(
            prompt_tokens=1,
            completion_tokens=1,
            total_tokens=2
        )
        
        cost = usage.calculate_cost(
            price_per_1k_prompt=Decimal("0.0001"),
            price_per_1k_completion=Decimal("0.0002")
        )
        
        # Expected: (1/1000)*0.0001 + (1/1000)*0.0002 = 0.0000001 + 0.0000002 = 0.0000003
        assert cost == Decimal("0.0000003")
        # Verify it's a Decimal, not a float
        assert isinstance(cost, Decimal)
    
    def test_calculate_cost_large_token_counts(self):
        """Test cost calculation with large token counts."""
        usage = TokenUsage(
            prompt_tokens=100_000,
            completion_tokens=50_000,
            total_tokens=150_000
        )
        
        cost = usage.calculate_cost(
            price_per_1k_prompt=Decimal("0.0015"),
            price_per_1k_completion=Decimal("0.002")
        )
        
        # Expected: (100000/1000)*0.0015 + (50000/1000)*0.002 = 0.15 + 0.10 = 0.25
        assert cost == Decimal("0.25")
    
    def test_token_usage_is_frozen(self):
        """Test that TokenUsage is immutable (frozen dataclass)."""
        usage = TokenUsage(
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150
        )
        
        # Attempting to modify should raise FrozenInstanceError
        with pytest.raises(Exception):  # dataclasses.FrozenInstanceError
            usage.prompt_tokens = 200
