# Technical Design

## Technology Stack

### Core Framework
- **Chainlit** (>=1.0.0): Modern Python framework for building conversational AI applications with a built-in UI
  - Provides chat interface, file upload, authentication, and session management
  - Supports streaming responses and real-time updates

### LLM & AI
- **OpenAI** (>=1.0.0): Primary LLM provider
  - `langchain-openai` (>=0.1.0): LangChain integration for OpenAI
  - Models: GPT-4o-mini (default, configurable via `DEFAULT_GAI_MODEL`)
  - Used for both chat completions and text embeddings

### LangChain Ecosystem
- **langchain** (>=0.1.0): Core orchestration framework
- **langchain-community** (>=0.0.20): Community integrations
- **langchain-text-splitters** (>=0.0.1): Text chunking utilities
- **Components Used**:
  - `ConversationalRetrievalChain`: RAG chain with conversation memory
  - `RecursiveCharacterTextSplitter`: Document chunking (1000 chars, 100 overlap)
  - `ConversationBufferMemory`: Maintains chat history
  - `ChatMessageHistory`: Stores message history

### Vector Database
- **ChromaDB** (>=0.4.0): Embedded vector database for document embeddings
  - Stores document chunks as vectors
  - Enables semantic search over uploaded documents
  - Metadata tracking for source attribution

### PII Security
- **presidio-analyzer** (>=2.2.0): Detects PII in text
- **presidio-anonymizer** (>=2.2.0): Anonymizes detected PII
- **spacy** (>=3.7.0): NLP library used by Presidio
  - English model: `en_core_web_sm` (downloaded during Docker build)

### Database
- **SQLAlchemy** (>=2.0.0): ORM for database operations
- **aiosqlite** (>=0.19.0): Async SQLite driver
  - Used for persistent session storage
  - Database path: `./data/chainlit.db`

### Development Tools
- **ruff** (>=0.1.0): Fast Python linter and formatter
  - Replaces black, isort, flake8, and other tools
  - Configured in `pyproject.toml`
- **pytest** (>=7.4.0): Testing framework
- **pytest-asyncio** (>=0.21.0): Async test support

### Package Management
- **uv**: Fast Python package installer and resolver
  - Used for dependency management and virtual environment creation
  - Faster than pip, written in Rust

### Containerization
- **Docker**: Container runtime
- **Docker Compose**: Multi-container orchestration
  - Hot reload support for development
  - Volume mounting for code changes
  - Health checks configured

## Architecture

### Application Flow

```
User Uploads Document
    ↓
Text Extraction & Chunking
    ↓
Embedding Generation (OpenAI)
    ↓
Vector Store Creation (ChromaDB)
    ↓
User Query → PII Anonymization
    ↓
Retrieval from Vector Store
    ↓
RAG Chain (LangChain)
    ↓
LLM Response → PII Anonymization
    ↓
Stream Response to User
```

### Key Components

1. **Document Processing Pipeline**
   - File upload → Text extraction → Chunking → Embedding → Vector storage

2. **Query Processing Pipeline**
   - User input → PII detection/anonymization → Vector retrieval → RAG → Response anonymization → Streaming output

3. **Session Management**
   - Persistent sessions stored in SQLite
   - Conversation history maintained via LangChain memory

4. **Security Layer**
   - PII detection on both input and output
   - Google OAuth authentication (can be bypassed in dev mode via `CHAINLIT_NO_LOGIN`)

## Developer Quickstart

### Prerequisites
- Python 3.12 (required)
- Docker and Docker Compose (optional, for containerized development)
- `uv` package manager (recommended) or `pip`
- OpenAI API key

### Local Development Setup

#### Option 1: Using uv (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd chainlit-bootstrap
   ```

2. **Create virtual environment**
   ```bash
   make venv
   # Or manually: uv venv --python python3.12
   ```

3. **Install dependencies**
   ```bash
   make install
   # Or manually: uv pip install --python .venv/bin/python <dependencies>
   ```

4. **Download spaCy model** (required for Presidio)
   ```bash
   source .venv/bin/activate  # or: .venv/bin/activate
   python -m spacy download en_core_web_sm
   ```

5. **Set environment variables**
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   # Optional:
   export DEFAULT_GAI_MODEL="gpt-4o-mini"
   export CHAINLIT_PORT=8000
   # To bypass authentication in dev mode:
   export CHAINLIT_NO_LOGIN=1
   ```

6. **Run the application**
   ```bash
   chainlit run app.py
   ```
   The app will be available at `http://localhost:8000`

#### Option 2: Using Docker

1. **Create `.env` file**
   ```bash
   echo "OPENAI_API_KEY=your-api-key-here" > .env
   ```

2. **Build and run**
   ```bash
   make build    # Build Docker image
   make dev      # Run with hot reload
   # Or: docker-compose up
   ```

3. **Access the application**
   - Open `http://localhost:8000` in your browser

### Development Workflow

#### Code Quality
```bash
# Lint code
make lint

# Format code
make format

# Auto-fix issues
make fix
```

#### Testing
```bash
# Run tests
make test

# Note: Create tests/ directory and add pytest tests
```

#### Cleanup
```bash
# Remove build artifacts and caches
make clean
```

### Project Structure

```
chainlit-bootstrap/
├── app.py                 # Main application entry point
├── chainlit.toml          # Chainlit configuration
├── pyproject.toml         # Python project metadata and dependencies
├── Dockerfile             # Docker image definition
├── docker-compose.yml     # Docker Compose configuration
├── Makefile               # Development commands
├── data/                  # Persistent data (database, uploads)
│   └── chainlit.db       # SQLite database (created at runtime)
├── docs/                  # Documentation
│   ├── requirements.md
│   └── technical-design.md
└── tests/                 # Test directory (create as needed)
```

### Configuration Files

- **`chainlit.toml`**: Chainlit UI and feature configuration
  - Authentication settings
  - Feature flags (voice, file upload, etc.)
  - UI customization

- **`pyproject.toml`**: Python project configuration
  - Dependencies
  - Ruff linting/formatting rules
  - Build system configuration

### Environment Variables

Create a `.env` file for local development (or export in shell):

```bash
OPENAI_API_KEY=sk-...
DEFAULT_GAI_MODEL=gpt-4o-mini  # Optional
CHAINLIT_PORT=8000              # Optional
CHAINLIT_HOST=0.0.0.0           # Optional
CHAINLIT_NO_LOGIN=1             # Optional: bypass authentication in dev mode
```

### Common Development Tasks

#### Adding a New Dependency
1. Add to `pyproject.toml` under `dependencies`
2. Run `make install` to sync
3. Update `Dockerfile` and `Makefile` if needed

#### Modifying Chainlit Configuration
- Edit `chainlit.toml`
- Restart the application for changes to take effect
- Note: `CHAINLIT_NO_LOGIN` environment variable programmatically modifies `chainlit.toml` to disable authentication when set

#### Debugging
- Chainlit provides built-in debugging UI
- Check logs in terminal output
- Use `cl.Message()` for debugging messages

### Troubleshooting

#### Issue: spaCy model not found
```bash
python -m spacy download en_core_web_sm
```

#### Issue: Port already in use
```bash
export CHAINLIT_PORT=8001
# Or change in docker-compose.yml
```

#### Issue: OpenAI API errors
- Verify `OPENAI_API_KEY` is set correctly
- Check API key has sufficient credits
- Verify model name is correct

#### Issue: Docker build fails
- Ensure Docker has sufficient memory (4GB+ recommended)
- Check Python version compatibility (3.12 required)

### Next Steps for Contributors

1. Review `app.py` to understand the application flow
2. Check `chainlit.toml` for available features
3. Explore LangChain documentation for RAG patterns
4. Review Presidio documentation for PII detection customization
5. Consider implementing TODO items in `app.py` (PDF support, voice integration)

