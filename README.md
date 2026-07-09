# Resume Analyzer API
An AI service for result analysis based on LangGraph. It accepts a PDF or TXT file, simultaneously launches four specialized agents via Celery, and generates a detailed report that takes requirements and recommendations into account.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        FastAPI                               │
│  POST /analyze   GET /analyze/{task_id}/status               │
│  GET /history    GET /{id}                                   │
└──────────────────────────┬──────────────────────────────────┘
                           │
                    ┌──────▼──────┐
                    │    Redis     │
                    │  cache hit?  │
                    └──────┬──────┘
               HIT ◄───────┴───────► MISS
           (мгновенно)              (202 + task_id)
                                         │
                                  Celery Worker
                                         │
                     ┌───────────────────┴────────────────┐
                     │                                     │
               LangGraph Graph                    ResumeRepository
                     │                                     │
               ┌─────────────┐                         PostgreSQL
               │  Параллельные│
               │   агенты     │
               │              │
               │ analyze_skills
               │ analyze_experience
               │ analyze_structure
               │ analyze_language
               └──────┬───────┘
                      │
               compile_report
                      │
      Save to DB + Redis cache (TTL 24h)
                      │
         (optional) webhook → callback_url
```

## Стек

- **Python 3.11**
- **FastAPI** — REST API
- **LangGraph** — agent orchestration
- **LangChain** — integration with LLM providers
- **Celery + Redis** — background processing and task queue
- **Redis Cache** — result caching (Cache-Aside, 24h TTL)
- **PostgreSQL 16** — analysis history storage
- **SQLAlchemy** — asynchronous ORM
- **Docker + docker-compose** — containerization
- **Ruff + mypy** — linters
- **pytest + testcontainers** — testing

## Supported LLM Providers

The provider is selected via the `LLM_PROVIDER` variable in `.env`. No code changes are required.

| Provider | Default model | Where to get the key |
|-----------|---------------------|----------------|
| `groq` | `llama-3.3-70b-versatile` | [console.groq.com](https://console.groq.com) — free |
| `gemini` | `gemini-2.0-flash` | [aistudio.google.com](https://aistudio.google.com) — free |
| `ollama` | `llama3.2` | Локально, без ключей — [ollama.com](https://ollama.com) |

## Quick Start

### Requirements

- Docker + Docker Compose

### Installation

```bash
git clone https://github.com/boshka22/langchain_start
cd resume-analyzer
```

Create a `.env` file and select a provider:

```env
# ── LLM Provider ───────────────────────────────
# Choose one: groq | gemini | ollama
LLM_PROVIDER=groq
MODEL_NAME=llama-3.3-70b-versatile

# Groq (free, https://console.groq.com)
GROQ_API_KEY=your-key

# Gemini (free, https://aistudio.google.com)
# LLM_PROVIDER=gemini
# MODEL_NAME=gemini-2.0-flash
# GOOGLE_API_KEY=your-key

# Ollama (local, no keys)
# LLM_PROVIDER=ollama
# MODEL_NAME=llama3.2
# OLLAMA_BASE_URL=http://host.docker.internal:11434

# ── Infrastructure ─────────────────────────────
POSTGRES_DB=resume_analyzer
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/resume_analyzer
REDIS_URL=redis://redis:6379/0
```
Run:

```bash
docker-compose up --build
```

The API is available at [http://localhost:8000/docs](http://localhost:8000/docs)

### Ollama (local model, no API keys required)

```bash
# Install Ollama from ollama.com, then:
ollama pull llama3.2

# Set the following in .env:
# LLM_PROVIDER=ollama
# MODEL_NAME=llama3.2
```

## How asynchronous analysis works

### Without cache (first request)

```
1. POST /analyze + file
   → X-Cache: MISS
   → 202 Accepted {"task_id": "uuid", "status": "pending", "cached": false}

2. GET /analyze/{task_id}/status  →  {"status": "started", "result": null}
3. GET /analyze/{task_id}/status  →  {"status": "success", "result": {...}}
```

### With cache (repeat request for the same resume)

```
1. POST /analyze + file
   → X-Cache: HIT
   → 202 Accepted {"task_id": "cached", "status": "success", "cached": true, "result": {...}}
```

Repeat requests return the result instantly—Celery is not involved.
The cache persists for 24 hours; the cache key is the MD5 hash of the resume text.

Optionally, you can pass a `callback_url` in the request form. Once analysis is complete, the worker will automatically send a POST request containing the result to that URL.

## Endpoints

| Method | Path | Description |
|-------|------|----------|
| `POST` | `/api/v1/resume/analyze` | Start resume analysis (PDF or TXT) |
| `GET` | `/api/v1/resume/analyze/{task_id}/status` | Task status and result |
| `GET` | `/api/v1/resume/history` | Analysis history with pagination |
| `GET` | `/api/v1/resume/{id}` | Retrieve analysis by ID from the database |
| `GET` | `/api/v1/resume/{id}/export` | Export analysis to PDF |
| `GET` | `/health` | Health check |

## Response Examples

### New analysis (cache MISS)

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "cached": false,
  "result": null
}
```

### Result from cache (cache HIT)

```json
{
  "task_id": "cached",
  "status": "success",
  "cached": true,
  "result": {
    "status": "success",
    "overall_score": 8,
    "summary": "The resume demonstrates a broad tech stack and specific achievements backed by figures.",
    "criteria": {
      "skills": {
        "score": 9,
        "feedback": "Relevant tech stack; good coverage of technologies.",
        "suggestions": ["Add proficiency levels for technologies", "Specify version numbers"]
      },
"experience": {
        "score": 9,
        "feedback": "Concrete achievements with figures, good career progression.",
        "suggestions": ["Add a GitHub link", "Describe teamwork"]
      },
      "structure": {
        "score": 7,
        "feedback": "Clear structure, but contains some redundant sections.",
        "suggestions": ["Remove duplicate contact details", "Add a Summary section"]
      },
      "language": {
        "score": 8,
        "feedback": "Professional tone, strong action verbs.",
        "suggestions": ["Remove clichés", "Shorten long sentences"]
      }
    },
    "top_strengths": ["Concrete metrics and achievements", "Modern tech stack", "Career progression"],
    "top_improvements": ["Add a Summary section", "Indicate skill proficiency levels"],
    "file_name": "resume.pdf"
  }
}
```

## Project Structure

```
resume_analyzer/
├── app/
│   ├── api/
│   │   └── v1/
│   │       └── resume.py        # Routers
│   ├── cache/
│   │   └── resume.py            # Cache-Aside caching in Redis
│   ├── core/
│   │   ├── config.py            # Configuration settings
│   │   └── database.py          # Database connection
│   ├── database/
│   │   └── models.py            # SQLAlchemy models
│   ├── graph/
│   │   ├── state.py             # Graph state
│   │   ├── nodes.py             # Agent nodes + LLM factory
│   │   └── builder.py           # Graph assembly
│   ├── parsers/
│   │   └── file.py              # PDF/TXT parsing
│   ├── repositories/
│   │ └── resume.py # DB layer
│   ├── schemas/
│   │ └── v1/
│   │ └── resume.py # Pydantic schemas
│   ├── services/
│   │ └── resume.py # business logic
│   ├── tasks/
│   │ └── analyze.py # Celery task
│   ├── celery_app.py # Celery initialization
│   └── main.py # FastAPI application
├── tests/
│   ├── unit/
│   │ └── test_parsers.py
│   └── integration/
│   ├── test_api.py
│   ├── test_cache.py
│   └── test_repository.py
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
└── requirements.txt
```
## Development

### Running tests

```bash
# All tests (testcontainers will automatically spin up PostgreSQL)
pytest tests/ -v

# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v
```

### Linters

```bash
ruff check app/
ruff format app/
mypy app/
```

### Pre-commit hooks

```bash
pre-commit install
pre-commit run --all-files
```

### Checking Redis cache

```bash
# Enter Redis CLI
docker exec -it resume_analyzer_redis redis-cli

# View all cache keys
KEYS resume:analysis:*

# Check key TTL
TTL resume:analysis:<hash>
```
## Roadmap

- [x] Resume analysis via LangGraph with parallel agents
- [x] PDF and TXT support
- [x] History persistence in PostgreSQL
- [x] Clean architecture (api / services / graph / repositories)
- [x] Celery + Redis — background processing, status polling
- [x] Webhook notifications (callback_url)
- [x] Support for multiple LLM providers (Groq, Gemini, Ollama)
- [x] Result caching via Redis (Cache-Aside, 24h TTL)
- [x] Docker + docker-compose
- [x] Linters (ruff, mypy) and pre-commit hooks
- [x] Tests using Testcontainers
- [x] PDF report export
- [ ] Authentication (JWT)
- [ ] Resume vs. job description comparison
- [ ] LangSmith for agent monitoring
- [ ] Kubernetes deployment
