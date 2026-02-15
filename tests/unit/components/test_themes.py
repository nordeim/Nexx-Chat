"""Tests for theme system."""

import pytest
from neural_terminal.components.themes import (
    ThemeMode,
    ColorPalette,
    Typography,
    Spacing,
    Effects,
    Theme,
    ThemeRegistry,
    DEFAULT_THEME,
)


class TestThemeMode:
    """Tests for ThemeMode enum."""
    
    def test_theme_mode_values(self):
        """ThemeMode has expected values."""
        assert ThemeMode.TERMINAL.name == "TERMINAL"
        assert ThemeMode.DARK.name == "DARK"
        assert ThemeMode.HIGH_CONTRAST.name == "HIGH_CONTRAST"


class TestColorPalette:
    """Tests for ColorPalette dataclass."""
    
    def test_color_palette_creation(self):
        """Can create color palette with all fields."""
        palette = ColorPalette(
            bg_primary="#000000",
            bg_secondary="#111111",
            bg_tertiary="#222222",
            text_primary="#FFFFFF",
            text_secondary="#CCCCCC",
            text_disabled="#666666",
            accent_primary="#00FF00",
            accent_secondary="#FFB000",
            accent_error="#FF0000",
            accent_warning="#FFAA00",
            accent_info="#00AAFF",
            border_subtle="#333333",
            border_strong="#666666",
            cursor="#00FF00",
            selection="rgba(0,255,0,0.3)",
            glow="rgba(0,255,0,0.4)",
        )
        
        assert palette.bg_primary == "#000000"
        assert palette.accent_primary == "#00FF00"
    
    def test_color_palette_immutability(self):
        """ColorPalette is frozen (immutable)."""
        palette = ColorPalette(
            bg_primary="#000000",
            bg_secondary="#111111",
            bg_tertiary="#222222",
            text_primary="#FFFFFF",
            text_secondary="#CCCCCC",
            text_disabled="#666666",
            accent_primary="#00FF00",
            accent_secondary="#FFB000",
            accent_error="#FF0000",
            accent_warning="#FFAA00",
            accent_info="#00AAFF",
            border_subtle="#333333",
            border_strong="#666666",
            cursor="#00FF00",
            selection="rgba(0,255,0,0.3)",
            glow="rgba(0,255,0,0.4)",
        )
        
        with pytest.raises(AttributeError):
            palette.bg_primary = "#FFFFFF"


class TestTypography:
    """Tests for Typography dataclass."""
    
    def test_typography_creation(self):
        """Can create typography configuration."""
        typography = Typography(
            font_mono="JetBrains Mono, monospace",
            font_sans="Inter, sans-serif",
            font_size_xs="0.75rem",
            font_size_sm="0.875rem",
            font_size_base="1rem",
            font_size_md="1.125rem",
            font_size_lg="1.25rem",
            font_size_xl="1.5rem",
            line_height=1.6,
        )
        
        assert typography.font_mono == "JetBrains Mono, monospace"
        assert typography.line_height == 1.6


class TestSpacing:
    """Tests for Spacing dataclass."""
    
    def test_default_spacing(self):
        """Spacing has sensible defaults."""
        spacing = Spacing()
        
        assert spacing.xs == "0.25rem"
        assert spacing.sm == "0.5rem"
        assert spacing.md == "1rem"
        assert spacing.lg == "1.5rem"
        assert spacing.xl == "2rem"
        assert spacing.xxl == "3rem"
    
    def test_custom_spacing(self):
        """Can create custom spacing."""
        spacing = Spacing(xs="2px", md="16px")
        
        assert spacing.xs == "2px"
        assert spacing.md == "16px"
        assert spacing.sm == "0.5rem"  # Default


class TestEffects:
    """Tests for Effects dataclass."""
    
    def test_default_effects(self):
        """Effects has sensible defaults."""
        effects = Effects()
        
        assert effects.glow_intensity == "0 0 10px"
        assert effects.glow_spread == "0 0 20px"
        assert effects.scanline_opacity == 0.03
        assert effects.crt_flicker is True
        assert effects.cursor_blink is True


class TestTheme:
    """Tests for Theme dataclass."""
    
    def test_theme_creation(self):
        """Can create complete theme."""
        palette = ColorPalette(
            bg_primary="#0D1117",
            bg_secondary="#161B22",
            bg_tertiary="#21262D",
            text_primary="#E6EDF3",
            text_secondary="#8B949E",
            text_disabled="#484F58",
            accent_primary="#00FF41",
            accent_secondary="#FFB000",
            accent_error="#FF4136",
            accent_warning="#FF851B",
            accent_info="#00D9FF",
            border_subtle="#30363D",
            border_strong="#8B949E",
            cursor="#00FF41",
            selection="rgba(0,255,65,0.3)",
            glow="rgba(0,255,65,0.4)",
        )
        
        typography = Typography(
            font_mono="JetBrains Mono, monospace",
            font_sans="Inter, sans-serif",
            font_size_xs="0.75rem",
            font_size_sm="0.875rem",
            font_size_base="1rem",
            font_size_md="1.125rem",
            font_size_lg="1.25rem",
            font_size_xl="1.5rem",
            line_height=1.6,
        )
        
        theme = Theme(
            name="Test Theme",
            mode=ThemeMode.TERMINAL,
            colors=palette,
            typography=typography,
        )
        
        assert theme.name == "Test Theme"
        assert theme.mode == ThemeMode.TERMINAL
        assert theme.colors.accent_primary == "#00FF41"
    
    def test_theme_to_css_variables(self):
        """Theme converts to CSS variables."""
        palette = ColorPalette(
            bg_primary="#0D1117",
            bg_secondary="#161B22",
            bg_tertiary="#21262D",
            text_primary="#E6EDF3",
            text_secondary="#8B949E",
            text_disabled="#484F58",
            accent_primary="#00FF41",
            accent_secondary="#FFB000",
            accent_error="#FF4136",
            accent_warning="#FF851B",
            accent_info="#00D9FF",
            border_subtle="#30363D",
            border_strong="#8B949E",
            cursor="#00FF41",
            selection="rgba(0,255,65,0.3)",
            glow="rgba(0,255,65,0.4)",
        )
        
        typography = Typography(
            font_mono="JetBrains Mono, monospace",
            font_sans="Inter, sans-serif",
            font_size_xs="0.75rem",
            font_size_sm="0.875rem",
            font_size_base="1rem",
            font_size_md="1.125rem",
            font_size_lg="1.25rem",
            font_size_xl="1.5rem",
            line_height=1.6,
        )
        
        theme = Theme(
            name="Test Theme",
            mode=ThemeMode.TERMINAL,
            colors=palette,
            typography=typography,
        )
        
        css_vars = theme.to_css_variables()
        
        assert "--nt-bg-primary" in css_vars
        assert css_vars["--nt-bg-primary"] == "#0D1117"
        assert "--nt-accent-primary" in css_vars
        assert css_vars["--nt-accent-primary"] == "#00FF41"
        assert "--nt-font-mono" in css_vars
        assert "--nt-line-height" in css_vars
        assert css_vars["--nt-line-height"] == "1.6"


class TestThemeRegistry:
    """Tests for ThemeRegistry."""
    
    def test_default_themes_exist(self):
        """Registry has default themes."""
        assert ThemeRegistry.TERMINAL_GREEN.name == "Terminal Green"
        assert ThemeRegistry.CYBERPUNK_AMBER.name == "Cyberpunk Amber"
        assert ThemeRegistry.MINIMAL_DARK.name == "Minimal Dark"
    
    def test_terminal_green_colors(self):
        """Terminal Green has correct accent color."""
        theme = ThemeRegistry.TERMINAL_GREEN
        assert theme.colors.accent_primary == "#00FF41"  # Matrix green
        assert theme.mode == ThemeMode.TERMINAL
    
    def test_cyberpunk_amber_colors(self):
        """Cyberpunk Amber has correct accent color."""
        theme = ThemeRegistry.CYBERPUNK_AMBER
        assert theme.colors.accent_primary == "#FFB000"  # Amber
        assert theme.mode == ThemeMode.TERMINAL
    
    def test_minimal_dark_colors(self):
        """Minimal Dark has correct accent color."""
        theme = ThemeRegistry.MINIMAL_DARK
        assert theme.mode == ThemeMode.DARK
    
    def test_get_theme_terminal(self):
        """Can get terminal theme."""
        theme = ThemeRegistry.get_theme("terminal")
        assert theme == ThemeRegistry.TERMINAL_GREEN
        
        theme = ThemeRegistry.get_theme("TERMINAL")
        assert theme == ThemeRegistry.TERMINAL_GREEN
    
    def test_get_theme_amber(self):
        """Can get amber theme."""
        theme = ThemeRegistry.get_theme("amber")
        assert theme == ThemeRegistry.CYBERPUNK_AMBER
        
        theme = ThemeRegistry.get_theme("cyberpunk")
        assert theme == ThemeRegistry.CYBERPUNK_AMBER
    
    def test_get_theme_minimal(self):
        """Can get minimal theme."""
        theme = ThemeRegistry.get_theme("minimal")
        assert theme == ThemeRegistry.MINIMAL_DARK
        
        theme = ThemeRegistry.get_theme("dark")
        assert theme == ThemeRegistry.MINIMAL_DARK
    
    def test_get_theme_case_insensitive(self):
        """Theme lookup is case insensitive."""
        theme1 = ThemeRegistry.get_theme("Terminal")
        theme2 = ThemeRegistry.get_theme("terminal")
        theme3 = ThemeRegistry.get_theme("TERMINAL")
        
        assert theme1 == theme2 == theme3
    
    def test_get_theme_unknown(self):
        """Unknown theme raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            ThemeRegistry.get_theme("nonexistent")
        
        assert "Unknown theme" in str(exc_info.value)
        assert "nonexistent" in str(exc_info.value)
    
    def test_list_themes(self):
        """Can list available themes."""
        themes = ThemeRegistry.list_themes()
        
        assert len(themes) == 3
        
        keys = [k for k, _ in themes]
        assert "terminal" in keys
        assert "amber" in keys
        assert "minimal" in keys


class TestDefaultTheme:
    """Tests for default theme."""
    
    def test_default_is_terminal_green(self):
        """Default theme is Terminal Green."""
        assert DEFAULT_THEME == ThemeRegistry.TERMINAL_GREEN
    
    def test_default_has_required_colors(self):
        """Default theme has all required colors."""
        assert DEFAULT_THEME.colors.bg_primary
        assert DEFAULT_THEME.colors.text_primary
        assert DEFAULT_THEME.colors.accent_primary
    
    def test_default_has_typography(self):
        """Default theme has typography."""
        assert DEFAULT_THEME.typography.font_mono
        assert DEFAULT_THEME.typography.line_height > 0
