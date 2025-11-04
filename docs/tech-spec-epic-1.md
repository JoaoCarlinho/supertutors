# Epic Technical Specification: Foundation & Infrastructure Setup

Date: 2025-11-03
Author: caiojoao
Epic ID: 1
Status: Draft

---

## Overview

Epic 1 establishes the foundational technical infrastructure for the SuperTutors platform, creating the development environment and deployment pipeline that will support all subsequent feature development. This epic delivers a fully operational full-stack application skeleton comprising a React TypeScript frontend (Vite + Tailwind CSS v4.0), Python Flask backend (with WebSocket support), PostgreSQL database for conversation persistence, Redis caching layer, and integrated Ollama LLM for AI-powered Socratic tutoring. The epic concludes with automated Railway deployment and comprehensive error handling/logging infrastructure.

This foundation enables the core technical capabilities required by the PRD: real-time chat communication, conversation persistence, LLM integration for Socratic dialogue, and multimodal input processing. All 7 stories in this epic deliver vertically-sliced functionality that can be tested end-to-end, ensuring the platform is deployment-ready from Story 1.6 onwards.

## Objectives and Scope

**In Scope:**
- React 18.3.1 + Vite 6.x + TypeScript 5.7.x frontend initialization with shadcn/ui and Tailwind CSS v4.0
- Flask 3.1.2 backend API with Flask-SocketIO for WebSocket support, CORS configuration, and health check endpoints
- PostgreSQL 18 database with SQLAlchemy ORM, Alembic migrations, and initial schema (conversations, messages tables)
- Redis 7.4 caching infrastructure with connection pooling and basic cache operations
- Ollama LLM integration with Llama 3.2 Vision model, service abstraction layer, and timeout/error handling
- Railway deployment configuration with automated build/deploy pipeline, environment variables, and health checks
- Comprehensive error handling (frontend error boundaries, backend global error handler) and structured logging

**Out of Scope:**
- UI component development (deferred to Epic 2: Core Chat Interface)
- Socratic Guard service implementation (deferred to Epic 3: Socratic Tutoring Engine)
- SymPy integration for mathematical computation (deferred to Epic 4: Mathematical Computation)
- Canvas drawing functionality (deferred to Epic 5: Multimodal Problem Input)
- Celebration system (deferred to Epic 6: Celebration & Motivation)
- WCAG accessibility compliance implementation (deferred to Epic 7: Accessibility & Responsive Polish)
- Production LLM hosting (Modal/Replicate/RunPod) - Epic 1 uses local Ollama only
- User authentication/authorization - MVP is single-user development environment

## System Architecture Alignment

This epic directly implements the **Project Structure** and **Technology Stack Details** defined in the Architecture document. The frontend follows the prescribed mono-repo structure with `frontend/` containing Vite-initialized React app, while the backend uses the specified `backend/` Flask structure with blueprints, services, and ORM models.

**Key Architecture Alignments:**
- **ADR-001 (Vite):** Story 1.1 initializes Vite for fast HMR (Hot Module Replacement), critical for rapid canvas/celebration development in future epics
- **ADR-002 (Kea):** State management library installed in Story 1.1, ready for conversationLogic, canvasLogic, celebrationLogic in subsequent epics
- **ADR-003 (SymPy):** Backend dependency installed in Story 1.2, service implementation deferred to Epic 4
- **ADR-004 (Flask-SocketIO):** Story 1.2 configures WebSocket support for real-time chat (Epic 2)
- **ADR-005 (Railway):** Story 1.6 implements Railway deployment with managed PostgreSQL + Redis
- **ADR-006 (Tailwind v4.0):** Story 1.1 configures latest Tailwind for 5x faster builds

**Infrastructure Services:**
- Frontend service: Vite dev server (local), static build hosted on Railway (production)
- Backend service: Flask API with gunicorn + eventlet workers for WebSocket support
- Database service: PostgreSQL 18 managed by Railway (connection pooling, automated backups)
- Cache service: Redis 7.4 managed by Railway (pub/sub for WebSocket, LLM response caching)

**Non-Functional Constraints:**
- Response time <2s for text-based questions (established by health check endpoints in Story 1.2, 1.7)
- Error handling ensures zero crashes during LLM failures (Story 1.7 graceful degradation)
- Logging infrastructure supports debugging and future observability (Story 1.7)

## Detailed Design

### Services and Modules

| Service/Module | Responsibility | Inputs | Outputs | Owner/Story |
|----------------|---------------|--------|---------|-------------|
| **Frontend (React/Vite)** | UI rendering, user interactions, state management | User input, WebSocket events | HTTP requests, WebSocket messages | Story 1.1 |
| **Flask API** | Request routing, business logic orchestration | HTTP requests, WebSocket connections | JSON responses, WebSocket events | Story 1.2 |
| **LLM Service (`llm_service.py`)** | Ollama API integration, prompt engineering | Prompts (strings), conversation context | LLM completions (strings), error states | Story 1.5 |
| **Database Service (SQLAlchemy)** | ORM operations, schema management | Entity objects (Conversation, Message) | Persisted records, query results | Story 1.3 |
| **Cache Service (Redis)** | Key-value caching, pub/sub messaging | Cache keys, values, TTL | Cached data, pub/sub events | Story 1.4 |
| **Error Handler** | Global exception handling, user-friendly error messages | Exception objects, request context | Standardized error responses | Story 1.7 |
| **Logger** | Structured logging, debugging support | Log messages, severity levels | Console output (dev), structured logs (prod) | Story 1.7 |

**Module Interaction Flow:**
1. **Story 1.1 (Frontend)** → Initializes React app, ready to make API calls
2. **Story 1.2 (Backend)** → Flask API receives requests, routes to appropriate handlers
3. **Story 1.3 (Database)** → SQLAlchemy ORM persists conversation data
4. **Story 1.4 (Cache)** → Redis stores temporary data, enables WebSocket pub/sub
5. **Story 1.5 (LLM)** → Ollama service generates AI responses
6. **Story 1.6 (Deployment)** → Railway hosts all services with auto-deploy
7. **Story 1.7 (Error Handling)** → Catches failures across all modules, logs errors

### Data Models and Contracts

**Database Schema (Story 1.3):**

**`conversations` table:**
```sql
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID REFERENCES students(id),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    topic VARCHAR(255),
    CONSTRAINT conversations_pkey PRIMARY KEY (id)
);

CREATE INDEX idx_conversations_student_id ON conversations(student_id);
CREATE INDEX idx_conversations_updated_at ON conversations(updated_at DESC);
```

**`messages` table:**
```sql
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    sender VARCHAR(10) NOT NULL CHECK (sender IN ('student', 'tutor')),
    content TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    metadata JSONB,
    CONSTRAINT messages_pkey PRIMARY KEY (id)
);

CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_messages_timestamp ON messages(timestamp DESC);
CREATE INDEX idx_messages_metadata_gin ON messages USING GIN(metadata);
```

**`students` table:**
```sql
CREATE TABLE students (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    preferences JSONB DEFAULT '{}',
    CONSTRAINT students_pkey PRIMARY KEY (id)
);
```

**SQLAlchemy ORM Models (Story 1.3):**
```python
# models/conversation.py
from app.extensions import db
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
from datetime import datetime

class Conversation(db.Model):
    __tablename__ = 'conversations'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = db.Column(UUID(as_uuid=True), db.ForeignKey('students.id'))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    topic = db.Column(db.String(255))

    messages = db.relationship('Message', backref='conversation', lazy='dynamic', cascade='all, delete-orphan')

# models/message.py
class Message(db.Model):
    __tablename__ = 'messages'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = db.Column(UUID(as_uuid=True), db.ForeignKey('conversations.id'), nullable=False)
    sender = db.Column(db.String(10), nullable=False)  # 'student' or 'tutor'
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    metadata = db.Column(JSONB)

    __table_args__ = (
        db.CheckConstraint("sender IN ('student', 'tutor')", name='check_sender'),
    )
```

**Redis Cache Key Naming Convention (Story 1.4):**
- LLM responses: `llm:response:{hash(prompt)}`
- Conversation context: `conversation:context:{conversation_id}`
- Health checks: `health:ollama:status`
- TTL: 3600 seconds (1 hour) default

### APIs and Interfaces

**REST API Endpoints (Story 1.2):**

**Health Check:**
```
GET /api/health
Response: 200 OK
{
  "success": true,
  "data": {
    "status": "healthy",
    "timestamp": "2025-11-03T10:30:00Z",
    "services": {
      "database": "connected",
      "redis": "connected",
      "ollama": "not_configured"  // Story 1.5 will make this "available"
    }
  }
}
```

**Database Health Check (Story 1.3):**
```
GET /api/health/database
Response: 200 OK
{
  "success": true,
  "data": {
    "status": "connected",
    "pool_size": 5,
    "max_connections": 20
  }
}
```

**Cache Health Check (Story 1.4):**
```
GET /api/health/cache
Response: 200 OK
{
  "success": true,
  "data": {
    "status": "connected",
    "ping_response": "PONG",
    "memory_usage": "1.2MB"
  }
}
```

**LLM Health Check (Story 1.5):**
```
GET /api/health/llm
Response: 200 OK
{
  "success": true,
  "data": {
    "status": "available",
    "model": "llama3.2-vision",
    "endpoint": "http://localhost:11434"
  }
}
```

**Error Response Format (Story 1.7):**
```json
{
  "success": false,
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "Something went wrong. Please try again.",
    "details": {}
  }
}
```

**WebSocket Events (Story 1.2 - configured, not yet implemented):**
- Connection endpoint: `ws://localhost:5000/socket.io`
- Events: `connect`, `disconnect` (basic connectivity testing)
- Full implementation deferred to Epic 2

**LLM Service Interface (Story 1.5):**
```python
# services/llm_service.py
from ollama import Client
from typing import Optional

class LLMService:
    def __init__(self, endpoint: str = "http://localhost:11434"):
        self.client = Client(host=endpoint)
        self.model = "llama3.2-vision"
        self.timeout = 10  # seconds

    def generate(self, prompt: str, context: Optional[list] = None) -> dict:
        """
        Generate LLM completion with timeout and error handling.

        Args:
            prompt: The prompt string
            context: Optional conversation context

        Returns:
            {
                "success": bool,
                "content": str,
                "error": Optional[str]
            }
        """
        try:
            response = self.client.generate(
                model=self.model,
                prompt=prompt,
                context=context,
                options={"timeout": self.timeout}
            )
            return {
                "success": True,
                "content": response['response'],
                "error": None
            }
        except TimeoutError:
            return {
                "success": False,
                "content": None,
                "error": "LLM request timed out"
            }
        except Exception as e:
            return {
                "success": False,
                "content": None,
                "error": str(e)
            }

    def health_check(self) -> dict:
        """Check if Ollama service is available."""
        try:
            models = self.client.list()
            return {
                "status": "available",
                "model": self.model,
                "endpoint": self.client._client.base_url
            }
        except Exception:
            return {
                "status": "unavailable",
                "model": None,
                "endpoint": None
            }
```

### Workflows and Sequencing

**Story Execution Sequence:**

1. **Story 1.1 (Frontend)** - Parallel with 1.2
   - `npm create vite@latest` → Initialize React + Vite project
   - `npx shadcn-ui@latest init` → Install shadcn/ui components
   - Configure Tailwind CSS v4.0, ESLint, Prettier
   - Install Kea state management library
   - Verify: `npm run dev` starts successfully

2. **Story 1.2 (Backend)** - Parallel with 1.1
   - Create Flask project structure (`app/`, `routes/`, `services/`, `models/`)
   - Configure Flask-SocketIO, Flask-CORS
   - Implement health check endpoint: `GET /api/health`
   - Verify: `flask run` starts successfully

3. **Story 1.3 (Database)** - Depends on 1.2
   - Install PostgreSQL locally (or use Docker)
   - Configure SQLAlchemy with Flask (`app/extensions.py`)
   - Set up Alembic migrations
   - Create initial migration with `conversations`, `messages`, `students` tables
   - Implement database health check: `GET /api/health/database`
   - Verify: Migration applies successfully, health check returns "connected"

4. **Story 1.4 (Cache)** - Depends on 1.2
   - Install Redis locally (or use Docker)
   - Configure redis-py client with connection pooling
   - Implement cache health check: `GET /api/health/cache`
   - Test basic cache operations (set, get, expire)
   - Verify: Health check returns "connected", cache operations work

5. **Story 1.5 (LLM)** - Depends on 1.2
   - Install Ollama locally
   - Pull `llama3.2-vision` model
   - Create `LLMService` abstraction layer (`services/llm_service.py`)
   - Implement timeout wrapper (10s max)
   - Implement LLM health check: `GET /api/health/llm`
   - Test example prompts
   - Verify: Health check returns "available", prompt/response works

6. **Story 1.6 (Deployment)** - Depends on 1.2, 1.3, 1.4
   - Create Railway project
   - Link GitHub repository for auto-deploy
   - Provision PostgreSQL and Redis add-ons on Railway
   - Configure environment variables: `DATABASE_URL`, `REDIS_URL`, `OLLAMA_API_URL`
   - Configure start command: `gunicorn --worker-class eventlet -w 1 app:app`
   - Deploy to Railway staging environment
   - Verify: Health checks accessible via Railway URL

7. **Story 1.7 (Error Handling)** - Depends on 1.1, 1.2
   - Configure Python `logging` module with structured JSON format
   - Implement global Flask error handler (`@app.errorhandler(Exception)`)
   - Create React error boundary component (`ErrorBoundary.tsx`)
   - Standardize error response format (see API section above)
   - Configure logging levels (DEBUG for dev, INFO for prod)
   - Add request/response logging middleware
   - Test graceful degradation for LLM failures
   - Verify: Errors logged correctly, user sees friendly messages

**Deployment Workflow (Story 1.6):**
```
Developer commits to GitHub
    ↓
Railway detects commit
    ↓
Railway builds backend (pip install -r requirements.txt)
    ↓
Railway builds frontend (npm run build)
    ↓
Railway runs migrations (flask db upgrade)
    ↓
Railway starts gunicorn with eventlet workers
    ↓
Health checks pass
    ↓
Deployment complete
```

## Non-Functional Requirements

### Performance

**Response Time (Stories 1.2, 1.5, 1.7):**
- Health check endpoints: <100ms response time (Story 1.2, 1.3, 1.4, 1.5)
- LLM prompt/response: <10s timeout enforced (Story 1.5)
- Database queries: <100ms for indexed queries (Story 1.3)
- Redis cache operations: <10ms for get/set operations (Story 1.4)

**Resource Utilization:**
- Frontend bundle size: Target <500KB gzipped (Story 1.1 - Vite optimization)
- Database connection pooling: Max 20 connections configured (Story 1.3)
- Redis connection pooling: Configured via redis-py (Story 1.4)

**Build Performance (Story 1.1):**
- Vite dev server: <1s startup time
- HMR (Hot Module Replacement): <100ms update time
- Tailwind CSS v4.0: 5x faster builds vs v3.x

**Deployment Performance (Story 1.6):**
- Railway build time: <5 minutes for initial build
- Railway deploy time: <2 minutes after build

### Security

**Authentication & Authorization:**
- **MVP Limitation:** No authentication implemented in Epic 1 (single-user dev environment)
- **Production Warning:** DO NOT expose to public internet without authentication (documented in Story 1.2, 1.6)

**CORS Configuration (Story 1.2):**
- Allowed origins: `http://localhost:5173` (dev), `https://supertutors.railway.app` (prod)
- Allowed methods: GET, POST, PUT, DELETE
- Credentials: Not supported in MVP

**Input Validation:**
- Frontend: TypeScript type checking (Story 1.1)
- Backend: Flask request validation (Story 1.2)
- Database: SQLAlchemy ORM prevents SQL injection (Story 1.3)

**Environment Variables (Story 1.2, 1.6):**
- `DATABASE_URL`: PostgreSQL connection string (Railway managed)
- `REDIS_URL`: Redis connection string (Railway managed)
- `OLLAMA_API_URL`: Ollama endpoint (local: `http://localhost:11434`, prod: TBD)
- `FLASK_ENV`: `development` or `production`
- **Security:** All secrets stored as Railway environment variables, never committed to Git

**HTTPS/TLS:**
- Development: HTTP only (localhost)
- Production: HTTPS enforced by Railway (automatic SSL certificates)

### Reliability/Availability

**Error Handling (Story 1.7):**
- Global Flask error handler catches all unhandled exceptions
- React error boundary prevents full frontend crashes
- Graceful degradation for LLM failures (timeout errors show friendly message)
- Database connection failures handled gracefully (retry logic)
- Redis connection failures handled gracefully (fallback to no caching)

**Health Checks (Stories 1.2, 1.3, 1.4, 1.5):**
- `/api/health` - Overall system health
- `/api/health/database` - PostgreSQL connection status
- `/api/health/cache` - Redis connection status
- `/api/health/llm` - Ollama availability
- Use: Railway health checks to detect deployment failures

**Uptime Target:**
- MVP: Best-effort (no SLA)
- Development environment: Acceptable downtime during deployments
- Production target (future): 99.5% during school hours (3pm-9pm ET weekdays)

**Data Integrity (Story 1.3):**
- Database transactions for multi-table operations
- Foreign key constraints ensure referential integrity
- Cascade deletes configured (delete conversation → delete all messages)
- PostgreSQL automated backups (Railway managed)

### Observability

**Logging (Story 1.7):**

**Backend Logging:**
- Python `logging` module configured with structured format
- Log levels:
  - `DEBUG`: Development only (verbose output)
  - `INFO`: Normal operations (health checks, API requests)
  - `WARNING`: Recoverable issues (LLM timeouts, cache misses)
  - `ERROR`: Failures requiring attention (database errors, uncaught exceptions)
- Log format: `[timestamp] [level] [module] message`
- Example: `[2025-11-03 14:23:45] [INFO] [llm_service] Generating LLM completion`

**Frontend Logging:**
- Development: `console.log()` for debugging
- Production: Structured logging to console (future: external service like LogRocket/Sentry)
- Error boundary logs React errors

**Request/Response Logging (Story 1.7):**
- Middleware logs all API requests/responses
- Includes: method, path, status code, response time
- Example: `[INFO] [api] GET /api/health - 200 OK - 45ms`

**Metrics (MVP - Basic):**
- Health check endpoint provides service status
- Future: Application metrics (request count, error rate, latency percentiles)

**Monitoring (Future):**
- Railway provides basic infrastructure monitoring (CPU, memory, disk)
- Application-level monitoring deferred to post-MVP
- Error tracking deferred to post-MVP

## Dependencies and Integrations

### Frontend Dependencies (Story 1.1)

**Core Framework:**
```json
{
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "kea": "^3.1.6",
    "kea-typegen": "^3.1.6",
    "react-katex": "^3.1.0",
    "katex": "^0.16.11",
    "socket.io-client": "^4.8.1"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.3.4",
    "vite": "^6.0.0",
    "typescript": "^5.7.0",
    "tailwindcss": "^4.0.0",
    "@types/react": "^18.3.12",
    "@types/react-dom": "^18.3.1",
    "eslint": "^9.15.0",
    "prettier": "^3.4.1"
  }
}
```

**shadcn/ui Components (installed via CLI):**
- Button, Input, Dialog, Toast, Card, Label
- Radix UI primitives (automatic dependency)

### Backend Dependencies (Story 1.2)

**requirements.txt:**
```
Flask==3.1.2
Flask-SocketIO==5.5.1
Flask-CORS==6.0.1
SQLAlchemy==2.0.36
Alembic==1.14.0
psycopg2-binary==2.9.10
redis==5.2.1
ollama==0.6.0
sympy==1.14.0
python-dotenv==1.0.1
gunicorn==23.0.0
eventlet==0.37.0
```

**Python Version:**
- Python 3.11+ required (for type hints, performance optimizations)

### External Services

**PostgreSQL (Story 1.3):**
- Version: 18 (latest stable)
- Local development: PostgreSQL.app or Docker container
- Production: Railway managed PostgreSQL add-on
- Connection: `DATABASE_URL` environment variable

**Redis (Story 1.4):**
- Version: 7.4 (latest stable)
- Local development: Redis installed via Homebrew or Docker container
- Production: Railway managed Redis add-on
- Connection: `REDIS_URL` environment variable

**Ollama LLM (Story 1.5):**
- Version: Latest (0.6.0+)
- Model: Llama 3.2 Vision (11B parameters)
- Local development: Ollama running on Mac
- Production: Cloud GPU endpoint (Modal/Replicate/RunPod) - TBD
- Connection: `OLLAMA_API_URL` environment variable

**Railway (Story 1.6):**
- Platform version: Latest
- Buildpacks: nixpacks (auto-detected)
- Services: Frontend (static), Backend (Flask), PostgreSQL, Redis
- Deployment: Git push triggers auto-deploy

### Integration Points

**Frontend → Backend:**
- Protocol: HTTP/HTTPS for REST API, WebSocket for real-time chat
- Authentication: None in Epic 1 (future: JWT tokens)
- Base URL: `http://localhost:5000` (dev), `https://supertutors-api.railway.app` (prod)

**Backend → PostgreSQL:**
- Protocol: PostgreSQL wire protocol (TCP)
- Connection pooling: SQLAlchemy pool (max 20 connections)
- Migrations: Alembic (version-controlled schema changes)

**Backend → Redis:**
- Protocol: Redis protocol (TCP)
- Connection pooling: redis-py connection pool
- Use cases: LLM response caching, WebSocket pub/sub

**Backend → Ollama:**
- Protocol: HTTP REST API
- Endpoint: `http://localhost:11434` (dev), TBD (prod)
- Timeout: 10 seconds per request
- Error handling: Graceful fallback on failure

### Version Constraints

**Critical Version Requirements:**
- Node.js: 18+ (for Vite 6.x compatibility)
- Python: 3.11+ (for performance, type hints)
- PostgreSQL: 14+ (for JSONB, UUIDs, modern features)
- Redis: 7.0+ (for latest commands, stability)

**Dependency Update Policy:**
- Major versions: Manual review required
- Minor versions: Auto-update acceptable (security patches)
- Lock files: `package-lock.json` (frontend), `requirements.txt` with pinned versions (backend)

## Acceptance Criteria (Authoritative)

**Epic 1 Completion Criteria:**

1. **Story 1.1 - Frontend Initialization:**
   - ✅ Vite project created with React 18.3.1 and TypeScript 5.7.x
   - ✅ Tailwind CSS v4.0 configured and functional
   - ✅ shadcn/ui components installed and importable
   - ✅ Kea state management library installed
   - ✅ ESLint and Prettier configured
   - ✅ `npm run dev` starts development server on `http://localhost:5173`
   - ✅ Hot Module Replacement (HMR) works

2. **Story 1.2 - Backend Initialization:**
   - ✅ Flask 3.1.2 project created with proper folder structure
   - ✅ Flask-SocketIO configured for WebSocket support
   - ✅ Flask-CORS configured for frontend access
   - ✅ Health check endpoint `GET /api/health` returns 200 OK
   - ✅ Python type hints configured (mypy)
   - ✅ Pylint configured for code quality
   - ✅ `flask run` starts API server on `http://localhost:5000`

3. **Story 1.3 - Database Configuration:**
   - ✅ PostgreSQL 18 installed locally and accessible
   - ✅ SQLAlchemy ORM configured with Flask
   - ✅ Alembic migrations initialized
   - ✅ Initial migration created: `conversations`, `messages`, `students` tables
   - ✅ Indexes created on frequently queried columns
   - ✅ Migration applied successfully: `flask db upgrade`
   - ✅ Database health check `GET /api/health/database` returns "connected"

4. **Story 1.4 - Cache Configuration:**
   - ✅ Redis 7.4 installed locally and running
   - ✅ redis-py client configured with connection pooling
   - ✅ Cache health check `GET /api/health/cache` returns "connected"
   - ✅ Basic cache operations work: set, get, expire
   - ✅ TTL management configured (default 1 hour)
   - ✅ Cache key naming convention documented

5. **Story 1.5 - LLM Integration:**
   - ✅ Ollama installed locally
   - ✅ Llama 3.2 Vision model pulled: `ollama pull llama3.2-vision`
   - ✅ `LLMService` abstraction layer created in `services/llm_service.py`
   - ✅ Basic prompt/response flow works
   - ✅ Timeout wrapper implemented (10s max)
   - ✅ Error handling for LLM failures (network, timeout)
   - ✅ LLM health check `GET /api/health/llm` returns "available"
   - ✅ Example prompts tested successfully

6. **Story 1.6 - Railway Deployment:**
   - ✅ Railway project created and linked to GitHub repository
   - ✅ Environment variables configured: `DATABASE_URL`, `REDIS_URL`, `OLLAMA_API_URL`, `FLASK_ENV`
   - ✅ PostgreSQL and Redis Railway add-ons provisioned
   - ✅ Build pipeline configured (nixpacks buildpack)
   - ✅ Start command configured: `gunicorn --worker-class eventlet -w 1 app:app`
   - ✅ Successful deployment to Railway staging environment
   - ✅ Health check endpoints accessible via Railway URL
   - ✅ All services (database, redis) show "connected" status

7. **Story 1.7 - Error Handling & Logging:**
   - ✅ Python `logging` module configured with structured format
   - ✅ Frontend error boundary component created (`ErrorBoundary.tsx`)
   - ✅ Global Flask error handler implemented (`@app.errorhandler(Exception)`)
   - ✅ Error response standardization (consistent JSON format)
   - ✅ Logging levels configured (DEBUG for dev, INFO for prod)
   - ✅ Request/response logging middleware added
   - ✅ Error tracking works (errors logged to console)
   - ✅ Graceful degradation for LLM failures tested

**End-to-End Verification:**
- ✅ Frontend starts: `npm run dev` (localhost:5173)
- ✅ Backend starts: `flask run` (localhost:5000)
- ✅ Frontend can fetch `http://localhost:5000/api/health` successfully
- ✅ All health checks return "connected" or "available"
- ✅ Railway deployment accessible and all services healthy
- ✅ Error handling gracefully handles LLM timeout (tested manually)

## Traceability Mapping

| Acceptance Criterion | Spec Section | Component/API | Test Approach |
|---------------------|--------------|---------------|---------------|
| **AC 1.1**: Vite + React + TypeScript initialized | Detailed Design → Services | Frontend (React/Vite) | Verify `npm run dev` starts, HMR works |
| **AC 1.1**: Tailwind CSS v4.0 configured | Dependencies → Frontend | Frontend styling | Check Tailwind classes render correctly |
| **AC 1.1**: shadcn/ui installed | Dependencies → Frontend | UI components | Import Button component, verify no errors |
| **AC 1.1**: Kea state management installed | Dependencies → Frontend | State management | Import kea, verify no errors |
| **AC 1.2**: Flask 3.1.2 with proper structure | Detailed Design → Services | Flask API | Verify folder structure exists, `flask run` starts |
| **AC 1.2**: Flask-SocketIO configured | APIs → WebSocket Events | Flask API | Connect to WebSocket, verify `connect` event |
| **AC 1.2**: Health check endpoint | APIs → REST Endpoints | `GET /api/health` | Curl endpoint, verify 200 OK response |
| **AC 1.3**: PostgreSQL with SQLAlchemy | Data Models | Database Service | Run migration, verify tables created |
| **AC 1.3**: Indexes created | Data Models → Schema | Database indexes | Check `pg_indexes` table in PostgreSQL |
| **AC 1.3**: Database health check | APIs → REST Endpoints | `GET /api/health/database` | Curl endpoint, verify "connected" status |
| **AC 1.4**: Redis with connection pooling | Dependencies → External Services | Cache Service | Verify `redis-cli ping` returns PONG |
| **AC 1.4**: Cache operations work | Detailed Design → Services | Cache Service (Redis) | Test set/get/expire via Python script |
| **AC 1.4**: Cache health check | APIs → REST Endpoints | `GET /api/health/cache` | Curl endpoint, verify "connected" status |
| **AC 1.5**: Ollama LLM integrated | Dependencies → External Services | LLM Service | Verify `ollama list` shows llama3.2-vision |
| **AC 1.5**: LLMService abstraction layer | APIs → LLM Service Interface | `services/llm_service.py` | Call `generate()` method, verify response |
| **AC 1.5**: Timeout wrapper (10s) | APIs → LLM Service Interface | LLMService timeout | Test with slow prompt, verify timeout error |
| **AC 1.5**: LLM health check | APIs → REST Endpoints | `GET /api/health/llm` | Curl endpoint, verify "available" status |
| **AC 1.6**: Railway deployment configured | Dependencies → External Services | Railway platform | Check Railway dashboard, verify services running |
| **AC 1.6**: Environment variables set | Security → Environment Variables | Railway config | Verify env vars accessible in Flask app |
| **AC 1.6**: Health checks accessible via Railway URL | Deployment → Workflows | Railway deployment | Curl Railway URL + `/api/health` |
| **AC 1.7**: Python logging configured | Observability → Logging | Backend logging | Check console output, verify log format |
| **AC 1.7**: Frontend error boundary | Detailed Design → Services | `ErrorBoundary.tsx` | Trigger React error, verify boundary catches it |
| **AC 1.7**: Global Flask error handler | Detailed Design → Services | Error Handler | Trigger unhandled exception, verify friendly error |
| **AC 1.7**: Graceful LLM degradation | Reliability → Error Handling | LLM Service error handling | Simulate LLM timeout, verify friendly message |

## Risks, Assumptions, Open Questions

### Risks

**RISK-1: Ollama local development dependency**
- **Severity:** Medium
- **Description:** Developers must install Ollama locally and pull Llama 3.2 Vision model (11GB download). Large model size may cause onboarding friction.
- **Mitigation:** Provide clear setup documentation in Story 1.5. Consider Docker container with pre-pulled model as alternative.
- **Owner:** Story 1.5

**RISK-2: Railway cost overruns in production**
- **Severity:** Low (MVP)
- **Description:** Railway usage-based pricing could exceed budget if traffic spikes unexpectedly.
- **Mitigation:** MVP is single-user dev environment (minimal traffic). Monitor Railway usage dashboard. Set up billing alerts.
- **Owner:** Story 1.6

**RISK-3: PostgreSQL 18 compatibility issues**
- **Severity:** Low
- **Description:** PostgreSQL 18 is very recent (released 2024). Potential compatibility issues with SQLAlchemy or Railway managed service.
- **Mitigation:** PostgreSQL 14+ is acceptable fallback (documented in version constraints). Railway may provision PostgreSQL 16 instead.
- **Owner:** Story 1.3

**RISK-4: Tailwind CSS v4.0 breaking changes**
- **Severity:** Low
- **Description:** Tailwind v4.0 is bleeding-edge (2025 release). Potential breaking changes or instability.
- **Mitigation:** Fallback to Tailwind v3.4 if issues arise. Document migration path in Story 1.1.
- **Owner:** Story 1.1

**RISK-5: WebSocket connection failures in production**
- **Severity:** Medium
- **Description:** Railway may have WebSocket limitations or connection instability (long polling fallback required).
- **Mitigation:** Flask-SocketIO provides automatic long polling fallback. Test WebSocket connection during Story 1.6 deployment.
- **Owner:** Story 1.6

### Assumptions

**ASSUMPTION-1: Developers have macOS**
- Architecture document assumes Mac for local Ollama development.
- **Validation:** Confirm with team during Story 1.5. Provide Linux/Windows alternative if needed (Docker).

**ASSUMPTION-2: GitHub repository exists**
- Story 1.6 assumes GitHub repo for Railway auto-deploy.
- **Validation:** Create GitHub repo before Story 1.6. Confirm repository access for Railway.

**ASSUMPTION-3: Railway free tier sufficient for MVP**
- Assumption: $5 trial credit covers MVP development/testing.
- **Validation:** Monitor Railway usage during Story 1.6. Upgrade to Hobby plan ($5/month) if needed.

**ASSUMPTION-4: Single-user dev environment security acceptable**
- No authentication/authorization in Epic 1.
- **Validation:** Confirm with product owner. Document security warning in Story 1.2, 1.6.

**ASSUMPTION-5: LLM production hosting deferred to future epic**
- Epic 1 uses local Ollama only. Production GPU hosting (Modal/Replicate/RunPod) deferred.
- **Validation:** Confirm with product owner. Document in "Out of Scope" section.

### Open Questions

**QUESTION-1: Should we use Docker for local PostgreSQL + Redis?**
- **Context:** Architecture mentions Docker as optional but not required.
- **Decision Needed:** Standardize on Docker Compose vs native installs for consistency.
- **Impact:** Affects Story 1.3, 1.4 implementation approach.
- **Owner:** Developer preference (document both approaches)

**QUESTION-2: What LLM model size for production?**
- **Context:** Llama 3.2 Vision 11B for local dev. Production may need smaller model for cost.
- **Decision Needed:** Test performance/cost tradeoff (11B vs 7B vs 3B).
- **Impact:** Affects future Epic (production LLM hosting).
- **Owner:** Deferred to post-Epic 1

**QUESTION-3: Should Railway deployment include frontend static build?**
- **Context:** Workflow.yaml mentions both frontend + backend deployment to Railway.
- **Decision Needed:** Confirm Railway hosts both services or separate hosting (Vercel for frontend?).
- **Impact:** Affects Story 1.6 deployment configuration.
- **Owner:** Story 1.6 implementation decision

**QUESTION-4: Do we need Redis persistence (RDB/AOF)?**
- **Context:** Redis used for caching (ephemeral) and WebSocket pub/sub.
- **Decision Needed:** Configure Redis persistence for durability or accept volatile caching.
- **Impact:** Affects Story 1.4 Redis configuration.
- **Owner:** Story 1.4 (default: no persistence for MVP caching)

## Test Strategy Summary

### Unit Testing

**Frontend (Story 1.1):**
- **Framework:** Vitest (Vite-native testing)
- **Coverage Target:** >70% for critical utilities
- **Test Cases:**
  - Kea logic store actions/reducers (when implemented in future epics)
  - Error boundary component (Story 1.7)
  - Utility functions (when created)

**Backend (Story 1.2, 1.3, 1.4, 1.5, 1.7):**
- **Framework:** pytest
- **Coverage Target:** >70% for services and models
- **Test Cases:**
  - LLMService.generate() success/failure scenarios (Story 1.5)
  - LLMService timeout handling (Story 1.5)
  - Database models CRUD operations (Story 1.3)
  - Redis cache set/get/expire operations (Story 1.4)
  - Error handler exception scenarios (Story 1.7)

### Integration Testing

**API Endpoints (Story 1.2, 1.3, 1.4, 1.5):**
- **Framework:** pytest with Flask test client
- **Test Cases:**
  - `GET /api/health` returns 200 OK with correct JSON format
  - `GET /api/health/database` returns "connected" when database available
  - `GET /api/health/cache` returns "connected" when Redis available
  - `GET /api/health/llm` returns "available" when Ollama running
  - Error responses return standardized JSON format (Story 1.7)

**Database Integration (Story 1.3):**
- **Framework:** pytest with test database
- **Test Cases:**
  - Alembic migration applies successfully
  - Tables created with correct schema (UUIDs, indexes, constraints)
  - SQLAlchemy models insert/query/update/delete successfully
  - Foreign key relationships work (delete conversation cascades to messages)

**Redis Integration (Story 1.4):**
- **Framework:** pytest with test Redis instance
- **Test Cases:**
  - Connection pooling works under load
  - Cache operations (set/get/expire) work correctly
  - TTL expiration works as expected (1 hour default)

**LLM Integration (Story 1.5):**
- **Framework:** pytest with mocked Ollama responses
- **Test Cases:**
  - LLMService.generate() returns correct format on success
  - Timeout wrapper triggers after 10 seconds
  - Error handling returns friendly error messages
  - Health check detects Ollama availability

### End-to-End Testing

**Local Development (Stories 1.1, 1.2):**
- **Manual Testing:**
  - Start frontend: `npm run dev` → verify localhost:5173 accessible
  - Start backend: `flask run` → verify localhost:5000 accessible
  - Frontend fetch to backend: verify CORS allows cross-origin requests
  - Health check: curl localhost:5000/api/health → verify all services "connected"

**Railway Deployment (Story 1.6):**
- **Manual Testing:**
  - Git push → verify Railway auto-deploy triggers
  - Health checks: curl Railway URL + /api/health → verify 200 OK
  - Database connection: verify Railway PostgreSQL shows "connected"
  - Redis connection: verify Railway Redis shows "connected"
  - WebSocket connection: test Socket.IO client connects successfully

**Error Handling (Story 1.7):**
- **Manual Testing:**
  - Trigger React error → verify error boundary catches and displays friendly message
  - Trigger Flask exception → verify global error handler returns standardized JSON
  - Simulate LLM timeout → verify graceful degradation with user-friendly message
  - Check logs → verify all errors logged with correct format and severity

### Performance Testing

**Health Check Response Time (Story 1.2, 1.3, 1.4, 1.5):**
- **Tool:** curl with timing (`curl -w "%{time_total}"`)
- **Target:** <100ms response time
- **Test:** 10 consecutive requests, measure average latency

**LLM Timeout Enforcement (Story 1.5):**
- **Tool:** pytest with sleep mock
- **Target:** Timeout triggers at 10 seconds
- **Test:** Simulate slow LLM response, verify timeout error after 10s

**Database Query Performance (Story 1.3):**
- **Tool:** PostgreSQL EXPLAIN ANALYZE
- **Target:** <100ms for indexed queries
- **Test:** Query conversations by student_id, verify index used

### Regression Testing

**After Each Story:**
- Re-run all health checks to ensure no regressions
- Verify previous stories' functionality still works
- Check logs for unexpected errors or warnings

### Test Execution Schedule

**Story 1.1**: Unit tests for error boundary (future)
**Story 1.2**: Integration tests for `/api/health` endpoint
**Story 1.3**: Integration tests for database models + health check
**Story 1.4**: Integration tests for Redis cache + health check
**Story 1.5**: Unit tests for LLMService + integration test for health check
**Story 1.6**: End-to-end tests for Railway deployment
**Story 1.7**: Integration tests for error handling + logging

**End of Epic 1**: Full regression suite (all health checks, E2E verification)
