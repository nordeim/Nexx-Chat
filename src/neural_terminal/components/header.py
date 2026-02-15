"""Header component for Neural Terminal.

Provides terminal-style header with model selection and status indicators.
"""

from typing import Optional, List, Tuple, Callable, Any
from dataclasses import dataclass

import streamlit as st

from .themes import Theme, DEFAULT_THEME


@dataclass
class HeaderConfig:
    """Configuration for header component."""
    title: str = "NEURAL TERMINAL"
    subtitle: str = "OpenRouter Chat Interface"
    show_status: bool = True
    show_theme_selector: bool = True
    show_model_selector: bool = True


class Header:
    """Terminal-style header component."""
    
    def __init__(self, config: Optional[HeaderConfig] = None):
        """Initialize header.
        
        Args:
            config: Header configuration
        """
        self._config = config or HeaderConfig()
    
    def render(
        self,
        is_connected: bool = True,
        available_models: Optional[List[Tuple[str, str]]] = None,
        selected_model: Optional[str] = None,
        on_model_change: Optional[Callable[[str], None]] = None,
        theme: Theme = DEFAULT_THEME,
    ) -> None:
        """Render the header.
        
        Args:
            is_connected: Connection status
            available_models: List of (value, label) tuples
            selected_model: Currently selected model
            on_model_change: Callback for model selection change
            theme: Current theme
        """
        # Build header HTML
        status_class = "" if is_connected else "offline"
        status_text = "ONLINE" if is_connected else "OFFLINE"
        
        html = f'''
        <div class="nt-header">
            <div class="nt-header-brand">
                <h1 class="nt-header-title">{self._config.title}</h1>
                <p class="nt-header-subtitle">{self._config.subtitle}</p>
            </div>
            <div class="nt-header-status">
                <span class="nt-status-indicator {status_class}"></span>
                <span>{status_text}</span>
            </div>
        </div>
        '''
        
        st.markdown(html, unsafe_allow_html=True)
        
        # Model selector
        if self._config.show_model_selector and available_models:
            self._render_model_selector(
                available_models,
                selected_model,
                on_model_change,
            )
    
    def _render_model_selector(
        self,
        models: List[Tuple[str, str]],
        selected: Optional[str],
        on_change: Optional[Callable[[str], None]],
    ) -> None:
        """Render model selection dropdown.
        
        Args:
            models: List of (value, label) tuples
            selected: Currently selected value
            on_change: Change callback
        """
        cols = st.columns([3, 1])
        
        with cols[0]:
            # Find index of selected model
            values = [v for v, _ in models]
            index = values.index(selected) if selected in values else 0
            
            labels = [l for _, l in models]
            
            selected_label = st.selectbox(
                "Model",
                options=labels,
                index=index,
                label_visibility="collapsed",
                help="Select AI model to use",
            )
            
            # Get value from label
            selected_value = values[labels.index(selected_label)]
            
            if on_change and selected_value != selected:
                on_change(selected_value)
        
        with cols[1]:
            # Theme toggle (placeholder)
            if self._config.show_theme_selector:
                st.selectbox(
                    "Theme",
                    options=["Terminal", "Amber", "Minimal"],
                    index=0,
                    label_visibility="collapsed",
                    help="Select visual theme",
                )
    
    def render_simple(
        self,
        title: Optional[str] = None,
        is_connected: bool = True,
    ) -> None:
        """Render simplified header.
        
        Args:
            title: Custom title
            is_connected: Connection status
        """
        status_class = "" if is_connected else "offline"
        status_text = "● ONLINE" if is_connected else "● OFFLINE"
        
        display_title = title or self._config.title
        
        html = f'''
        <div class="nt-header">
            <h1 class="nt-header-title">{display_title}</h1>
            <div class="nt-header-status">
                <span class="nt-status-indicator {status_class}"></span>
                <span>{status_text}</span>
            </div>
        </div>
        '''
        
        st.markdown(html, unsafe_allow_html=True)


class Sidebar:
    """Sidebar component for settings and info."""
    
    def __init__(self):
        """Initialize sidebar."""
        pass
    
    def render(
        self,
        total_cost: float = 0.0,
        budget_limit: Optional[float] = None,
        conversation_count: int = 0,
    ) -> None:
        """Render sidebar content.
        
        Args:
            total_cost: Total session cost
            budget_limit: Budget limit if set
            conversation_count: Number of conversations
        """
        with st.sidebar:
            st.title("⚡ Neural Terminal")
            
            # Cost info
            st.subheader("Session Cost")
            
            cost_col, budget_col = st.columns(2)
            with cost_col:
                st.metric("Spent", f"${total_cost:.4f}")
            with budget_col:
                if budget_limit:
                    remaining = budget_limit - total_cost
                    st.metric("Remaining", f"${remaining:.4f}")
                else:
                    st.metric("Budget", "∞")
            
            # Budget progress bar
            if budget_limit and budget_limit > 0:
                progress = min(total_cost / budget_limit, 1.0)
                
                # Determine color based on usage
                if progress < 0.5:
                    color = "normal"
                elif progress < 0.8:
                    color = "orange"
                else:
                    color = "red"
                
                st.progress(progress, text=f"{progress*100:.1f}% used")
            
            st.divider()
            
            # Stats
            st.subheader("Stats")
            st.write(f"Conversations: {conversation_count}")
            
            st.divider()
            
            # Help
            with st.expander("⌨️ Keyboard Shortcuts"):
                st.markdown("""
                - **Enter**: Send message
                - **Shift+Enter**: New line
                - **Ctrl+C**: Copy selection
                """)
            
            with st.expander("📖 Help"):
                st.markdown("""
                **Neural Terminal** is a production-grade chat interface
                for OpenRouter AI models.
                
                Features:
                - Multiple AI model support
                - Cost tracking
                - Conversation history
                - Terminal aesthetic
                """)


# Convenience functions
def render_header(
    title: str = "NEURAL TERMINAL",
    is_connected: bool = True,
) -> None:
    """Render simple header.
    
    Args:
        title: Header title
        is_connected: Connection status
    """
    header = Header(HeaderConfig(title=title))
    header.render_simple(is_connected=is_connected)


def render_sidebar(**kwargs) -> None:
    """Render sidebar.
    
    Args:
        **kwargs: Sidebar parameters
    """
    sidebar = Sidebar()
    sidebar.render(**kwargs)
