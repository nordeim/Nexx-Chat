#!/usr/bin/env python3
"""
Neural Terminal - Production-grade chatbot with OpenRouter integration.

A Streamlit-based chat interface with:
- Multiple AI model support via OpenRouter
- Cost tracking and budget management
- Conversation history
- Terminal/cyberpunk aesthetic
- XSS-safe message rendering

Usage:
    streamlit run app.py

Environment Variables:
    OPENROUTER_API_KEY: Your OpenRouter API key
    DATABASE_URL: SQLite database URL (default: sqlite:///neural_terminal.db)
    DEFAULT_MODEL: Default AI model (default: openai/gpt-3.5-turbo)
"""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from neural_terminal.main import main

if __name__ == "__main__":
    main()
