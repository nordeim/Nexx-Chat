"""Tests for header components."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from neural_terminal.components.header import (
    HeaderConfig,
    Header,
    Sidebar,
    render_header,
    render_sidebar,
)


class TestHeaderConfig:
    """Tests for HeaderConfig."""
    
    def test_default_config(self):
        """Default configuration is set."""
        config = HeaderConfig()
        
        assert config.title == "NEURAL TERMINAL"
        assert config.subtitle == "OpenRouter Chat Interface"
        assert config.show_status is True
        assert config.show_theme_selector is True
        assert config.show_model_selector is True
    
    def test_custom_config(self):
        """Can create custom configuration."""
        config = HeaderConfig(
            title="Custom Title",
            show_status=False,
        )
        
        assert config.title == "Custom Title"
        assert config.show_status is False


class TestHeader:
    """Tests for Header component."""
    
    @patch("neural_terminal.components.header.st")
    def test_render_basic(self, mock_st):
        """Renders basic header."""
        header = Header()
        
        header.render()
        
        mock_st.markdown.assert_called()
        args, _ = mock_st.markdown.call_args
        assert "NEURAL TERMINAL" in args[0]
    
    @patch("neural_terminal.components.header.st")
    def test_render_offline_status(self, mock_st):
        """Renders offline status."""
        header = Header()
        
        header.render(is_connected=False)
        
        args, _ = mock_st.markdown.call_args
        assert "OFFLINE" in args[0]
        assert "offline" in args[0]
    
    @patch("neural_terminal.components.header.st")
    def test_render_with_model_selector(self, mock_st):
        """Renders with model selector."""
        mock_cols = [MagicMock(), MagicMock()]
        mock_st.columns.return_value = mock_cols
        # Mock selectbox to return a label that exists in models
        mock_st.selectbox.return_value = "GPT-4"
        
        header = Header(HeaderConfig(show_model_selector=True))
        models = [("gpt-4", "GPT-4"), ("gpt-3.5", "GPT-3.5")]
        
        header.render(available_models=models)
        
        # Should create selectbox for model
        mock_st.selectbox.assert_called()
    
    @patch("neural_terminal.components.header.st")
    def test_render_model_change_callback(self, mock_st):
        """Calls callback on model change."""
        mock_cols = [MagicMock(), MagicMock()]
        mock_st.columns.return_value = mock_cols
        
        callback = Mock()
        header = Header()
        models = [("gpt-4", "GPT-4"), ("gpt-3.5-turbo", "GPT-3.5")]
        
        # Mock selectbox to simulate selection (selecting GPT-4 when gpt-3.5-turbo was selected)
        mock_st.selectbox.return_value = "GPT-4"
        
        header.render(
            available_models=models,
            selected_model="gpt-3.5-turbo",
            on_model_change=callback,
        )
        
        # Callback should be triggered due to model change
        callback.assert_called_once_with("gpt-4")
    
    @patch("neural_terminal.components.header.st")
    def test_render_simple(self, mock_st):
        """Renders simplified header."""
        header = Header()
        
        header.render_simple(title="Simple Title", is_connected=True)
        
        args, _ = mock_st.markdown.call_args
        assert "Simple Title" in args[0]
        assert "ONLINE" in args[0]
    
    @patch("neural_terminal.components.header.st")
    def test_render_simple_uses_config_title(self, mock_st):
        """Simple render uses config title as default."""
        header = Header(HeaderConfig(title="Config Title"))
        
        header.render_simple()
        
        args, _ = mock_st.markdown.call_args
        assert "Config Title" in args[0]


class TestSidebar:
    """Tests for Sidebar component."""
    
    @patch("neural_terminal.components.header.st")
    def test_render_basic(self, mock_st):
        """Renders sidebar."""
        mock_cols = [MagicMock(), MagicMock()]
        mock_st.columns.return_value = mock_cols
        
        sidebar = Sidebar()
        
        sidebar.render()
        
        mock_st.title.assert_called_with("⚡ Neural Terminal")
    
    @patch("neural_terminal.components.header.st")
    def test_render_with_cost(self, mock_st):
        """Renders with cost info."""
        mock_cols = [MagicMock(), MagicMock()]
        mock_st.columns.return_value = mock_cols
        
        sidebar = Sidebar()
        
        sidebar.render(total_cost=1.2345)
        
        mock_st.metric.assert_called()
    
    @patch("neural_terminal.components.header.st")
    def test_render_with_budget(self, mock_st):
        """Renders with budget info."""
        mock_cols = [MagicMock(), MagicMock()]
        mock_st.columns.return_value = mock_cols
        
        sidebar = Sidebar()
        
        sidebar.render(total_cost=5.0, budget_limit=10.0)
        
        mock_st.progress.assert_called()
    
    @patch("neural_terminal.components.header.st")
    def test_render_with_conversation_count(self, mock_st):
        """Renders conversation count."""
        mock_cols = [MagicMock(), MagicMock()]
        mock_st.columns.return_value = mock_cols
        
        sidebar = Sidebar()
        
        sidebar.render(conversation_count=5)
        
        mock_st.write.assert_called()
    
    @patch("neural_terminal.components.header.st")
    def test_render_expander_shortcuts(self, mock_st):
        """Renders keyboard shortcuts expander."""
        mock_cols = [MagicMock(), MagicMock()]
        mock_st.columns.return_value = mock_cols
        
        sidebar = Sidebar()
        
        sidebar.render()
        
        mock_st.expander.assert_any_call("⌨️ Keyboard Shortcuts")
    
    @patch("neural_terminal.components.header.st")
    def test_render_expander_help(self, mock_st):
        """Renders help expander."""
        mock_cols = [MagicMock(), MagicMock()]
        mock_st.columns.return_value = mock_cols
        
        sidebar = Sidebar()
        
        sidebar.render()
        
        mock_st.expander.assert_any_call("📖 Help")


class TestConvenienceFunctions:
    """Tests for convenience functions."""
    
    @patch("neural_terminal.components.header.st")
    def test_render_header(self, mock_st):
        """render_header creates header."""
        render_header("Test Title", is_connected=False)
        
        mock_st.markdown.assert_called()
        args, _ = mock_st.markdown.call_args
        assert "Test Title" in args[0]
    
    @patch("neural_terminal.components.header.st")
    def test_render_sidebar(self, mock_st):
        """render_sidebar creates sidebar."""
        mock_cols = [MagicMock(), MagicMock()]
        mock_st.columns.return_value = mock_cols
        
        render_sidebar(total_cost=1.0, conversation_count=3)
        
        mock_st.title.assert_called()
