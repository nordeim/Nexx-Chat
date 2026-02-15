# Neural Terminal ⚡

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-330%20passing-brightgreen.svg)]()
[![Poetry](https://img.shields.io/badge/poetry-managed-blue.svg)](https://python-poetry.org/)

> A production-grade chatbot interface with OpenRouter integration, featuring a distinctive terminal/cyberpunk aesthetic.

![Terminal Green Theme](https://img.shields.io/badge/Theme-Terminal%20Green-00FF41)
![Cyberpunk Amber Theme](https://img.shields.io/badge/Theme-Cyberpunk%20Amber-FFB000)
![Minimal Dark Theme](https://img.shields.io/badge/Theme-Minimal%20Dark-569CD6)

## Features

### 🤖 AI Model Support
- **Multi-model integration** via OpenRouter API
- Support for GPT-4, GPT-3.5, Claude 3, Gemini Pro, Llama 2, Mistral, and more
- Real-time streaming responses
- Context window management with automatic truncation

### 💰 Cost Tracking & Budget Management
- Real-time cost calculation per message
- Session and conversation cost tracking
- Budget limits with warnings at 80% and 100%
- Cost breakdown by model

### 🎨 Terminal Aesthetic
- **3 Distinct Themes:**
  - Terminal Green (Matrix-style with glow effects)
  - Cyberpunk Amber (Retro-futuristic amber phosphor)
  - Minimal Dark (Clean VS Code-inspired)
- Monospace typography (JetBrains Mono, Fira Code)
- CRT scanline effects and cursor blink
- Syntax-highlighted code blocks

### 🔒 Security & Safety
- XSS protection via Bleach sanitization
- API key secure storage (never logged or displayed)
- Circuit breaker pattern for API resilience
- Input validation and rate limiting

### 💬 Conversation Management
- Persistent conversation history (SQLite)
- Conversation list with search/filter
- New conversation with custom system prompts
- Message metadata (cost, tokens, latency)

## Quick Start

### Prerequisites
- Python 3.11 or higher
- Poetry package manager
- OpenRouter API key ([Get one free](https://openrouter.ai/))

### Installation

#### Option 1: Using Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/example/neural-terminal.git
cd neural-terminal

# Run with Docker Compose (includes persistent storage)
OPENROUTER_API_KEY=your-key docker-compose up -d

# Or build and run manually
docker build -t neural-terminal:latest .
docker run -p 8501:8501 -e OPENROUTER_API_KEY=your-key neural-terminal:latest
```

#### Option 2: Using Poetry

```bash
# Clone the repository
git clone https://github.com/example/neural-terminal.git
cd neural-terminal

# Install dependencies with Poetry
poetry install
```

#### Option 3: Using pip

```bash
pip install -r requirements.txt
```

### Configuration

Set your OpenRouter API key:

```bash
# Option 1: Environment variable
export OPENROUTER_API_KEY="your-api-key-here"

# Option 2: Create .env file
echo "OPENROUTER_API_KEY=your-api-key-here" > .env

# Option 3: Via the Settings UI (in-app)
```

### Running the Application

```bash
# Using Poetry
poetry run streamlit run app.py

# Or with Python directly
PYTHONPATH=src poetry run python -m streamlit run app.py
```

The application will be available at `http://localhost:8501`

## Usage

### Keyboard Shortcuts
- **Enter** - Send message
- **Shift+Enter** - New line in message
- **Ctrl+C** - Copy selection

### Chat Interface
1. Type your message in the input area
2. Press Enter or click Send
3. Watch the AI response stream in real-time
4. View cost and token information below each message

### Managing Conversations
- Click **New Conversation** in the sidebar to start fresh
- Select previous conversations from the list
- Delete conversations with the 🗑️ button

### Settings
Access settings via the sidebar to configure:
- **API Key** - Your OpenRouter API key
- **Default Model** - Preferred AI model
- **Temperature** - Response creativity (0.0-2.0)
- **Max Tokens** - Maximum response length
- **Budget Limit** - Spending cap with warnings
- **Theme** - Visual appearance

## Architecture

```
neural-terminal/
├── app.py                          # Streamlit entry point
├── src/neural_terminal/
│   ├── app_state.py                # Global state management
│   ├── main.py                     # App orchestration
│   ├── components/                 # UI components
│   │   ├── themes.py               # Theme system
│   │   ├── styles.py               # CSS injection
│   │   ├── message_renderer.py     # XSS-safe rendering
│   │   ├── chat_container.py       # Message display
│   │   ├── header.py               # Terminal header
│   │   ├── status_bar.py           # Cost tracking
│   │   └── error_handler.py        # Error display
│   ├── application/                # Business logic
│   │   ├── orchestrator.py         # Chat service
│   │   ├── state.py                # Session state
│   │   ├── events.py               # Event bus
│   │   └── cost_tracker.py         # Budget tracking
│   ├── infrastructure/             # External services
│   │   ├── database.py             # SQLite/SQLAlchemy
│   │   ├── repositories.py         # Repository pattern
│   │   ├── openrouter.py           # API client
│   │   ├── token_counter.py        # Tiktoken
│   │   └── circuit_breaker.py      # Resilience
│   └── domain/                     # Core models
│       ├── models.py               # Domain entities
│       └── exceptions.py           # Custom errors
└── tests/                          # Test suite (330 tests)
```

## Docker Deployment

### Quick Start with Docker Compose

```bash
# Copy example environment file
cp .env.example .env
# Edit .env and add your OPENROUTER_API_KEY

# Start the application
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the application
docker-compose down
```

### Docker Commands

```bash
# Build image
make docker-build

# Run container
make docker-run OPENROUTER_API_KEY=your-key

# Start with docker-compose
make docker-compose-up

# Stop docker-compose
make docker-compose-down
```

### Docker Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENROUTER_API_KEY` | **Required** - OpenRouter API key | - |
| `DEFAULT_MODEL` | Default AI model | `openai/gpt-3.5-turbo` |
| `LOG_LEVEL` | Logging level | `INFO` |

### Persistent Storage

The Docker container stores data in `/app/data`:
- `neural_terminal.db` - SQLite database (conversations, messages)
- Backups are created automatically

Mount a volume for persistence:
```bash
docker run -v $(pwd)/data:/app/data -p 8501:8501 neural-terminal:latest
```

## Development

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=src/neural_terminal --cov-report=html

# Run specific test file
poetry run pytest tests/unit/test_orchestrator.py -v
```

### Code Quality

```bash
# Format code
poetry run black src tests

# Lint with Ruff
poetry run ruff check src tests

# Type check with MyPy
poetry run mypy src
```

### Project Structure Principles

This project follows **Clean Architecture** principles:

1. **Domain Layer** - Core business logic, models, and exceptions
2. **Infrastructure Layer** - External concerns (database, API, tokenization)
3. **Application Layer** - Use cases, orchestration, events
4. **UI Layer** - Streamlit components and presentation

## Configuration Options

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENROUTER_API_KEY` | OpenRouter API key | Required |
| `DATABASE_URL` | SQLite database URL | `sqlite:///neural_terminal.db` |
| `DEFAULT_MODEL` | Default AI model | `openai/gpt-3.5-turbo` |
| `BUDGET_LIMIT` | Default budget limit | None |
| `LOG_LEVEL` | Logging level | `INFO` |

### Available Models

| Model ID | Name |
|----------|------|
| `openai/gpt-4-turbo` | GPT-4 Turbo |
| `openai/gpt-4` | GPT-4 |
| `openai/gpt-3.5-turbo` | GPT-3.5 Turbo |
| `anthropic/claude-3-opus` | Claude 3 Opus |
| `anthropic/claude-3-sonnet` | Claude 3 Sonnet |
| `google/gemini-pro` | Gemini Pro |
| `meta-llama/llama-2-70b-chat` | Llama 2 70B |
| `mistral/mistral-medium` | Mistral Medium |

## Troubleshooting

### Common Issues

**Application won't start**
- Check that `OPENROUTER_API_KEY` is set
- Verify Python version is 3.11+
- Run `poetry install` to ensure dependencies

**Database errors**
- Delete `neural_terminal.db` to reset
- Check file permissions in the project directory

**API rate limiting**
- The app includes circuit breaker protection
- Wait 30 seconds and retry
- Check your OpenRouter quota

**Theme not applying**
- Refresh the browser page
- Check browser console for CSS errors
- Try switching themes in Settings

### Getting Help

- Open an issue on GitHub
- Check existing issues for solutions
- Review the test suite for usage examples

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`poetry run pytest`)
5. Commit (`git commit -m 'Add amazing feature'`)
6. Push (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Development Setup

```bash
# Install dev dependencies
poetry install --with dev

# Pre-commit hooks
poetry run pre-commit install
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [OpenRouter](https://openrouter.ai/) for AI model aggregation
- [Streamlit](https://streamlit.io/) for the web framework
- [SQLAlchemy](https://www.sqlalchemy.org/) for database ORM
- [Bleach](https://bleach.readthedocs.io/) for XSS protection

## Changelog

### 0.1.0 - Initial Release
- ✅ Terminal aesthetic with 3 themes
- ✅ OpenRouter integration with 8 models
- ✅ Real-time streaming responses
- ✅ Cost tracking and budget management
- ✅ Conversation persistence
- ✅ XSS-safe message rendering
- ✅ Circuit breaker resilience
- ✅ 330 passing tests

---

<p align="center">
  Built with ⚡ by the Neural Terminal Team
</p>
