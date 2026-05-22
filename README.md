# Search Gateway

LLM Web Search Gateway for mainland China network environments.

## Overview

Search Gateway sits between LLM/Agent clients and search backends (SearXNG), providing:

- Search quality control and result structuring
- Failure isolation (single engine failure does not break the request)
- Partial results support
- Query classification and rule-based expansion
- Engine routing with cooldown management
- URL deduplication and source scoring
- Redis caching

## Architecture

```
LLM / Agent / MCP Client
        |
        v
Search Gateway (FastAPI)
        |
        +---> SearXNG
                |
                +---> Bing / 360 / Sogou / Quark / Baidu
                +---> GitHub / StackOverflow / PyPI / NPM
                +---> arXiv / Crossref / OpenAlex
```

## Deployment

### Prerequisites

- Docker Desktop (Windows/Mac/Linux)
- Docker Compose v2+

### Windows (PowerShell)

```powershell
# 1. Navigate to project directory
cd D:\miroconsumer\MiroConsumer\search-gateway

# 2. Run deployment script
.\deploy.ps1

# Or manually:
docker compose up --build -d
```

### Linux / macOS

```bash
cd search-gateway
docker compose up --build -d
```

### Verify Deployment

```bash
# Health check
curl http://localhost:8011/health

# Ready check (includes Redis + SearXNG status)
curl http://localhost:8011/ready

# Engine status
curl http://localhost:8011/v1/engines/status
```

### Services

| Service | URL | Description |
|---------|-----|-------------|
| Search Gateway | http://localhost:8011 | FastAPI Gateway |
| SearXNG | http://localhost:8080 | Search backend |
| Redis | localhost:6379 | Cache & cooldown |

### Stop

```bash
docker compose down
```

## SearXNG Engine Configuration

Default enabled engines in `searxng/settings.yml`:
- `bing`
- `baidu`
- `duckduckgo`
- `github`
- `stackoverflow`
- `arxiv`
- `yandex`
- `google`
- `wikipedia`

To add more engines (e.g., sogou, 360search, quark), edit `searxng/settings.yml` and restart:

```bash
docker compose restart searxng
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/ready` | Readiness probe |
| POST | `/v1/search` | Search |
| GET | `/v1/engines/status` | Engine status |

### Search Example

```bash
curl -X POST http://localhost:8011/v1/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "LangGraph checkpointer 报错怎么解决",
    "profile": "auto",
    "limit": 10
  }'
```

## Configuration

Edit `config.yml` to customize profiles, timeouts, and scoring weights.

Key sections:
- `profiles`: Engine routing per query type
- `cooldown`: Engine failure cooldown durations
- `scoring`: Result ranking weights
- `dedup`: Deduplication thresholds

## Development

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pytest
```

## Project Structure

```
search-gateway/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── schemas.py
│   ├── routers/
│   │   ├── health.py
│   │   └── search.py
│   ├── services/
│   │   ├── searxng_client.py
│   │   ├── cache.py
│   │   ├── classifier.py
│   │   ├── query_expander.py
│   │   ├── engine_router.py
│   │   ├── cooldown.py
│   │   ├── dedup.py
│   │   ├── ranker.py
│   │   ├── source_classifier.py
│   │   └── metrics.py
│   ├── rules/
│   │   ├── domain_boost.yml
│   │   ├── content_farm.yml
│   │   ├── tech_keywords.yml
│   │   └── official_domains.yml
│   └── utils/
│       ├── url.py
│       └── text.py
├── tests/
├── searxng/
│   └── settings.yml
├── docker-compose.yml
├── Dockerfile
├── deploy.ps1
├── config.yml
├── requirements.txt
└── README.md
```
