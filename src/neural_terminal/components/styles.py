"""CSS generation and injection utilities for Neural Terminal.

Provides utilities for generating and injecting custom CSS into Streamlit,
creating the terminal aesthetic UI.
"""

from typing import Dict, Optional
import streamlit as st

from .themes import Theme, ThemeRegistry, DEFAULT_THEME


def generate_base_css(theme: Theme) -> str:
    """Generate base CSS with theme variables.
    
    Args:
        theme: Theme configuration
        
    Returns:
        CSS string with custom properties
    """
    vars_css = "\n".join(
        f"    {k}: {v};" for k, v in theme.to_css_variables().items()
    )
    
    return f"""
    <style>
    :root {{
{vars_css}
    }}
    
    /* Base styles */
    .stApp {{
        background-color: var(--nt-bg-primary) !important;
        color: var(--nt-text-primary) !important;
        font-family: var(--nt-font-mono) !important;
    }}
    
    /* Main container */
    .main .block-container {{
        background-color: var(--nt-bg-primary) !important;
        padding: var(--nt-spacing-md) !important;
        max-width: 1200px !important;
    }}
    
    /* Typography */
    h1, h2, h3, h4, h5, h6 {{
        font-family: var(--nt-font-mono) !important;
        color: var(--nt-text-primary) !important;
        font-weight: 600 !important;
    }}
    
    h1 {{
        color: var(--nt-accent-primary) !important;
        text-shadow: var(--nt-glow) !important;
        border-bottom: 2px solid var(--nt-border-subtle) !important;
        padding-bottom: var(--nt-spacing-sm) !important;
    }}
    
    p, span, div {{
        font-family: var(--nt-font-mono) !important;
    }}
    
    /* Links */
    a {{
        color: var(--nt-accent-info) !important;
        text-decoration: none !important;
        border-bottom: 1px dotted var(--nt-accent-info) !important;
        transition: all 0.2s ease !important;
    }}
    
    a:hover {{
        color: var(--nt-accent-primary) !important;
        border-bottom: 1px solid var(--nt-accent-primary) !important;
        text-shadow: 0 0 5px var(--nt-glow) !important;
    }}
    
    /* Code */
    code {{
        font-family: var(--nt-font-mono) !important;
        background-color: var(--nt-bg-tertiary) !important;
        color: var(--nt-accent-primary) !important;
        padding: 0.2em 0.4em !important;
        border-radius: 3px !important;
        font-size: 0.9em !important;
    }}
    
    pre {{
        background-color: var(--nt-bg-secondary) !important;
        border: 1px solid var(--nt-border-subtle) !important;
        border-radius: 6px !important;
        padding: var(--nt-spacing-md) !important;
        overflow-x: auto !important;
    }}
    
    pre code {{
        background-color: transparent !important;
        padding: 0 !important;
    }}
    
    /* Selection */
    ::selection {{
        background-color: var(--nt-selection) !important;
        color: var(--nt-text-primary) !important;
    }}
    
    /* Scrollbar */
    ::-webkit-scrollbar {{
        width: 10px !important;
        height: 10px !important;
    }}
    
    ::-webkit-scrollbar-track {{
        background: var(--nt-bg-secondary) !important;
    }}
    
    ::-webkit-scrollbar-thumb {{
        background: var(--nt-border-subtle) !important;
        border-radius: 5px !important;
    }}
    
    ::-webkit-scrollbar-thumb:hover {{
        background: var(--nt-accent-primary) !important;
    }}
    
    /* Sidebar */
    [data-testid="stSidebar"] {{
        background-color: var(--nt-bg-secondary) !important;
        border-right: 1px solid var(--nt-border-subtle) !important;
    }}
    
    [data-testid="stSidebar"] .stMarkdown {{
        color: var(--nt-text-secondary) !important;
    }}
    
    /* Buttons */
    .stButton > button {{
        background-color: var(--nt-bg-tertiary) !important;
        color: var(--nt-accent-primary) !important;
        border: 1px solid var(--nt-accent-primary) !important;
        border-radius: 4px !important;
        font-family: var(--nt-font-mono) !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
    }}
    
    .stButton > button:hover {{
        background-color: var(--nt-accent-primary) !important;
        color: var(--nt-bg-primary) !important;
        box-shadow: var(--nt-glow) !important;
    }}
    
    .stButton > button:active {{
        transform: scale(0.98) !important;
    }}
    
    .stButton > button:disabled {{
        background-color: var(--nt-bg-secondary) !important;
        color: var(--nt-text-disabled) !important;
        border-color: var(--nt-border-subtle) !important;
        cursor: not-allowed !important;
    }}
    
    /* Inputs */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {{
        background-color: var(--nt-bg-secondary) !important;
        color: var(--nt-text-primary) !important;
        border: 1px solid var(--nt-border-subtle) !important;
        border-radius: 4px !important;
        font-family: var(--nt-font-mono) !important;
    }}
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {{
        border-color: var(--nt-accent-primary) !important;
        box-shadow: 0 0 0 1px var(--nt-accent-primary) !important;
    }}
    
    /* Selectbox */
    .stSelectbox > div > div > div {{
        background-color: var(--nt-bg-secondary) !important;
        color: var(--nt-text-primary) !important;
        border: 1px solid var(--nt-border-subtle) !important;
        border-radius: 4px !important;
        font-family: var(--nt-font-mono) !important;
    }}
    
    /* Expander */
    .streamlit-expanderHeader {{
        background-color: var(--nt-bg-secondary) !important;
        color: var(--nt-text-primary) !important;
        border: 1px solid var(--nt-border-subtle) !important;
        border-radius: 4px !important;
        font-family: var(--nt-font-mono) !important;
    }}
    
    .streamlit-expanderContent {{
        background-color: var(--nt-bg-primary) !important;
        border: 1px solid var(--nt-border-subtle) !important;
        border-top: none !important;
        border-radius: 0 0 4px 4px !important;
    }}
    
    /* Divider */
    hr {{
        border-color: var(--nt-border-subtle) !important;
        border-width: 1px !important;
        border-style: solid !important;
        margin: var(--nt-spacing-lg) 0 !important;
    }}
    
    /* Toast/Alerts */
    .stAlert {{
        background-color: var(--nt-bg-secondary) !important;
        border: 1px solid var(--nt-border-subtle) !important;
        border-radius: 4px !important;
        font-family: var(--nt-font-mono) !important;
    }}
    
    .stAlert [data-baseweb="notification"] {{
        background-color: transparent !important;
    }}
    </style>
    """


def generate_terminal_effects_css(theme: Theme) -> str:
    """Generate terminal-specific effect CSS.
    
    Args:
        theme: Theme configuration
        
    Returns:
        CSS string with terminal effects
    """
    effects = []
    
    # Glow effect for primary accent
    effects.append(f"""
    <style>
    .terminal-glow {{
        text-shadow: {theme.effects.glow_intensity} {theme.colors.glow} !important;
    }}
    
    .terminal-glow-strong {{
        text-shadow: {theme.effects.glow_spread} {theme.colors.glow} !important;
    }}
    
    .terminal-border-glow {{
        box-shadow: 0 0 10px {theme.colors.glow} !important;
    }}
    </style>
    """)
    
    # Cursor blink effect
    if theme.effects.cursor_blink:
        effects.append(f"""
    <style>
    @keyframes blink {{
        0%, 50% {{ opacity: 1; }}
        51%, 100% {{ opacity: 0; }}
    }}
    
    .terminal-cursor {{
        display: inline-block;
        width: 0.6em;
        height: 1.2em;
        background-color: {theme.colors.cursor};
        animation: blink 1s step-end infinite;
        vertical-align: text-bottom;
        margin-left: 2px;
    }}
    </style>
    """)
    
    # Scanline effect
    if theme.effects.scanline_opacity > 0:
        opacity = theme.effects.scanline_opacity
        effects.append(f"""
    <style>
    .terminal-scanlines::before {{
        content: "";
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: repeating-linear-gradient(
            0deg,
            rgba(0, 0, 0, {opacity}),
            rgba(0, 0, 0, {opacity}) 1px,
            transparent 1px,
            transparent 2px
        );
        pointer-events: none;
        z-index: 9999;
    }}
    </style>
    """)
    
    return "\n".join(effects)


def generate_message_css(theme: Theme) -> str:
    """Generate CSS for message bubbles.
    
    Args:
        theme: Theme configuration
        
    Returns:
        CSS string for message components
    """
    return f"""
    <style>
    /* Message container */
    .nt-message-container {{
        display: flex;
        flex-direction: column;
        gap: var(--nt-spacing-sm);
        margin-bottom: var(--nt-spacing-md);
    }}
    
    /* Message bubble base */
    .nt-message {{
        max-width: 85%;
        padding: var(--nt-spacing-md);
        border-radius: 8px;
        font-family: var(--nt-font-mono) !important;
        line-height: var(--nt-line-height);
        word-wrap: break-word;
        position: relative;
    }}
    
    /* User message */
    .nt-message-user {{
        align-self: flex-end;
        background-color: var(--nt-bg-tertiary);
        border: 1px solid var(--nt-accent-primary);
        color: var(--nt-text-primary);
        border-bottom-right-radius: 2px;
    }}
    
    .nt-message-user::before {{
        content: ">>>";
        color: var(--nt-accent-primary);
        margin-right: var(--nt-spacing-sm);
        font-weight: bold;
    }}
    
    /* Assistant message */
    .nt-message-assistant {{
        align-self: flex-start;
        background-color: var(--nt-bg-secondary);
        border: 1px solid var(--nt-border-subtle);
        color: var(--nt-text-primary);
        border-bottom-left-radius: 2px;
    }}
    
    .nt-message-assistant::before {{
        content: "█";
        color: var(--nt-accent-secondary);
        margin-right: var(--nt-spacing-sm);
    }}
    
    /* System message */
    .nt-message-system {{
        align-self: center;
        background-color: transparent;
        border: 1px dashed var(--nt-border-subtle);
        color: var(--nt-text-secondary);
        font-size: var(--nt-font-size-sm);
        font-style: italic;
        max-width: 90%;
    }}
    
    /* Error message */
    .nt-message-error {{
        align-self: center;
        background-color: rgba(255, 65, 54, 0.1);
        border: 1px solid var(--nt-accent-error);
        color: var(--nt-accent-error);
        max-width: 90%;
    }}
    
    .nt-message-error::before {{
        content: "[ERROR]";
        color: var(--nt-accent-error);
        margin-right: var(--nt-spacing-sm);
        font-weight: bold;
    }}
    
    /* Message metadata */
    .nt-message-meta {{
        font-size: var(--nt-font-size-xs);
        color: var(--nt-text-secondary);
        margin-top: var(--nt-spacing-xs);
        display: flex;
        gap: var(--nt-spacing-md);
    }}
    
    .nt-message-cost {{
        color: var(--nt-accent-secondary);
    }}
    
    .nt-message-tokens {{
        color: var(--nt-text-disabled);
    }}
    
    /* Streaming indicator */
    .nt-streaming {{
        display: inline-block;
        color: var(--nt-accent-primary);
    }}
    
    .nt-streaming::after {{
        content: "▋";
        animation: blink 1s step-end infinite;
    }}
    </style>
    """


def generate_header_css(theme: Theme) -> str:
    """Generate CSS for header component.
    
    Args:
        theme: Theme configuration
        
    Returns:
        CSS string for header
    """
    return f"""
    <style>
    .nt-header {{
        background-color: var(--nt-bg-secondary);
        border: 1px solid var(--nt-border-subtle);
        border-radius: 8px;
        padding: var(--nt-spacing-md);
        margin-bottom: var(--nt-spacing-lg);
        display: flex;
        justify-content: space-between;
        align-items: center;
    }}
    
    .nt-header-title {{
        font-size: var(--nt-font-size-xl);
        font-weight: bold;
        color: var(--nt-accent-primary);
        text-shadow: var(--nt-glow);
        margin: 0;
    }}
    
    .nt-header-subtitle {{
        font-size: var(--nt-font-size-sm);
        color: var(--nt-text-secondary);
        margin: 0;
    }}
    
    .nt-header-status {{
        display: flex;
        align-items: center;
        gap: var(--nt-spacing-sm);
        font-size: var(--nt-font-size-sm);
        color: var(--nt-text-secondary);
    }}
    
    .nt-status-indicator {{
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background-color: var(--nt-accent-primary);
        box-shadow: 0 0 8px var(--nt-accent-primary);
    }}
    
    .nt-status-indicator.offline {{
        background-color: var(--nt-accent-error);
        box-shadow: 0 0 8px var(--nt-accent-error);
    }}
    </style>
    """


def generate_input_css(theme: Theme) -> str:
    """Generate CSS for input area.
    
    Args:
        theme: Theme configuration
        
    Returns:
        CSS string for input component
    """
    return f"""
    <style>
    .nt-input-container {{
        background-color: var(--nt-bg-secondary);
        border: 1px solid var(--nt-border-subtle);
        border-radius: 8px;
        padding: var(--nt-spacing-md);
        margin-top: var(--nt-spacing-lg);
        position: sticky;
        bottom: 0;
    }}
    
    .nt-input-prompt {{
        color: var(--nt-accent-primary);
        font-weight: bold;
        margin-bottom: var(--nt-spacing-sm);
    }}
    
    .nt-input-hint {{
        font-size: var(--nt-font-size-xs);
        color: var(--nt-text-secondary);
        margin-top: var(--nt-spacing-xs);
    }}
    
    .nt-input-hint kbd {{
        background-color: var(--nt-bg-tertiary);
        border: 1px solid var(--nt-border-subtle);
        border-radius: 3px;
        padding: 0.1em 0.4em;
        font-family: var(--nt-font-mono);
        font-size: 0.9em;
    }}
    </style>
    """


def generate_status_bar_css(theme: Theme) -> str:
    """Generate CSS for status bar.
    
    Args:
        theme: Theme configuration
        
    Returns:
        CSS string for status bar
    """
    return f"""
    <style>
    .nt-status-bar {{
        background-color: var(--nt-bg-secondary);
        border-top: 1px solid var(--nt-border-subtle);
        padding: var(--nt-spacing-sm) var(--nt-spacing-md);
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: var(--nt-font-size-sm);
        color: var(--nt-text-secondary);
        font-family: var(--nt-font-mono);
    }}
    
    .nt-status-section {{
        display: flex;
        align-items: center;
        gap: var(--nt-spacing-md);
    }}
    
    .nt-status-label {{
        color: var(--nt-text-disabled);
    }}
    
    .nt-status-value {{
        color: var(--nt-accent-secondary);
        font-weight: 500;
    }}
    
    .nt-status-value.warning {{
        color: var(--nt-accent-warning);
    }}
    
    .nt-status-value.error {{
        color: var(--nt-accent-error);
    }}
    
    /* Progress bar for budget */
    .nt-budget-bar {{
        width: 100px;
        height: 4px;
        background-color: var(--nt-bg-tertiary);
        border-radius: 2px;
        overflow: hidden;
    }}
    
    .nt-budget-fill {{
        height: 100%;
        background-color: var(--nt-accent-primary);
        transition: width 0.3s ease;
    }}
    
    .nt-budget-fill.warning {{
        background-color: var(--nt-accent-warning);
    }}
    
    .nt-budget-fill.error {{
        background-color: var(--nt-accent-error);
    }}
    </style>
    """


def generate_all_css(theme: Optional[Theme] = None) -> str:
    """Generate complete CSS for the theme.
    
    Args:
        theme: Theme to use (defaults to TERMINAL_GREEN)
        
    Returns:
        Complete CSS string
    """
    if theme is None:
        theme = DEFAULT_THEME
    
    css_parts = [
        generate_base_css(theme),
        generate_terminal_effects_css(theme),
        generate_message_css(theme),
        generate_header_css(theme),
        generate_input_css(theme),
        generate_status_bar_css(theme),
    ]
    
    return "\n".join(css_parts)


def inject_css(theme: Optional[Theme] = None, key: str = "nt_theme_css") -> None:
    """Inject CSS into Streamlit.
    
    Uses st.markdown with unsafe_allow_html to inject custom CSS.
    Only injects once per session to avoid duplication.
    
    Args:
        theme: Theme to use (defaults to TERMINAL_GREEN)
        key: Unique key for the markdown container
    """
    if theme is None:
        theme = DEFAULT_THEME
    
    # Check if already injected this session
    css_key = f"_{key}_injected"
    if css_key in st.session_state:
        return
    
    css = generate_all_css(theme)
    st.markdown(css, unsafe_allow_html=True)
    
    # Mark as injected
    st.session_state[css_key] = True


def switch_theme(theme_name: str) -> Theme:
    """Switch to a different theme.
    
    Args:
        theme_name: Name of the theme to switch to
        
    Returns:
        The new theme instance
    """
    theme = ThemeRegistry.get_theme(theme_name)
    
    # Clear injection flag to force re-injection
    for key in list(st.session_state.keys()):
        if key.endswith("_injected"):
            del st.session_state[key]
    
    inject_css(theme)
    return theme


class StyleManager:
    """Manager for theme and styling."""
    
    def __init__(self, theme: Optional[Theme] = None):
        """Initialize style manager.
        
        Args:
            theme: Initial theme (defaults to TERMINAL_GREEN)
        """
        self._theme = theme or DEFAULT_THEME
    
    @property
    def theme(self) -> Theme:
        """Get current theme."""
        return self._theme
    
    def apply(self) -> None:
        """Apply current theme to Streamlit."""
        inject_css(self._theme)
    
    def set_theme(self, theme_name: str) -> Theme:
        """Change theme.
        
        Args:
            theme_name: Name of theme to switch to
            
        Returns:
            New theme instance
        """
        self._theme = ThemeRegistry.get_theme(theme_name)
        self.apply()
        return self._theme
