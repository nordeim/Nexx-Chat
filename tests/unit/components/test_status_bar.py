"""Tests for status bar components."""

import pytest
from decimal import Decimal
from unittest.mock import Mock, patch

from neural_terminal.components.status_bar import (
    StatusInfo,
    StatusBar,
    CostDisplay,
    render_status,
    render_budget_warning,
)


class TestStatusInfo:
    """Tests for StatusInfo dataclass."""
    
    def test_default_values(self):
        """Default values are set correctly."""
        status = StatusInfo()
        
        assert status.total_cost == Decimal("0.00")
        assert status.budget_limit is None
        assert status.total_tokens == 0
        assert status.message_count == 0
        assert status.current_model == "unknown"
        assert status.is_streaming is False
        assert status.connection_status == "connected"
    
    def test_custom_values(self):
        """Can set custom values."""
        status = StatusInfo(
            total_cost=Decimal("1.50"),
            budget_limit=Decimal("10.00"),
            total_tokens=1000,
            message_count=50,
            current_model="gpt-4",
            is_streaming=True,
            connection_status="error",
        )
        
        assert status.total_cost == Decimal("1.50")
        assert status.budget_limit == Decimal("10.00")
        assert status.current_model == "gpt-4"


class TestStatusBar:
    """Tests for StatusBar component."""
    
    @patch("neural_terminal.components.status_bar.st")
    def test_render_connected(self, mock_st):
        """Renders connected status."""
        bar = StatusBar()
        status = StatusInfo(connection_status="connected")
        
        bar.render(status)
        
        mock_st.markdown.assert_called_once()
        args, _ = mock_st.markdown.call_args
        assert "CONNECTED" in args[0]
    
    @patch("neural_terminal.components.status_bar.st")
    def test_render_streaming(self, mock_st):
        """Renders streaming status."""
        bar = StatusBar()
        status = StatusInfo(is_streaming=True)
        
        bar.render(status)
        
        args, _ = mock_st.markdown.call_args
        assert "STREAMING" in args[0]
        assert "⚡" in args[0]
    
    @patch("neural_terminal.components.status_bar.st")
    def test_render_disconnected(self, mock_st):
        """Renders disconnected status."""
        bar = StatusBar()
        status = StatusInfo(connection_status="disconnected")
        
        bar.render(status)
        
        args, _ = mock_st.markdown.call_args
        assert "DISCONNECTED" in args[0]
    
    @patch("neural_terminal.components.status_bar.st")
    def test_render_with_cost(self, mock_st):
        """Renders cost information."""
        bar = StatusBar()
        status = StatusInfo(total_cost=Decimal("1.2345"))
        
        bar.render(status)
        
        args, _ = mock_st.markdown.call_args
        assert "$1.2345" in args[0]
    
    @patch("neural_terminal.components.status_bar.st")
    def test_render_with_tokens(self, mock_st):
        """Renders token count."""
        bar = StatusBar()
        status = StatusInfo(total_tokens=1500)
        
        bar.render(status)
        
        args, _ = mock_st.markdown.call_args
        assert "1500 tokens" in args[0]
    
    @patch("neural_terminal.components.status_bar.st")
    def test_render_compact(self, mock_st):
        """Renders compact status."""
        bar = StatusBar()
        status = StatusInfo()
        
        bar.render_compact(status)
        
        mock_st.write.assert_called()
    
    @patch("neural_terminal.components.status_bar.st")
    def test_render_budget_warning_exceeded(self, mock_st):
        """Renders error when budget exceeded."""
        bar = StatusBar()
        status = StatusInfo(
            total_cost=Decimal("15.00"),
            budget_limit=Decimal("10.00"),
        )
        
        bar.render_budget_warning(status)
        
        mock_st.error.assert_called_once()
    
    @patch("neural_terminal.components.status_bar.st")
    def test_render_budget_warning_high(self, mock_st):
        """Renders warning when budget high."""
        bar = StatusBar()
        status = StatusInfo(
            total_cost=Decimal("8.50"),
            budget_limit=Decimal("10.00"),
        )
        
        bar.render_budget_warning(status)
        
        mock_st.warning.assert_called_once()
    
    @patch("neural_terminal.components.status_bar.st")
    def test_render_budget_warning_normal(self, mock_st):
        """No warning when budget normal."""
        bar = StatusBar()
        status = StatusInfo(
            total_cost=Decimal("4.00"),
            budget_limit=Decimal("10.00"),
        )
        
        bar.render_budget_warning(status)
        
        mock_st.error.assert_not_called()
        mock_st.warning.assert_not_called()
    
    @patch("neural_terminal.components.status_bar.st")
    def test_render_budget_warning_no_budget(self, mock_st):
        """No warning when no budget set."""
        bar = StatusBar()
        status = StatusInfo(
            total_cost=Decimal("100.00"),
            budget_limit=None,
        )
        
        bar.render_budget_warning(status)
        
        mock_st.error.assert_not_called()
        mock_st.warning.assert_not_called()


class TestCostDisplay:
    """Tests for CostDisplay component."""
    
    @patch("neural_terminal.components.status_bar.st")
    def test_render_basic(self, mock_st):
        """Renders basic cost display."""
        display = CostDisplay()
        
        display.render(
            current_cost=Decimal("0.0012"),
            session_cost=Decimal("0.0500"),
        )
        
        mock_st.metric.assert_called()
        assert mock_st.metric.call_count == 3
    
    @patch("neural_terminal.components.status_bar.st")
    def test_render_with_budget(self, mock_st):
        """Renders with budget limit."""
        display = CostDisplay()
        
        display.render(
            current_cost=Decimal("0.0012"),
            session_cost=Decimal("5.00"),
            budget_limit=Decimal("10.00"),
        )
        
        mock_st.metric.assert_called()
        mock_st.progress.assert_called()
    
    @patch("neural_terminal.components.status_bar.st")
    def test_render_breakdown(self, mock_st):
        """Renders cost breakdown."""
        display = CostDisplay()
        
        costs = {
            "gpt-4": Decimal("5.00"),
            "gpt-3.5": Decimal("1.00"),
        }
        
        display.render_breakdown(costs)
        
        mock_st.write.assert_called()
    
    @patch("neural_terminal.components.status_bar.st")
    def test_render_breakdown_empty(self, mock_st):
        """Renders empty breakdown message."""
        display = CostDisplay()
        
        display.render_breakdown({})
        
        mock_st.info.assert_called_once()


class TestConvenienceFunctions:
    """Tests for convenience functions."""
    
    @patch("neural_terminal.components.status_bar.st")
    def test_render_status(self, mock_st):
        """render_status creates status bar."""
        render_status(
            total_cost=Decimal("1.00"),
            is_streaming=True,
        )
        
        mock_st.markdown.assert_called_once()
    
    @patch("neural_terminal.components.status_bar.st")
    def test_render_budget_warning(self, mock_st):
        """render_budget_warning creates warning."""
        render_budget_warning(
            total_cost=Decimal("9.00"),
            budget_limit=Decimal("10.00"),
        )
        
        mock_st.warning.assert_called_once()
