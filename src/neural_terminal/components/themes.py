"""Terminal aesthetic theme system for Neural Terminal.

Provides design tokens, color palettes, and typography for the
cyberpunk/terminal-inspired UI aesthetic.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum, auto


class ThemeMode(Enum):
    """Available theme modes."""
    TERMINAL = auto()
    DARK = auto()
    HIGH_CONTRAST = auto()


@dataclass(frozen=True)
class ColorPalette:
    """Color palette for a theme.
    
    All colors specified as hex strings.
    """
    # Backgrounds
    bg_primary: str      # Main background
    bg_secondary: str    # Secondary/surface background
    bg_tertiary: str     # Tertiary/elevated background
    
    # Text
    text_primary: str    # Primary text
    text_secondary: str  # Secondary/muted text
    text_disabled: str   # Disabled text
    
    # Accents
    accent_primary: str   # Main accent (terminal green)
    accent_secondary: str # Secondary accent (amber)
    accent_error: str     # Error/danger (red)
    accent_warning: str   # Warning (yellow/orange)
    accent_info: str      # Info (cyan/blue)
    
    # Borders
    border_subtle: str    # Subtle borders
    border_strong: str    # Strong borders
    
    # Special
    cursor: str           # Cursor color
    selection: str        # Text selection
    glow: str             # Glow effect color


@dataclass(frozen=True)
class Typography:
    """Typography configuration."""
    font_mono: str      # Monospace font stack
    font_sans: str      # Sans-serif fallback
    font_size_xs: str   # Extra small
    font_size_sm: str   # Small
    font_size_base: str # Base size
    font_size_md: str   # Medium
    font_size_lg: str   # Large
    font_size_xl: str   # Extra large
    line_height: float  # Base line height


@dataclass(frozen=True)
class Spacing:
    """Spacing scale."""
    xs: str = "0.25rem"   # 4px
    sm: str = "0.5rem"    # 8px
    md: str = "1rem"      # 16px
    lg: str = "1.5rem"    # 24px
    xl: str = "2rem"      # 32px
    xxl: str = "3rem"     # 48px


@dataclass(frozen=True)
class Effects:
    """Visual effects configuration."""
    glow_intensity: str = "0 0 10px"
    glow_spread: str = "0 0 20px"
    scanline_opacity: float = 0.03
    crt_flicker: bool = True
    cursor_blink: bool = True


@dataclass(frozen=True)
class Theme:
    """Complete theme configuration."""
    name: str
    mode: ThemeMode
    colors: ColorPalette
    typography: Typography
    spacing: Spacing = field(default_factory=Spacing)
    effects: Effects = field(default_factory=Effects)
    
    def to_css_variables(self) -> Dict[str, str]:
        """Convert theme to CSS custom properties."""
        return {
            # Colors - Backgrounds
            "--nt-bg-primary": self.colors.bg_primary,
            "--nt-bg-secondary": self.colors.bg_secondary,
            "--nt-bg-tertiary": self.colors.bg_tertiary,
            
            # Colors - Text
            "--nt-text-primary": self.colors.text_primary,
            "--nt-text-secondary": self.colors.text_secondary,
            "--nt-text-disabled": self.colors.text_disabled,
            
            # Colors - Accents
            "--nt-accent-primary": self.colors.accent_primary,
            "--nt-accent-secondary": self.colors.accent_secondary,
            "--nt-accent-error": self.colors.accent_error,
            "--nt-accent-warning": self.colors.accent_warning,
            "--nt-accent-info": self.colors.accent_info,
            
            # Colors - Borders
            "--nt-border-subtle": self.colors.border_subtle,
            "--nt-border-strong": self.colors.border_strong,
            
            # Colors - Special
            "--nt-cursor": self.colors.cursor,
            "--nt-selection": self.colors.selection,
            "--nt-glow": self.colors.glow,
            
            # Typography
            "--nt-font-mono": self.typography.font_mono,
            "--nt-font-sans": self.typography.font_sans,
            "--nt-font-size-xs": self.typography.font_size_xs,
            "--nt-font-size-sm": self.typography.font_size_sm,
            "--nt-font-size-base": self.typography.font_size_base,
            "--nt-font-size-md": self.typography.font_size_md,
            "--nt-font-size-lg": self.typography.font_size_lg,
            "--nt-font-size-xl": self.typography.font_size_xl,
            "--nt-line-height": str(self.typography.line_height),
            
            # Spacing
            "--nt-spacing-xs": self.spacing.xs,
            "--nt-spacing-sm": self.spacing.sm,
            "--nt-spacing-md": self.spacing.md,
            "--nt-spacing-lg": self.spacing.lg,
            "--nt-spacing-xl": self.spacing.xl,
            "--nt-spacing-xxl": self.spacing.xxl,
        }


class ThemeRegistry:
    """Registry of available themes."""
    
    # Terminal Green Theme (Default)
    TERMINAL_GREEN = Theme(
        name="Terminal Green",
        mode=ThemeMode.TERMINAL,
        colors=ColorPalette(
            # Backgrounds - Deep blacks
            bg_primary="#0D1117",
            bg_secondary="#161B22",
            bg_tertiary="#21262D",
            
            # Text - High contrast whites/grays
            text_primary="#E6EDF3",
            text_secondary="#8B949E",
            text_disabled="#484F58",
            
            # Accents - Terminal colors
            accent_primary="#00FF41",    # Matrix green
            accent_secondary="#FFB000",  # Amber
            accent_error="#FF4136",      # Red
            accent_warning="#FF851B",    # Orange
            accent_info="#00D9FF",       # Cyan
            
            # Borders
            border_subtle="#30363D",
            border_strong="#8B949E",
            
            # Special
            cursor="#00FF41",
            selection="rgba(0, 255, 65, 0.3)",
            glow="rgba(0, 255, 65, 0.4)",
        ),
        typography=Typography(
            font_mono='"JetBrains Mono", "Fira Code", "SF Mono", Monaco, "Cascadia Code", "Roboto Mono", Consolas, "Courier New", monospace',
            font_sans='-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif',
            font_size_xs="0.75rem",    # 12px
            font_size_sm="0.875rem",   # 14px
            font_size_base="1rem",     # 16px
            font_size_md="1.125rem",   # 18px
            font_size_lg="1.25rem",    # 20px
            font_size_xl="1.5rem",     # 24px
            line_height=1.6,
        ),
        effects=Effects(
            glow_intensity="0 0 10px",
            glow_spread="0 0 20px",
            scanline_opacity=0.03,
            crt_flicker=True,
            cursor_blink=True,
        ),
    )
    
    # Cyberpunk Amber Theme
    CYBERPUNK_AMBER = Theme(
        name="Cyberpunk Amber",
        mode=ThemeMode.TERMINAL,
        colors=ColorPalette(
            bg_primary="#0A0A0A",
            bg_secondary="#141414",
            bg_tertiary="#1E1E1E",
            
            text_primary="#FFE4B5",
            text_secondary="#B8860B",
            text_disabled="#5C4033",
            
            accent_primary="#FFB000",    # Amber
            accent_secondary="#FF6B00",  # Dark orange
            accent_error="#FF2A2A",      # Bright red
            accent_warning="#FFD700",    # Gold
            accent_info="#00CED1",       # Dark turquoise
            
            border_subtle="#2A1F1F",
            border_strong="#8B6914",
            
            cursor="#FFB000",
            selection="rgba(255, 176, 0, 0.3)",
            glow="rgba(255, 176, 0, 0.4)",
        ),
        typography=Typography(
            font_mono='"VT323", "Share Tech Mono", "JetBrains Mono", "Fira Code", monospace',
            font_sans='"Rajdhani", sans-serif',
            font_size_xs="0.75rem",
            font_size_sm="0.875rem",
            font_size_base="1rem",
            font_size_md="1.125rem",
            font_size_lg="1.25rem",
            font_size_xl="1.5rem",
            line_height=1.5,
        ),
        effects=Effects(
            glow_intensity="0 0 8px",
            glow_spread="0 0 16px",
            scanline_opacity=0.05,
            crt_flicker=True,
            cursor_blink=True,
        ),
    )
    
    # Minimal Dark Theme
    MINIMAL_DARK = Theme(
        name="Minimal Dark",
        mode=ThemeMode.DARK,
        colors=ColorPalette(
            bg_primary="#1E1E1E",
            bg_secondary="#252526",
            bg_tertiary="#2D2D30",
            
            text_primary="#D4D4D4",
            text_secondary="#9CDCFE",
            text_disabled="#6E6E6E",
            
            accent_primary="#569CD6",    # Blue
            accent_secondary="#4EC9B0",  # Teal
            accent_error="#F44747",      # Red
            accent_warning="#DCDCAA",    # Yellow
            accent_info="#9CDCFE",       # Light blue
            
            border_subtle="#3E3E42",
            border_strong="#555555",
            
            cursor="#AEAFAD",
            selection="rgba(0, 120, 215, 0.3)",
            glow="rgba(86, 156, 214, 0.3)",
        ),
        typography=Typography(
            font_mono='"SF Mono", "Consolas", "Courier New", monospace',
            font_sans='"Segoe UI", sans-serif',
            font_size_xs="0.75rem",
            font_size_sm="0.875rem",
            font_size_base="1rem",
            font_size_md="1.125rem",
            font_size_lg="1.25rem",
            font_size_xl="1.5rem",
            line_height=1.6,
        ),
        effects=Effects(
            glow_intensity="0 0 5px",
            glow_spread="0 0 10px",
            scanline_opacity=0.0,
            crt_flicker=False,
            cursor_blink=False,
        ),
    )
    
    @classmethod
    def get_theme(cls, name: str) -> Theme:
        """Get a theme by name.
        
        Args:
            name: Theme name (case-insensitive)
            
        Returns:
            Theme instance
            
        Raises:
            ValueError: If theme not found
        """
        themes = {
            "terminal": cls.TERMINAL_GREEN,
            "terminal_green": cls.TERMINAL_GREEN,
            "green": cls.TERMINAL_GREEN,
            "amber": cls.CYBERPUNK_AMBER,
            "cyberpunk": cls.CYBERPUNK_AMBER,
            "cyberpunk_amber": cls.CYBERPUNK_AMBER,
            "minimal": cls.MINIMAL_DARK,
            "dark": cls.MINIMAL_DARK,
            "minimal_dark": cls.MINIMAL_DARK,
        }
        
        key = name.lower().replace(" ", "_")
        if key not in themes:
            available = ", ".join(sorted(set(themes.keys())))
            raise ValueError(f"Unknown theme '{name}'. Available: {available}")
        
        return themes[key]
    
    @classmethod
    def list_themes(cls) -> List[Tuple[str, str]]:
        """List available themes.
        
        Returns:
            List of (key, display_name) tuples
        """
        return [
            ("terminal", "Terminal Green (Default)"),
            ("amber", "Cyberpunk Amber"),
            ("minimal", "Minimal Dark"),
        ]


# Default theme instance
DEFAULT_THEME = ThemeRegistry.TERMINAL_GREEN
