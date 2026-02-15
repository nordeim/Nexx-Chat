"""Tests for CSS generation and injection."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from neural_terminal.components.styles import (
    generate_base_css,
    generate_terminal_effects_css,
    generate_message_css,
    generate_header_css,
    generate_input_css,
    generate_status_bar_css,
    generate_all_css,
    inject_css,
    switch_theme,
    StyleManager,
)
from neural_terminal.components.themes import ThemeRegistry, DEFAULT_THEME


class TestGenerateBaseCSS:
    """Tests for generate_base_css."""
    
    def test_generates_css_variables(self):
        """CSS includes custom properties."""
        css = generate_base_css(DEFAULT_THEME)
        
        assert "--nt-bg-primary" in css
        assert "--nt-accent-primary" in css
        assert "--nt-font-mono" in css
    
    def test_includes_base_styles(self):
        """CSS includes base Streamlit overrides."""
        css = generate_base_css(DEFAULT_THEME)
        
        assert ".stApp" in css
        assert ".main .block-container" in css
        assert "background-color" in css
    
    def test_includes_button_styles(self):
        """CSS includes button styling."""
        css = generate_base_css(DEFAULT_THEME)
        
        assert ".stButton > button" in css
        assert "text-transform: uppercase" in css
    
    def test_includes_typography_styles(self):
        """CSS includes typography overrides."""
        css = generate_base_css(DEFAULT_THEME)
        
        assert "font-family: var(--nt-font-mono)" in css
        assert "h1" in css
    
    def test_applies_theme_colors(self):
        """CSS uses theme colors."""
        theme = ThemeRegistry.TERMINAL_GREEN
        css = generate_base_css(theme)
        
        # Should reference CSS variables that were set from theme
        assert "var(--nt-bg-primary)" in css
        assert "var(--nt-accent-primary)" in css


class TestGenerateTerminalEffectsCSS:
    """Tests for generate_terminal_effects_css."""
    
    def test_includes_glow_effects(self):
        """CSS includes glow effects."""
        css = generate_terminal_effects_css(DEFAULT_THEME)
        
        assert ".terminal-glow" in css
        assert "text-shadow" in css
    
    def test_includes_cursor_blink(self):
        """CSS includes cursor blink animation."""
        theme = ThemeRegistry.TERMINAL_GREEN
        css = generate_terminal_effects_css(theme)
        
        assert "@keyframes blink" in css
        assert ".terminal-cursor" in css
        assert "animation: blink" in css
    
    def test_no_cursor_when_disabled(self):
        """No cursor blink when disabled in theme."""
        theme = ThemeRegistry.MINIMAL_DARK  # cursor_blink=False
        css = generate_terminal_effects_css(theme)
        
        assert ".terminal-cursor" not in css
    
    def test_includes_scanlines(self):
        """CSS includes scanline effect."""
        theme = ThemeRegistry.TERMINAL_GREEN
        css = generate_terminal_effects_css(theme)
        
        assert ".terminal-scanlines" in css
        assert "repeating-linear-gradient" in css
    
    def test_no_scanlines_when_disabled(self):
        """No scanlines when opacity is 0."""
        theme = ThemeRegistry.MINIMAL_DARK  # scanline_opacity=0
        css = generate_terminal_effects_css(theme)
        
        assert ".terminal-scanlines" not in css


class TestGenerateMessageCSS:
    """Tests for generate_message_css."""
    
    def test_includes_message_container(self):
        """CSS includes message container."""
        css = generate_message_css(DEFAULT_THEME)
        
        assert ".nt-message-container" in css
    
    def test_includes_user_message(self):
        """CSS includes user message styling."""
        css = generate_message_css(DEFAULT_THEME)
        
        assert ".nt-message-user" in css
        assert ">>>" in css  # User prompt indicator
    
    def test_includes_assistant_message(self):
        """CSS includes assistant message styling."""
        css = generate_message_css(DEFAULT_THEME)
        
        assert ".nt-message-assistant" in css
        assert "█" in css  # Assistant indicator
    
    def test_includes_system_message(self):
        """CSS includes system message styling."""
        css = generate_message_css(DEFAULT_THEME)
        
        assert ".nt-message-system" in css
    
    def test_includes_error_message(self):
        """CSS includes error message styling."""
        css = generate_message_css(DEFAULT_THEME)
        
        assert ".nt-message-error" in css
        assert "[ERROR]" in css
    
    def test_includes_metadata_styles(self):
        """CSS includes message metadata styling."""
        css = generate_message_css(DEFAULT_THEME)
        
        assert ".nt-message-meta" in css
        assert ".nt-message-cost" in css
        assert ".nt-message-tokens" in css


class TestGenerateHeaderCSS:
    """Tests for generate_header_css."""
    
    def test_includes_header_container(self):
        """CSS includes header container."""
        css = generate_header_css(DEFAULT_THEME)
        
        assert ".nt-header" in css
    
    def test_includes_title_styles(self):
        """CSS includes title styling."""
        css = generate_header_css(DEFAULT_THEME)
        
        assert ".nt-header-title" in css
        assert "text-shadow" in css
    
    def test_includes_status_indicator(self):
        """CSS includes status indicator."""
        css = generate_header_css(DEFAULT_THEME)
        
        assert ".nt-status-indicator" in css
        assert "border-radius: 50%" in css


class TestGenerateInputCSS:
    """Tests for generate_input_css."""
    
    def test_includes_input_container(self):
        """CSS includes input container."""
        css = generate_input_css(DEFAULT_THEME)
        
        assert ".nt-input-container" in css
    
    def test_includes_prompt_styles(self):
        """CSS includes prompt styling."""
        css = generate_input_css(DEFAULT_THEME)
        
        assert ".nt-input-prompt" in css
    
    def test_includes_hint_styles(self):
        """CSS includes hint styling."""
        css = generate_input_css(DEFAULT_THEME)
        
        assert ".nt-input-hint" in css
        assert "kbd" in css


class TestGenerateStatusBarCSS:
    """Tests for generate_status_bar_css."""
    
    def test_includes_status_bar(self):
        """CSS includes status bar."""
        css = generate_status_bar_css(DEFAULT_THEME)
        
        assert ".nt-status-bar" in css
    
    def test_includes_budget_bar(self):
        """CSS includes budget progress bar."""
        css = generate_status_bar_css(DEFAULT_THEME)
        
        assert ".nt-budget-bar" in css
        assert ".nt-budget-fill" in css
    
    def test_includes_status_states(self):
        """CSS includes status state classes."""
        css = generate_status_bar_css(DEFAULT_THEME)
        
        assert ".warning" in css
        assert ".error" in css


class TestGenerateAllCSS:
    """Tests for generate_all_css."""
    
    def test_combines_all_css(self):
        """Generates combined CSS from all parts."""
        css = generate_all_css(DEFAULT_THEME)
        
        assert ".stApp" in css  # Base
        assert ".terminal-glow" in css  # Effects
        assert ".nt-message" in css  # Messages
        assert ".nt-header" in css  # Header
        assert ".nt-input-container" in css  # Input
        assert ".nt-status-bar" in css  # Status
    
    def test_uses_default_theme(self):
        """Uses default theme when none specified."""
        css1 = generate_all_css()
        css2 = generate_all_css(DEFAULT_THEME)
        
        assert css1 == css2


class TestInjectCSS:
    """Tests for inject_css."""
    
    @patch("neural_terminal.components.styles.st")
    def test_injects_css_once(self, mock_st):
        """CSS is only injected once per session."""
        mock_st.session_state = {}
        
        inject_css(DEFAULT_THEME, key="test_css")
        inject_css(DEFAULT_THEME, key="test_css")  # Second call
        
        # Should only be called once
        assert mock_st.markdown.call_count == 1
    
    @patch("neural_terminal.components.styles.st")
    def test_uses_unsafe_allow_html(self, mock_st):
        """Uses unsafe_allow_html for CSS injection."""
        mock_st.session_state = {}
        
        inject_css(DEFAULT_THEME)
        
        mock_st.markdown.assert_called_once()
        _, kwargs = mock_st.markdown.call_args
        assert kwargs.get("unsafe_allow_html") is True
    
    @patch("neural_terminal.components.styles.st")
    def test_generates_css_content(self, mock_st):
        """Generates and injects CSS content."""
        mock_st.session_state = {}
        
        inject_css(DEFAULT_THEME)
        
        args, _ = mock_st.markdown.call_args
        css_content = args[0]
        
        assert "<style>" in css_content
        assert "</style>" in css_content


class TestSwitchTheme:
    """Tests for switch_theme."""
    
    @patch("neural_terminal.components.styles.st")
    def test_switches_theme(self, mock_st):
        """Can switch to different theme."""
        mock_st.session_state = {}
        
        theme = switch_theme("amber")
        
        assert theme == ThemeRegistry.CYBERPUNK_AMBER
    
    @patch("neural_terminal.components.styles.st")
    def test_clears_injection_flags(self, mock_st):
        """Clears injection flags on switch."""
        mock_st.session_state = {
            "_test_injected": True,
            "other_key": "value",
        }
        
        switch_theme("minimal")
        
        assert "_test_injected" not in mock_st.session_state
        assert mock_st.session_state["other_key"] == "value"
    
    @patch("neural_terminal.components.styles.st")
    def test_injects_new_theme(self, mock_st):
        """Injects CSS for new theme."""
        mock_st.session_state = {}
        
        switch_theme("terminal")
        
        mock_st.markdown.assert_called_once()


class TestStyleManager:
    """Tests for StyleManager class."""
    
    def test_initializes_with_default_theme(self):
        """Initializes with default theme."""
        manager = StyleManager()
        
        assert manager.theme == DEFAULT_THEME
    
    def test_initializes_with_custom_theme(self):
        """Initializes with custom theme."""
        theme = ThemeRegistry.CYBERPUNK_AMBER
        manager = StyleManager(theme)
        
        assert manager.theme == theme
    
    @patch("neural_terminal.components.styles.st")
    def test_apply_injects_css(self, mock_st):
        """Apply method injects CSS."""
        mock_st.session_state = {}
        manager = StyleManager()
        
        manager.apply()
        
        mock_st.markdown.assert_called_once()
    
    @patch("neural_terminal.components.styles.st")
    def test_set_theme_changes_theme(self, mock_st):
        """Set theme changes current theme."""
        mock_st.session_state = {}
        manager = StyleManager()
        
        new_theme = manager.set_theme("amber")
        
        assert manager.theme == ThemeRegistry.CYBERPUNK_AMBER
        assert new_theme == ThemeRegistry.CYBERPUNK_AMBER
    
    @patch("neural_terminal.components.styles.st")
    def test_set_theme_injects_css(self, mock_st):
        """Set theme injects new CSS."""
        mock_st.session_state = {}
        manager = StyleManager()
        
        manager.set_theme("minimal")
        
        assert mock_st.markdown.called
