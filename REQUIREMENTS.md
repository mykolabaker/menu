# Requirements Specification: Vegetarian Menu Analyzer

## 1. Overview

### 1.1 Purpose
Develop a service that takes one or more photos of a restaurant menu as input and returns the total sum of all vegetarian dishes. The solution must use open-source technologies and standard best practices for building AI-driven systems.

### 1.2 Scope
The system consists of two microservices:
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

**Input:**
- 1 to 5 menu photos (multipart/form-data or base64)

**Output (JSON):**
```json
{
  "vegetarian_items": [
    {"name": "Greek Salad", "price": 7.5},
    {"name": "Veggie Burger", "price": 9.0}
  ],
  "total_sum": 16.5
}
```

#### 2.1.2 Endpoint: POST /review (Optional - HITL)

| Property | Specification |
|----------|---------------|
| Method | POST |
| Path | `/review` |
| Content-Type | `application/json` |

- Accept corrections for uncertain items
- Recompute deterministically based on corrections

---

### 2.2 OCR Processing

- Use an open-source OCR engine (e.g., Tesseract OCR or equivalent)
- Extract text from the menu, including dish names and prices

---

### 2.3 Data Structuring

- Transform the raw OCR text into a structured format

---

### 2.4 Vegetarian Classification

#### 2.4.1 LLM-Based Classification (Primary)
- Use an LLM for dish classification

#### 2.4.2 Keyword Dictionary Fallback (Secondary)
- Use a keyword dictionary (`vegetarian`, `veggie`, `salad`, `tofu`, etc.) as a fallback classification method

#### 2.4.3 Semantic Search (Optional)
- For a more advanced solution, implement a semantic search against a pre-defined database of vegetarian dishes to improve the classification accuracy of non-obvious items

---

### 2.5 MCP Server

- **Calculation**: Identify all vegetarian dishes and sum their prices
- Deploy the MCP server as a standalone service (HTTP/WebSocket)
- The REST API must not perform calculations directly; instead, it should call the MCP server via tool-calling
- The MCP server returns the result, and the REST API returns it to the client

---

### 2.6 RAG Memory

- Use a local, open-source vector index (ingredients & dishes)
- Retrieve top-k evidence during classification via the MCP server
- Combine retrieval with the existing keyword fallback
- Return confidence + brief reasoning notes in the JSON

---

### 2.7 Observability

- Use Langsmith to implement structured logs and cross-service tracing with a `request_id`
- Capture: OCR, parsing, MCP tool-calls, retrieval hits, token/latency stats, and the final decision

---

### 2.8 HITL Loop (Optional)

- If combined confidence is below the threshold, return an **uncertainty card** (JSON) instead of a verdict, listing suspect items with evidence
- Accept corrections via `POST /review`
- Recompute deterministically

---

## 3. Non-Functional Requirements

- Code must be written in **Python** or **JavaScript**
- Architecture must be split into separate components:
  - OCR + parsing inside the REST API
  - Calculation logic delegated to the MCP server
- Services must communicate over the network (e.g., REST API → HTTP request → MCP)
- The entire system must be runnable via Docker (2 microservices: API and MCP)

---

## 4. Deliverables

### 4.1 Code
- Git monorepo with backend and MCP code

### 4.2 Infrastructure
- Docker setup (`docker-compose.yml`) to start the system locally with multiple instances

### 4.3 Documentation
- README including:
  - Instructions for running the system
  - Architecture and design choices
  - Testing approach
