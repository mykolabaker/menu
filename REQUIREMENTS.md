# Requirements Specification: Vegetarian Menu Analyzer

## 1. Overview

### 1.1 Purpose
Develop a microservices-based system that processes restaurant menu photos, extracts dish information using OCR, classifies vegetarian dishes using AI/ML techniques, and returns the total sum of all vegetarian items.

### 1.2 Scope
The system consists of two primary microservices:
- **REST API Service**: Handles image upload, OCR processing, and text parsing
- **MCP Server**: Performs vegetarian classification and price calculation

### 1.3 Technology Constraints
- **Language**: Python or JavaScript
- **Infrastructure**: Docker with docker-compose
- **AI/ML**: Open-source technologies only

---

## 2. Functional Requirements

### 2.1 REST API Service

#### 2.1.1 Endpoint: POST /process-menu

| Property | Specification |
|----------|---------------|
| Method | POST |
| Path | `/process-menu` |
| Content-Type | `multipart/form-data` or `application/json` (base64) |

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| images | File[] or String[] | Yes | 1-5 menu photos (multipart files or base64-encoded strings) |

**Input Validation Rules:**
- FR-2.1.1.1: Accept minimum 1 image, maximum 5 images
- FR-2.1.1.2: Support common image formats (JPEG, PNG, WebP, TIFF)
- FR-2.1.1.3: Reject requests with 0 images or more than 5 images
- FR-2.1.1.4: Validate image file integrity before processing

**Success Response (200 OK):**
```json
{
  "vegetarian_items": [
    {
      "name": "Greek Salad",
      "price": 7.5
    },
    {
      "name": "Veggie Burger",
      "price": 9.0
    }
  ],
  "total_sum": 16.5
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| vegetarian_items | Array<Object> | List of identified vegetarian dishes |
| vegetarian_items[].name | String | Name of the dish |
| vegetarian_items[].price | Number | Price of the dish (float, 2 decimal precision) |
| total_sum | Number | Sum of all vegetarian dish prices |

**Error Responses:**

| Status Code | Condition |
|-------------|-----------|
| 400 Bad Request | Invalid input (no images, >5 images, invalid format) |
| 422 Unprocessable Entity | OCR failed to extract readable text |
| 500 Internal Server Error | System error |
| 503 Service Unavailable | MCP server unreachable |

#### 2.1.2 Endpoint: POST /review (Optional - HITL)

| Property | Specification |
|----------|---------------|
| Method | POST |
| Path | `/review` |
| Content-Type | `application/json` |

**Request Body:**
```json
{
  "request_id": "uuid-string",
  "corrections": [
    {
      "name": "Mushroom Risotto",
      "is_vegetarian": true
    }
  ]
}
```

**Response:**
- Recomputes the result deterministically based on corrections
- Returns updated vegetarian items and total sum

---

### 2.2 OCR Processing

#### 2.2.1 OCR Engine Requirements
- FR-2.2.1.1: Use open-source OCR engine (Tesseract OCR recommended)
- FR-2.2.1.2: Support multiple languages (at minimum: English)
- FR-2.2.1.3: Handle various image qualities and orientations

#### 2.2.2 Text Extraction Requirements
- FR-2.2.2.1: Extract dish names from menu images
- FR-2.2.2.2: Extract prices associated with each dish
- FR-2.2.2.3: Handle various price formats ($9.99, 9.99, $9, etc.)
- FR-2.2.2.4: Process multiple images and merge results

#### 2.2.3 Image Preprocessing
- FR-2.2.3.1: Apply image preprocessing to improve OCR accuracy
  - Grayscale conversion
  - Noise reduction
  - Contrast enhancement
  - Deskewing (rotation correction)

---

### 2.3 Data Structuring

#### 2.3.1 Menu Item Parsing
- FR-2.3.1.1: Transform raw OCR text into structured menu items
- FR-2.3.1.2: Associate dish names with their corresponding prices
- FR-2.3.1.3: Handle menu sections/categories if present
- FR-2.3.1.4: Remove duplicates across multiple images

**Structured Format:**
```json
{
  "menu_items": [
    {
      "name": "Greek Salad",
      "price": 7.50,
      "description": "Fresh vegetables with feta cheese",
      "category": "Salads"
    }
  ]
}
```

---

### 2.4 Vegetarian Classification

#### 2.4.1 LLM-Based Classification (Primary)
- FR-2.4.1.1: Use an open-source LLM for dish classification
- FR-2.4.1.2: Classify each dish as vegetarian or non-vegetarian
- FR-2.4.1.3: Generate confidence score (0.0 - 1.0) for each classification
- FR-2.4.1.4: Provide reasoning/justification for classification decisions

**Recommended Open-Source LLMs:**
- Llama 2/3 (Meta)
- Mistral
- Phi-2/3 (Microsoft)
- Gemma (Google)

#### 2.4.2 Keyword Dictionary Fallback (Secondary)
- FR-2.4.2.1: Maintain a dictionary of vegetarian keywords
- FR-2.4.2.2: Use keyword matching as fallback when LLM is unavailable or uncertain

**Minimum Keyword Dictionary:**
```
Positive indicators (vegetarian):
- vegetarian, veggie, vegan, plant-based
- salad, tofu, tempeh, seitan
- paneer, cheese, mushroom, vegetable
- beans, lentils, chickpea, hummus
- pasta (without meat keywords)

Negative indicators (non-vegetarian):
- chicken, beef, pork, lamb, fish
- salmon, tuna, shrimp, seafood
- bacon, ham, steak, meat
- duck, turkey, veal
```

#### 2.4.3 Semantic Search / RAG (Optional Enhancement)
- FR-2.4.3.1: Implement vector database with pre-defined vegetarian dishes
- FR-2.4.3.2: Use embedding model for semantic similarity search
- FR-2.4.3.3: Retrieve top-k similar dishes for classification evidence
- FR-2.4.3.4: Combine retrieval results with keyword and LLM classification

---

### 2.5 MCP Server

#### 2.5.1 Server Requirements
- FR-2.5.1.1: Deploy as standalone HTTP/WebSocket service
- FR-2.5.1.2: Expose tool-calling interface for REST API
- FR-2.5.1.3: Handle concurrent requests

#### 2.5.2 Tool: classify_and_calculate

**Input:**
```json
{
  "menu_items": [
    {
      "name": "Greek Salad",
      "price": 7.50
    },
    {
      "name": "Grilled Chicken",
      "price": 12.00
    }
  ],
  "request_id": "uuid-string"
}
```

**Output:**
```json
{
  "vegetarian_items": [
    {
      "name": "Greek Salad",
      "price": 7.50,
      "confidence": 0.95,
      "reasoning": "Contains vegetables and feta cheese, no meat ingredients"
    }
  ],
  "total_sum": 7.50,
  "classification_method": "llm+rag",
  "request_id": "uuid-string"
}
```

#### 2.5.3 MCP Server Responsibilities
- FR-2.5.3.1: Receive structured menu items from REST API
- FR-2.5.3.2: Execute vegetarian classification logic
- FR-2.5.3.3: Perform RAG retrieval for classification evidence
- FR-2.5.3.4: Calculate total sum of vegetarian items
- FR-2.5.3.5: Return results with confidence scores and reasoning

---

### 2.6 RAG Memory System

#### 2.6.1 Vector Index Requirements
- FR-2.6.1.1: Use local, open-source vector database
- FR-2.6.1.2: Index ingredients and dish names
- FR-2.6.1.3: Support semantic similarity search

**Recommended Vector Databases:**
- ChromaDB
- Qdrant
- FAISS
- Milvus Lite

#### 2.6.2 Retrieval Process
- FR-2.6.2.1: Retrieve top-k (k=5 recommended) evidence items for each dish
- FR-2.6.2.2: Combine retrieval score with LLM confidence
- FR-2.6.2.3: Return evidence in classification reasoning

#### 2.6.3 Knowledge Base Content
- FR-2.6.3.1: Pre-populate with known vegetarian dishes
- FR-2.6.3.2: Include common ingredients classification
- FR-2.6.3.3: Support knowledge base updates/expansion

---

### 2.7 Observability

#### 2.7.1 Langsmith Integration
- FR-2.7.1.1: Integrate Langsmith for LLM observability
- FR-2.7.1.2: Track all LLM calls with inputs/outputs
- FR-2.7.1.3: Monitor token usage and latency

#### 2.7.2 Structured Logging
- FR-2.7.2.1: Generate unique `request_id` for each request
- FR-2.7.2.2: Propagate `request_id` across all service calls
- FR-2.7.2.3: Log with structured JSON format

**Required Log Events:**

| Event | Service | Data |
|-------|---------|------|
| request_received | REST API | request_id, image_count, timestamp |
| ocr_started | REST API | request_id, image_index |
| ocr_completed | REST API | request_id, extracted_text_length, duration_ms |
| parsing_completed | REST API | request_id, items_count, duration_ms |
| mcp_call_started | REST API | request_id, tool_name |
| mcp_call_completed | REST API | request_id, duration_ms |
| classification_started | MCP | request_id, items_count |
| llm_call | MCP | request_id, model, tokens_in, tokens_out, duration_ms |
| rag_retrieval | MCP | request_id, query, hits_count, duration_ms |
| classification_completed | MCP | request_id, vegetarian_count, total_sum |

#### 2.7.3 Cross-Service Tracing
- FR-2.7.3.1: Implement distributed tracing
- FR-2.7.3.2: Correlate logs across REST API and MCP server
- FR-2.7.3.3: Track end-to-end request latency

---

### 2.8 HITL Loop (Optional)

#### 2.8.1 Uncertainty Handling
- FR-2.8.1.1: Define confidence threshold (recommended: 0.7)
- FR-2.8.1.2: Flag items below threshold as uncertain
- FR-2.8.1.3: Return uncertainty card instead of final verdict when applicable

**Uncertainty Card Response:**
```json
{
  "status": "needs_review",
  "request_id": "uuid-string",
  "confident_items": [
    {"name": "Greek Salad", "price": 7.50, "confidence": 0.95}
  ],
  "uncertain_items": [
    {
      "name": "Mushroom Risotto",
      "price": 14.00,
      "confidence": 0.55,
      "evidence": ["Contains mushrooms (vegetarian)", "May contain chicken stock (uncertain)"]
    }
  ],
  "partial_sum": 7.50
}
```

#### 2.8.2 Correction Endpoint
- FR-2.8.2.1: Accept corrections via POST /review
- FR-2.8.2.2: Store corrections for request_id
- FR-2.8.2.3: Recompute deterministically using corrections
- FR-2.8.2.4: Return final result

---

## 3. Non-Functional Requirements

### 3.1 Performance

| Metric | Requirement |
|--------|-------------|
| NFR-3.1.1 | Response time < 30 seconds for 5 images |
| NFR-3.1.2 | OCR processing < 5 seconds per image |
| NFR-3.1.3 | MCP classification < 10 seconds for 50 items |
| NFR-3.1.4 | Support concurrent requests (minimum 10) |

### 3.2 Scalability
- NFR-3.2.1: Services must be horizontally scalable
- NFR-3.2.2: Support multiple instances via docker-compose
- NFR-3.2.3: Stateless REST API design

### 3.3 Reliability
- NFR-3.3.1: Graceful degradation when MCP server unavailable
- NFR-3.3.2: Retry logic for transient failures
- NFR-3.3.3: Health check endpoints for both services

### 3.4 Security
- NFR-3.4.1: Input validation for all endpoints
- NFR-3.4.2: File size limits for uploaded images (max 10MB per image)
- NFR-3.4.3: Rate limiting (optional)
- NFR-3.4.4: No sensitive data in logs

### 3.5 Maintainability
- NFR-3.5.1: Code documentation
- NFR-3.5.2: Modular architecture
- NFR-3.5.3: Configuration via environment variables

---

## 4. Architecture

### 4.1 System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Client Application                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       │ POST /process-menu
                                       │ (1-5 images)
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           REST API Service                                   │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────┐  ┌──────────────────┐  │
│  │   Image     │  │     OCR      │  │    Text     │  │   MCP Client     │  │
│  │  Validator  │──│   (Tesseract)│──│   Parser    │──│  (Tool Caller)   │  │
│  └─────────────┘  └──────────────┘  └─────────────┘  └──────────────────┘  │
│                                                              │              │
│                         Langsmith Tracing                    │              │
└─────────────────────────────────────────────────────────────┼──────────────┘
                                                               │
                                                               │ HTTP/WebSocket
                                                               │ Tool Call
                                                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                             MCP Server                                       │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────┐  ┌──────────────────┐  │
│  │   Tool      │  │     LLM      │  │    RAG      │  │   Calculator     │  │
│  │  Handler    │──│  Classifier  │──│  Retriever  │──│                  │  │
│  └─────────────┘  └──────────────┘  └─────────────┘  └──────────────────┘  │
│                          │                 │                                │
│                          ▼                 ▼                                │
│                   ┌─────────────┐  ┌──────────────┐                        │
│                   │  Open-Source│  │   Vector DB   │                        │
│                   │     LLM     │  │  (ChromaDB)   │                        │
│                   └─────────────┘  └──────────────┘                        │
│                                                                             │
│                         Langsmith Tracing                                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Component Responsibilities

| Component | Service | Responsibilities |
|-----------|---------|------------------|
| Image Validator | REST API | Validate image count, format, size |
| OCR Engine | REST API | Extract text from menu images |
| Text Parser | REST API | Structure extracted text into menu items |
| MCP Client | REST API | Call MCP server tools |
| Tool Handler | MCP | Route incoming tool calls |
| LLM Classifier | MCP | Classify dishes using LLM |
| RAG Retriever | MCP | Semantic search for evidence |
| Calculator | MCP | Sum vegetarian item prices |

### 4.3 Data Flow

1. Client uploads 1-5 menu images to REST API
2. REST API validates images
3. REST API processes each image through OCR
4. REST API parses OCR text into structured menu items
5. REST API calls MCP server with menu items
6. MCP server classifies each item (LLM + RAG + Keywords)
7. MCP server calculates total sum
8. MCP server returns results to REST API
9. REST API returns JSON response to client

---

## 5. API Specifications

### 5.1 REST API OpenAPI Specification

```yaml
openapi: 3.0.3
info:
  title: Vegetarian Menu Analyzer API
  version: 1.0.0
  description: API for processing restaurant menu photos and identifying vegetarian dishes

paths:
  /process-menu:
    post:
      summary: Process menu images and identify vegetarian dishes
      requestBody:
        required: true
        content:
          multipart/form-data:
            schema:
              type: object
              properties:
                images:
                  type: array
                  items:
                    type: string
                    format: binary
                  minItems: 1
                  maxItems: 5
          application/json:
            schema:
              type: object
              properties:
                images:
                  type: array
                  items:
                    type: string
                    description: Base64-encoded image
                  minItems: 1
                  maxItems: 5
      responses:
        '200':
          description: Successfully processed menu
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ProcessMenuResponse'
        '400':
          description: Invalid input
        '422':
          description: OCR processing failed
        '500':
          description: Internal server error
        '503':
          description: MCP server unavailable

  /review:
    post:
      summary: Submit corrections for uncertain items (HITL)
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ReviewRequest'
      responses:
        '200':
          description: Successfully recomputed results
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ProcessMenuResponse'

  /health:
    get:
      summary: Health check endpoint
      responses:
        '200':
          description: Service is healthy

components:
  schemas:
    ProcessMenuResponse:
      type: object
      properties:
        vegetarian_items:
          type: array
          items:
            $ref: '#/components/schemas/VegetarianItem'
        total_sum:
          type: number
          format: float

    VegetarianItem:
      type: object
      properties:
        name:
          type: string
        price:
          type: number
          format: float

    ReviewRequest:
      type: object
      properties:
        request_id:
          type: string
          format: uuid
        corrections:
          type: array
          items:
            type: object
            properties:
              name:
                type: string
              is_vegetarian:
                type: boolean
```

### 5.2 MCP Tool Specification

```json
{
  "name": "classify_and_calculate",
  "description": "Classify menu items as vegetarian/non-vegetarian and calculate total sum",
  "input_schema": {
    "type": "object",
    "properties": {
      "menu_items": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "name": { "type": "string" },
            "price": { "type": "number" },
            "description": { "type": "string" }
          },
          "required": ["name", "price"]
        }
      },
      "request_id": { "type": "string" }
    },
    "required": ["menu_items", "request_id"]
  }
}
```

---

## 6. Infrastructure Requirements

### 6.1 Docker Configuration

**Required Services:**
- `api` - REST API service
- `mcp` - MCP server

**docker-compose.yml structure:**
```yaml
version: '3.8'
services:
  api:
    build: ./api
    ports:
      - "8000:8000"
    environment:
      - MCP_SERVER_URL=http://mcp:8001
      - LANGSMITH_API_KEY=${LANGSMITH_API_KEY}
    depends_on:
      - mcp
    deploy:
      replicas: 2

  mcp:
    build: ./mcp
    ports:
      - "8001:8001"
    environment:
      - LLM_MODEL=${LLM_MODEL}
      - LANGSMITH_API_KEY=${LANGSMITH_API_KEY}
    volumes:
      - vector_db_data:/app/data
    deploy:
      replicas: 2

volumes:
  vector_db_data:
```

### 6.2 Environment Variables

| Variable | Service | Description | Required |
|----------|---------|-------------|----------|
| MCP_SERVER_URL | API | URL of MCP server | Yes |
| LANGSMITH_API_KEY | Both | Langsmith API key for tracing | Yes |
| LLM_MODEL | MCP | Open-source LLM model name | Yes |
| LOG_LEVEL | Both | Logging level (DEBUG/INFO/WARN/ERROR) | No |
| CONFIDENCE_THRESHOLD | MCP | Threshold for HITL uncertainty | No |

---

## 7. Testing Requirements

### 7.1 Unit Tests
- Test OCR text extraction with sample images
- Test text parser with various menu formats
- Test vegetarian classification logic
- Test price calculation accuracy

### 7.2 Integration Tests
- Test REST API → MCP server communication
- Test end-to-end flow with real images
- Test error handling and edge cases

### 7.3 Test Scenarios

| ID | Scenario | Expected Result |
|----|----------|-----------------|
| T-001 | Single image with clear text | Extract all items, classify correctly |
| T-002 | Multiple images (5) | Merge items, no duplicates |
| T-003 | Blurry/low-quality image | Graceful degradation or error |
| T-004 | Menu with no vegetarian items | Return empty list, total_sum: 0 |
| T-005 | Menu with all vegetarian items | Return all items |
| T-006 | Mixed menu | Correctly separate vegetarian items |
| T-007 | Invalid image format | Return 400 error |
| T-008 | More than 5 images | Return 400 error |
| T-009 | MCP server unavailable | Return 503 error |
| T-010 | Ambiguous dish names | Use RAG + keyword fallback |

---

## 8. Deliverables Checklist

### 8.1 Code
- [ ] REST API service with OCR and parsing
- [ ] MCP server with classification logic
- [ ] RAG/vector database integration
- [ ] Langsmith observability integration
- [ ] HITL loop implementation (optional)

### 8.2 Infrastructure
- [ ] Dockerfile for REST API
- [ ] Dockerfile for MCP server
- [ ] docker-compose.yml with multi-instance support
- [ ] Environment configuration templates

### 8.3 Documentation
- [ ] README.md with:
  - [ ] System overview
  - [ ] Installation instructions
  - [ ] Running instructions
  - [ ] Architecture diagram
  - [ ] Design decisions documentation
  - [ ] Testing approach
  - [ ] API documentation

### 8.4 Tests
- [ ] Unit tests for core components
- [ ] Integration tests
- [ ] Sample test images

---

## 9. Glossary

| Term | Definition |
|------|------------|
| OCR | Optical Character Recognition - technology to extract text from images |
| MCP | Model Context Protocol - protocol for AI model tool calling |
| LLM | Large Language Model - AI model for text understanding and generation |
| RAG | Retrieval Augmented Generation - technique combining retrieval with generation |
| HITL | Human-in-the-Loop - system design pattern involving human review |
| Vector Database | Database optimized for storing and querying embedding vectors |

---

## 10. Revision History

| Version | Date | Description |
|---------|------|-------------|
| 1.0 | 2024-XX-XX | Initial requirements document |
