# Story 1.2: Initialize Flask Backend API

Status: drafted

## Story

As a developer,
I want a properly structured Flask API with WebSocket support,
So that I can build real-time backend features with clean architecture.

## Acceptance Criteria

1. Flask 3.1.2 project created with proper folder structure
2. Flask-SocketIO configured for WebSocket support
3. CORS configured for local development and Railway deployment
4. Python type hints enabled (mypy configuration)
5. Pylint configured for code quality
6. `flask run` starts API server successfully
7. Health check endpoint returns 200 OK

## Tasks / Subtasks

- [ ] **Task 1: Initialize Flask project structure** (AC: #1)
  - [ ] Create `backend/` directory with Flask application factory pattern
  - [ ] Create folder structure: `app/__init__.py`, `app/routes/`, `app/services/`, `app/models/`, `app/utils/`, `app/config.py`, `app/extensions.py`
  - [ ] Create `requirements.txt` with Flask 3.1.2 and core dependencies
  - [ ] Create Python virtual environment: `python -m venv venv`
  - [ ] Install dependencies: `pip install -r requirements.txt`
  - [ ] Verify folder structure matches architecture specification

- [ ] **Task 2: Configure Flask application factory** (AC: #1, #7)
  - [ ] Implement `app/__init__.py` with `create_app()` factory function
  - [ ] Configure Flask app instance with development/production config
  - [ ] Create `app/config.py` with environment-based configuration (DevelopmentConfig, ProductionConfig)
  - [ ] Load environment variables using `python-dotenv`
  - [ ] Create `run.py` entry point that calls `create_app()`
  - [ ] Test: `flask run` starts successfully on `http://localhost:5000`

- [ ] **Task 3: Configure Flask-SocketIO for WebSocket support** (AC: #2)
  - [ ] Install Flask-SocketIO 5.5.1: verify in `requirements.txt`
  - [ ] Initialize SocketIO in `app/extensions.py`
  - [ ] Configure SocketIO in `create_app()` with CORS origins
  - [ ] Create basic connection event handlers (`connect`, `disconnect`) in `app/routes/`
  - [ ] Configure eventlet/gevent async mode for production compatibility
  - [ ] Test: SocketIO server accepts WebSocket connections on `/socket.io`

- [ ] **Task 4: Configure Flask-CORS** (AC: #3)
  - [ ] Install Flask-CORS 6.0.1: verify in `requirements.txt`
  - [ ] Initialize CORS in `app/extensions.py`
  - [ ] Configure allowed origins: `http://localhost:5173` (dev), Railway frontend URL (prod)
  - [ ] Configure allowed methods: GET, POST, PUT, DELETE
  - [ ] Configure credentials: False (no cookies in MVP)
  - [ ] Test: CORS headers present in response (verify with curl)

- [ ] **Task 5: Implement health check endpoint** (AC: #7)
  - [ ] Create `app/routes/health.py` blueprint
  - [ ] Implement `GET /api/health` endpoint returning JSON: `{"success": true, "data": {"status": "healthy", "timestamp": "...", "services": {}}}`
  - [ ] Register health blueprint in `create_app()`
  - [ ] Test: `curl http://localhost:5000/api/health` returns 200 OK
  - [ ] Verify response format matches tech spec (success, data, timestamp fields)

- [ ] **Task 6: Configure Python type hints and mypy** (AC: #4)
  - [ ] Install mypy: `pip install mypy`
  - [ ] Create `mypy.ini` configuration file
  - [ ] Configure strict type checking: `strict = True`
  - [ ] Add type hints to all function signatures in `app/__init__.py` and `app/routes/health.py`
  - [ ] Run `mypy app/` and fix any type errors
  - [ ] Add mypy check to development workflow

- [ ] **Task 7: Configure Pylint for code quality** (AC: #5)
  - [ ] Install Pylint: `pip install pylint`
  - [ ] Create `.pylintrc` configuration file
  - [ ] Configure Pylint rules (max line length 100, disable specific warnings)
  - [ ] Run `pylint app/` and fix critical issues
  - [ ] Add Pylint check to development workflow
  - [ ] Verify no critical Pylint errors (score >8.0)

- [ ] **Task 8: Verify complete backend startup** (AC: #6, #7)
  - [ ] Run `flask run` from backend directory
  - [ ] Verify server starts on `http://localhost:5000`
  - [ ] Verify health check endpoint accessible: `GET /api/health`
  - [ ] Verify SocketIO endpoint accessible (test connection with Socket.IO client)
  - [ ] Verify no console errors during startup
  - [ ] Document startup commands in README or backend documentation

## Dev Notes

### Architecture Context

This story establishes the Flask backend API foundation for the SuperTutors platform, implementing the backend infrastructure as specified in the Architecture document.

**Key Architecture Decisions:**
- **ADR-004 (Flask-SocketIO):** Real-time WebSocket communication essential for chat experience (Epic 2)
- **Flask Application Factory Pattern:** Enables environment-based configuration (dev/test/prod)
- **Blueprint Architecture:** Modular route organization for scalability (chat, image, voice, conversation routes in future stories)

**Technology Stack Rationale:**
- **Flask 3.1.2:** Lightweight, flexible, Python ecosystem integration (SymPy, Ollama)
- **Flask-SocketIO 5.5.1:** Bi-directional real-time communication, long-polling fallback for reliability
- **Flask-CORS 6.0.1:** Secure cross-origin requests from React frontend
- **Python Type Hints + mypy:** Type safety for complex service interactions (LLM, SymPy, database)
- **Pylint:** Code quality enforcement, prevent common Python pitfalls

### Project Structure Notes

**Alignment with Unified Project Structure:**

This story creates the `backend/` directory structure as specified in [docs/architecture.md#Project-Structure]:

```
backend/
├── app/
│   ├── __init__.py              # Flask application factory (create_app())
│   ├── routes/
│   │   └── health.py            # Health check blueprint (this story)
│   │   # Future: chat.py, image.py, voice.py, conversation.py
│   ├── services/                # Reserved for future stories (llm_service, sympy_service, etc.)
│   ├── models/                  # Reserved for Story 1.3 (conversation, message, student models)
│   ├── utils/                   # Reserved for future stories (validators, errors)
│   ├── config.py                # Environment-based configuration
│   └── extensions.py            # Flask extensions (socketio, cors)
├── migrations/                  # Reserved for Story 1.3 (Alembic migrations)
├── tests/                       # Reserved for future stories (unit/integration tests)
├── requirements.txt             # Python dependencies
├── run.py                       # Application entry point
├── mypy.ini                     # Type checking configuration
└── .pylintrc                    # Code quality configuration
```

**Naming Conventions (enforced):**
- Python modules: snake_case (e.g., `health.py`, `llm_service.py`)
- Python classes: PascalCase (e.g., `DevelopmentConfig`)
- Flask blueprints: snake_case + "_bp" suffix (e.g., `health_bp`)
- Functions: snake_case (e.g., `create_app()`, `health_check()`)

**No Conflicts:** This is the second story, parallel to Story 1.1 (frontend). No integration dependencies yet.

### Testing Standards

**Unit Testing Framework:** pytest (with Flask test client)
- Not required for this story (basic setup only)
- Future stories will add tests for health check endpoints and service integrations
- Target coverage: >70% for routes and services

**Manual Testing Checklist:**
- [ ] `flask run` starts successfully on `http://localhost:5000`
- [ ] `curl http://localhost:5000/api/health` returns 200 OK
- [ ] Response format matches: `{"success": true, "data": {"status": "healthy", "timestamp": "...", "services": {}}}`
- [ ] CORS headers present in response (Access-Control-Allow-Origin)
- [ ] SocketIO connection succeeds (test with Socket.IO client library or browser extension)
- [ ] `mypy app/` reports no type errors
- [ ] `pylint app/` score >8.0 (no critical errors)
- [ ] No console errors or warnings during startup

### References

**Technical Specifications:**
- [Source: docs/tech-spec-epic-1.md#Epic-1-Story-1.2] - Detailed implementation requirements
- [Source: docs/tech-spec-epic-1.md#Backend-Dependencies] - Exact dependency versions
- [Source: docs/tech-spec-epic-1.md#Workflows-Story-1.2] - Step-by-step execution sequence
- [Source: docs/tech-spec-epic-1.md#APIs-REST-Endpoints] - Health check endpoint specification

**Architecture Documentation:**
- [Source: docs/architecture.md#Project-Structure] - Backend folder structure specification
- [Source: docs/architecture.md#Backend-Stack] - Technology stack details
- [Source: docs/architecture.md#Integration-Points] - API endpoint patterns
- [Source: docs/architecture.md#ADR-004] - Flask-SocketIO decision rationale

**Epic Context:**
- [Source: docs/epics.md#Epic-1-Story-1.2] - User story and acceptance criteria
- [Source: docs/PRD.md#Technology-Stack] - Product requirements context

### Dependencies and Prerequisites

**Prerequisites:** None (parallel to Story 1.1)

**Dependencies for Future Stories:**
- Story 1.3 (Database) depends on this story for Flask app initialization
- Story 1.4 (Cache) depends on this story for Flask app initialization
- Story 1.5 (LLM) depends on this story for service layer
- Story 1.6 (Deployment) depends on this story for Flask app
- Story 1.7 (Error Handling) depends on this story for error handler integration
- Epic 2 (Chat UI) depends on this foundation

### Non-Functional Requirements

**Performance Targets (from tech spec):**
- Health check endpoint response time: <100ms
- Flask server startup: <3s
- SocketIO connection handshake: <500ms

**Security Considerations:**
- **CORS Configuration:** Whitelisted origins only (localhost:5173 for dev, Railway URL for prod)
- **No Authentication:** MVP is single-user dev environment (documented warning)
- **Environment Variables:** Load sensitive config via `python-dotenv`, never commit `.env` file
- **Input Validation:** Framework defaults sufficient for MVP (future stories add explicit validation)

**Production Readiness:**
- Flask app uses application factory pattern for testability
- Environment-based configuration (dev/prod separation)
- WSGI server compatibility (gunicorn with eventlet for SocketIO)

### Environment Variables

**Development (.env file):**
```
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=dev-secret-key-change-in-production
CORS_ORIGINS=http://localhost:5173
```

**Production (Railway environment variables):**
```
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=<generated secure key>
CORS_ORIGINS=https://supertutors-frontend.railway.app
DATABASE_URL=<Railway PostgreSQL URL>  # Story 1.3
REDIS_URL=<Railway Redis URL>         # Story 1.4
OLLAMA_API_URL=<Cloud GPU endpoint>   # Story 1.5
```

### Change Log

- **2025-11-04:** Story created by SM agent (caiojoao) via create-story workflow
  - Initial draft based on tech-spec-epic-1.md, epics.md, and architecture.md
  - Status: drafted (ready for review and dev)

## Dev Agent Record

### Context Reference

<!-- Path(s) to story context XML will be added here by context workflow -->

### Agent Model Used

<!-- Dev agent will fill this in during implementation -->

### Debug Log References

<!-- Dev agent will add debug log paths here -->

### Completion Notes List

<!-- Dev agent will document:
- New files created (Flask app structure, blueprints, config)
- New patterns/services established (application factory pattern)
- Architectural decisions made (folder structure, CORS config)
- Technical debt deferred (testing, authentication)
- Warnings for next story (database will need Flask app context)
-->

### File List

<!-- Dev agent will list:
- NEW: app/__init__.py, app/config.py, app/extensions.py, app/routes/health.py, run.py, requirements.txt, mypy.ini, .pylintrc
- MODIFIED: (none for this story)
- DELETED: (none for this story)
-->
