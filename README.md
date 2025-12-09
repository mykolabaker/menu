# Vegetarian Menu Analyzer

A microservices-based system that processes restaurant menu photos, extracts dish information using OCR, classifies vegetarian dishes using AI/ML techniques, and returns the total sum of all vegetarian items.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                           Client                                      │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                │ POST /process-menu (1-5 images)
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        REST API Service                               │
│  ┌────────────┐  ┌──────────┐  ┌──────────┐  ┌─────────────────┐    │
│  │   Image    │→ │   OCR    │→ │   Text   │→ │   MCP Client    │    │
│  │ Validator  │  │(Tesseract)│ │  Parser  │  │                 │    │
│  └────────────┘  └──────────┘  └──────────┘  └─────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                │ HTTP
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         MCP Server                                    │
│  ┌────────────┐  ┌──────────┐  ┌──────────┐  ┌─────────────────┐    │
│  │    RAG     │→ │   LLM    │→ │ Keywords │→ │   Calculator    │    │
│  │ (ChromaDB) │  │ (Ollama) │  │ Fallback │  │                 │    │
│  └────────────┘  └──────────┘  └──────────┘  └─────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

## Features

- **Image Processing**: Accepts 1-5 menu images (JPEG, PNG, WebP, TIFF)
- **OCR**: Text extraction using Tesseract with image preprocessing
- **AI Classification**: Multi-tier classification using:
  - RAG (Retrieval Augmented Generation) with ChromaDB
  - LLM classification with Ollama (Llama3/Mistral)
  - Keyword-based fallback
- **HITL Loop**: Human-in-the-loop review for uncertain classifications
- **Observability**: Structured JSON logging with request ID propagation

## Quick Start

### Prerequisites

- Docker and Docker Compose
- 8GB+ RAM (for Ollama)

### Running with Docker

1. Clone the repository and navigate to the project directory:
```bash
cd /path/to/menu
```

2. Copy environment template:
```bash
cp .env.example .env
```

3. Start all services:
```bash
docker-compose up -d
```

4. Pull the Ollama model (first time only):
```bash
docker exec -it menu-ollama-1 ollama pull llama3
```

5. Wait for services to be healthy:
```bash
docker-compose ps
```

The API will be available at `http://localhost:8000`

### API Usage

#### Process Menu Images

**Multipart Form Upload:**
```bash
curl -X POST http://localhost:8000/process-menu \
  -F "images=@menu1.jpg" \
  -F "images=@menu2.jpg"
```

**Base64 JSON:**
```bash
curl -X POST http://localhost:8000/process-menu-base64 \
  -H "Content-Type: application/json" \
  -d '{"images": ["'$(base64 -w0 menu1.jpg)'"]}'
```

**Response:**
```json
{
  "vegetarian_items": [
    {"name": "Greek Salad", "price": 7.50},
    {"name": "Veggie Burger", "price": 9.00}
  ],
  "total_sum": 16.50
}
```

#### Submit HITL Corrections

When items have low confidence, the API returns a `needs_review` response:
```json
{
  "status": "needs_review",
  "request_id": "abc-123",
  "confident_items": [...],
  "uncertain_items": [
    {
      "name": "Mushroom Risotto",
      "price": 14.00,
      "confidence": 0.55,
      "evidence": ["May contain chicken stock"]
    }
  ],
  "partial_sum": 7.50
}
```

Submit corrections:
```bash
curl -X POST http://localhost:8000/review \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "abc-123",
    "corrections": [
      {"name": "Mushroom Risotto", "is_vegetarian": true}
    ]
  }'
```

#### Health Check

```bash
curl http://localhost:8000/health
```

## Configuration

### Environment Variables

| Variable | Service | Description | Default |
|----------|---------|-------------|---------|
| `MCP_SERVER_URL` | API | URL of MCP server | `http://mcp:8001` |
| `OLLAMA_BASE_URL` | MCP | Ollama server URL | `http://ollama:11434` |
| `LLM_MODEL` | MCP | Ollama model name | `llama3` |
| `CONFIDENCE_THRESHOLD` | MCP | HITL threshold (0-1) | `0.7` |
| `LOG_LEVEL` | Both | Logging level | `INFO` |
| `LANGSMITH_API_KEY` | Both | Optional Langsmith key | - |

## Development

### Local Development Setup

**API Service:**
```bash
cd api
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**MCP Server:**
```bash
cd mcp
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

**Start Ollama locally:**
```bash
ollama serve
ollama pull llama3
```

### Running Tests

**API Tests:**
```bash
cd api
pytest tests/ -v
```

**MCP Tests:**
```bash
cd mcp
pytest tests/ -v
```

## API Documentation

Interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

MCP Server documentation:
- Swagger UI: `http://localhost:8001/docs`

## Project Structure

```
menu/
├── docker-compose.yml
├── .env.example
├── README.md
├── api/                      # REST API Service
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── routers/         # API endpoints
│   │   ├── services/        # Business logic
│   │   ├── models/          # Pydantic models
│   │   ├── middleware/      # Request ID, logging
│   │   └── utils/           # Validators, exceptions
│   └── tests/
└── mcp/                      # MCP Server
    ├── Dockerfile
    ├── requirements.txt
    ├── app/
    │   ├── main.py
    │   ├── config.py
    │   ├── tools/           # MCP tool implementations
    │   ├── services/        # Classification services
    │   ├── models/          # Pydantic models
    │   └── knowledge_base/  # RAG seed data
    └── tests/
```

## Design Decisions

1. **FastAPI for both services**: Unified Python stack with async support and automatic OpenAPI docs.

2. **HTTP for MCP communication**: Simpler than WebSocket, sufficient for this use case.

3. **Three-tier classification**: Combines RAG evidence, LLM reasoning, and keyword matching for robust results.

4. **ChromaDB for vector store**: Pure Python, easy setup, sufficient for the knowledge base size.

5. **Ollama for local LLM**: No API costs, fully offline capable, easy Docker integration.

6. **In-memory review store**: Simple for MVP, can migrate to Redis/database for production.

## Known Limitations

### HITL Review Store

The current implementation uses an in-memory store for pending HITL reviews. This has important implications:

- **Single API instance required**: The API service must run as a single instance to ensure review requests are routed to the same process that stored the pending review. The docker-compose.yml is configured accordingly.
- **No persistence**: Pending reviews are lost on API restart. For production, consider:
  - Using Redis for shared state across instances
  - Using a database (PostgreSQL, MongoDB) for persistence
  - Implementing sticky sessions if using multiple API instances

### Parallel Classification

Menu items are classified in parallel using a thread pool (4 workers). For very large menus (50+ items), consider:
- Increasing the thread pool size via configuration
- Implementing request queuing for burst protection
- Adding rate limiting for LLM calls

## Error Handling

| Status Code | Condition |
|-------------|-----------|
| 400 | Invalid input (no images, >5 images, invalid format) |
| 422 | OCR failed to extract readable text |
| 500 | Internal server error |
| 503 | MCP server unavailable |

## License

MIT
