"""Status bar component for cost and system information.

Provides real-time cost tracking and system status display.
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass
from decimal import Decimal

import streamlit as st


@dataclass
class StatusInfo:
    """Status information for display."""
    total_cost: Decimal = Decimal("0.00")
    budget_limit: Optional[Decimal] = None
    total_tokens: int = 0
    message_count: int = 0
    current_model: str = "unknown"
    is_streaming: bool = False
    connection_status: str = "connected"  # connected, disconnected, error


class StatusBar:
    """Terminal-style status bar."""
    
    # Status indicator characters
    INDICATORS = {
        'connected': '🟢',
        'disconnected': '🔴',
        'error': '⚠️',
        'streaming': '⚡',
    }
    
    def __init__(self):
        """Initialize status bar."""
        pass
    
    def render(self, status: StatusInfo) -> None:
        """Render status bar.
        
        Args:
            status: Current status information
        """
        # Calculate budget usage
        budget_percent = 0.0
        if status.budget_limit and status.budget_limit > 0:
            budget_percent = float(status.total_cost / status.budget_limit * 100)
        
        # Determine status indicator
        if status.is_streaming:
            indicator = self.INDICATORS['streaming']
            status_text = "STREAMING"
        else:
            indicator = self.INDICATORS.get(status.connection_status, '⚪')
            status_text = status.connection_status.upper()
        
        # Build HTML
        html = f'''
        <div class="nt-status-bar">
            <div class="nt-status-left">
                <span class="nt-status-indicator">{indicator}</span>
                <span class="nt-status-text">{status_text}</span>
                <span class="nt-status-separator">|</span>
                <span class="nt-status-model">{status.current_model}</span>
            </div>
            <div class="nt-status-right">
                <span class="nt-status-messages">{status.message_count} msgs</span>
                <span class="nt-status-separator">|</span>
                <span class="nt-status-tokens">{status.total_tokens} tokens</span>
                <span class="nt-status-separator">|</span>
                <span class="nt-status-cost ${'warning' if budget_percent > 80 else ''}">
                    ${float(status.total_cost):.4f}
                </span>
            </div>
        </div>
        '''
        
        st.markdown(html, unsafe_allow_html=True)
    
    def render_compact(self, status: StatusInfo) -> None:
        """Render compact status bar.
        
        Args:
            status: Current status information
        """
        cols = st.columns([1, 1, 1, 1])
        
        with cols[0]:
            if status.is_streaming:
                st.write("⚡ Streaming...")
            else:
                status_emoji = "🟢" if status.connection_status == "connected" else "🔴"
                st.write(f"{status_emoji} {status.connection_status}")
        
        with cols[1]:
            st.write(f"💬 {status.message_count}")
        
        with cols[2]:
            st.write(f"🔤 {status.total_tokens}")
        
        with cols[3]:
            cost_text = f"${float(status.total_cost):.4f}"
            if status.budget_limit:
                percent = float(status.total_cost / status.budget_limit * 100)
                if percent > 80:
                    cost_text = f"🔴 {cost_text}"
                elif percent > 50:
                    cost_text = f"🟡 {cost_text}"
            st.write(cost_text)
    
    def render_budget_warning(self, status: StatusInfo) -> None:
        """Render budget warning if approaching limit.
        
        Args:
            status: Current status information
        """
        if not status.budget_limit:
            return
        
        percent = float(status.total_cost / status.budget_limit * 100)
        
        if percent >= 100:
            st.error(f"⚠️ Budget exceeded! ${float(status.total_cost):.4f} / ${float(status.budget_limit):.2f}")
        elif percent >= 80:
            st.warning(f"⚠️ Budget at {percent:.1f}% (${float(status.total_cost):.4f} / ${float(status.budget_limit):.2f})")


class CostDisplay:
    """Detailed cost display component."""
    
    def __init__(self):
        """Initialize cost display."""
        pass
    
    def render(
        self,
        current_cost: Decimal,
        session_cost: Decimal,
        budget_limit: Optional[Decimal] = None,
    ) -> None:
        """Render detailed cost information.
        
        Args:
            current_cost: Current message cost
            session_cost: Total session cost
            budget_limit: Budget limit if set
        """
        st.subheader("💰 Cost Information")
        
        cols = st.columns(3)
        
        with cols[0]:
            st.metric(
                "Current Message",
                f"${float(current_cost):.4f}",
            )
        
        with cols[1]:
            st.metric(
                "Session Total",
                f"${float(session_cost):.4f}",
            )
        
        with cols[2]:
            if budget_limit:
                remaining = budget_limit - session_cost
                st.metric(
                    "Budget Remaining",
                    f"${float(remaining):.4f}",
                    delta=f"Limit: ${float(budget_limit):.2f}",
                )
            else:
                st.metric("Budget", "No limit")
        
        # Budget progress
        if budget_limit and budget_limit > 0:
            percent = float(session_cost / budget_limit * 100)
            
            st.progress(
                min(percent / 100, 1.0),
                text=f"Budget used: {percent:.1f}%",
            )
    
    def render_breakdown(
        self,
        costs_by_model: Dict[str, Decimal],
    ) -> None:
        """Render cost breakdown by model.
        
        Args:
            costs_by_model: Dictionary of model -> cost
        """
        if not costs_by_model:
            st.info("No cost data available")
            return
        
        st.subheader("Cost by Model")
        
        for model, cost in sorted(
            costs_by_model.items(),
            key=lambda x: x[1],
            reverse=True,
        ):
            st.write(f"**{model}**: ${float(cost):.4f}")


# Convenience functions
def render_status(
    total_cost: Decimal,
    budget_limit: Optional[Decimal] = None,
    is_streaming: bool = False,
    **kwargs,
) -> None:
    """Render simple status bar.
    
    Args:
        total_cost: Total cost
        budget_limit: Budget limit
        is_streaming: Whether streaming
        **kwargs: Additional status fields
    """
    status = StatusInfo(
        total_cost=total_cost,
        budget_limit=budget_limit,
        is_streaming=is_streaming,
        **kwargs,
    )
    
    bar = StatusBar()
    bar.render(status)


def render_budget_warning(
    total_cost: Decimal,
    budget_limit: Decimal,
) -> None:
    """Render budget warning if needed.
    
    Args:
        total_cost: Total cost
        budget_limit: Budget limit
    """
    status = StatusInfo(
        total_cost=total_cost,
        budget_limit=budget_limit,
    )
    
    bar = StatusBar()
    bar.render_budget_warning(status)
