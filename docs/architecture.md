# SuperTutors - Solution Architecture

**Project:** SuperTutors
**Author:** caiojoao
**Date:** 2025-11-03
**Version:** 1.0
**Project Level:** 2 (Medium Complexity Web Application)

---

## Executive Summary

SuperTutors is a full-stack web application combining a **React TypeScript frontend** with a **Python Flask backend**, leveraging **local and cloud-hosted LLMs** for Socratic math tutoring, **SymPy for computational accuracy**, and **PostgreSQL for conversation persistence**. The architecture prioritizes **pedagogical integrity** (never giving direct answers), **multimodal input processing** (text, voice, images, drawings), and **real-time responsiveness** (<2s text, <5s images).

**Deployment Strategy:** Mono-repo with separate frontend (Vite build) and backend (Flask API) deployed on Railway, with LLM inference on cloud GPU endpoints (Modal/Replicate/RunPod) for production.

---

## Project Initialization

**First implementation story:** Initialize project structure using Vite starter

```bash
# Frontend initialization
npm create vite@latest supertutors-frontend -- --template react-ts
cd supertutors-frontend
npm install

# Add shadcn/ui
npx shadcn-ui@latest init

# Add Tailwind CSS v4.0
npm install -D tailwindcss@4 postcss autoprefixer
npx tailwindcss init

# Install core dependencies
npm install kea kea-typegen react-katex katex socket.io-client

# Backend initialization (Python 3.9+)
mkdir supertutors-backend
cd supertutors-backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install flask==3.1.2 flask-cors==6.0.1 flask-socketio==5.5.1 \
            sympy==1.14.0 ollama==0.6.0 psycopg2-binary redis
```

**Decisions Provided by Vite Starter:**
- ✅ React 18.3.1 framework
- ✅ TypeScript 5.7.x type safety
- ✅ Vite 6.x build tool with fast HMR
- ✅ ESLint code linting
- ✅ Basic project structure (`src/`, `public/`, `index.html`)

---

## Decision Summary

| Category | Decision | Version | Affects Functional Areas | Rationale |
| -------- | -------- | ------- | ------------------------ | --------- |
| **Frontend Framework** | Vite + React + TypeScript | Vite 6.x, React 18.3.1, TS 5.7.x | All | Fast HMR for canvas/celebration development, TypeScript for complex state |
| **Design System** | shadcn/ui + Radix UI + Tailwind CSS | shadcn latest, Radix v1.x, Tailwind 4.0 | All UI components | WCAG 2.1 AA accessibility, copy-paste components, performance |
| **State Management** | Kea | 3.1.6 | Conversation, Canvas, Celebration | Composable state, specified in PRD |
| **Math Rendering** | KaTeX via react-katex | 3.1.0 (KaTeX latest) | Conversation Management | Fast rendering, LaTeX support, copy-able output |
| **API Framework** | Flask | 3.1.2 | Backend API | Lightweight, Python ecosystem, flexible routing |
| **WebSocket** | Flask-SocketIO | 5.5.1 | Real-time messaging | Bi-directional communication for chat |
| **CORS** | Flask-CORS | 6.0.1 | API security | Cross-origin requests from frontend |
| **Math Computation** | SymPy | 1.14.0 | Mathematical Computation | Deterministic accuracy, symbolic math |
| **LLM Integration** | Ollama Python | 0.6.0 | Socratic dialogue, Vision AI | Local dev (Ollama), cloud inference (production) |
| **Database** | PostgreSQL | 18 | Conversation persistence | Relational integrity, JSON support, full-text search |
| **Cache/Messaging** | Redis | 7.4 | Caching, WebSocket pub/sub | Fast in-memory storage, pub/sub for real-time |
| **Deployment** | Railway | Usage-based ($5 trial) | Infrastructure | Simple deployment, managed PostgreSQL + Redis |
| **LLM Hosting** | Modal/Replicate/RunPod | TBD | Production LLM inference | GPU endpoints for cloud-hosted models |

---

## Project Structure

```
supertutors/
├── frontend/                          # React TypeScript Vite app
│   ├── src/
│   │   ├── components/
│   │   │   ├── ui/                    # shadcn/ui components (Button, Input, Dialog, etc.)
│   │   │   └── custom/                # Custom educational components
│   │   │       ├── ChatCanvas.tsx     # Drawing overlay with 8-color toolbox
│   │   │       ├── CelebrationOverlay.tsx  # Balloons, confetti, flash text
│   │   │       ├── ConversationThread.tsx  # Chat message list with auto-scroll
│   │   │       ├── MathRenderer.tsx   # KaTeX integration wrapper
│   │   │       ├── VoiceInputButton.tsx    # Speech-to-text trigger
│   │   │       ├── ImageUploadButton.tsx   # Image upload with preview
│   │   │       └── TTSToggle.tsx      # Text-to-speech control
│   │   ├── logic/                     # Kea state management logic stores
│   │   │   ├── appLogic.ts            # Global app state
│   │   │   ├── conversationLogic.ts   # Chat state, messages, threads
│   │   │   ├── canvasLogic.ts         # Drawing state, colors, tools
│   │   │   ├── celebrationLogic.ts    # Streak tracking, celebration triggers
│   │   │   └── settingsLogic.ts       # TTS, preferences
│   │   ├── lib/
│   │   │   ├── api.ts                 # API client (fetch/axios wrappers)
│   │   │   ├── socket.ts              # Socket.IO client setup
│   │   │   └── utils.ts               # Helper functions
│   │   ├── types/
│   │   │   └── index.ts               # TypeScript type definitions
│   │   ├── assets/
│   │   │   ├── audio/                 # 7+ audio cheer variations
│   │   │   └── images/                # Logo, celebration assets
│   │   ├── App.tsx                    # Root component
│   │   ├── main.tsx                   # Entry point
│   │   └── index.css                  # Tailwind CSS imports
│   ├── public/                        # Static assets
│   ├── tailwind.config.js             # Tailwind CSS v4.0 config
│   ├── tsconfig.json                  # TypeScript configuration
│   ├── vite.config.ts                 # Vite build configuration
│   └── package.json
│
├── backend/                           # Python Flask API
│   ├── app/
│   │   ├── __init__.py                # Flask app factory
│   │   ├── routes/
│   │   │   ├── chat.py                # Chat endpoints (/api/chat)
│   │   │   ├── image.py               # Image upload + OCR (/api/image/upload)
│   │   │   ├── voice.py               # Speech-to-text (/api/voice/transcribe)
│   │   │   └── conversation.py        # Thread management (/api/conversations)
│   │   ├── services/
│   │   │   ├── llm_service.py         # Ollama integration, prompt engineering
│   │   │   ├── sympy_service.py       # SymPy computational engine
│   │   │   ├── vision_service.py      # Image OCR via vision-capable LLM
│   │   │   └── socratic_guard.py      # Architectural constraint: blocks direct answers
│   │   ├── models/
│   │   │   ├── conversation.py        # SQLAlchemy ORM: Conversation model
│   │   │   ├── message.py             # SQLAlchemy ORM: Message model
│   │   │   └── student.py             # SQLAlchemy ORM: Student (user) model
│   │   ├── utils/
│   │   │   ├── validators.py          # Input validation
│   │   │   └── errors.py              # Error handling utilities
│   │   ├── config.py                  # Configuration (dev/prod environments)
│   │   └── extensions.py              # Flask extensions (db, socketio, cors)
│   ├── migrations/                    # Database migrations (Alembic)
│   ├── tests/                         # Backend unit + integration tests
│   ├── requirements.txt               # Python dependencies
│   └── run.py                         # Application entry point
│
├── docs/                              # Project documentation
│   ├── PRD.md                         # Product Requirements Document
│   ├── ux-design-specification.md    # UX Design Specification
│   ├── architecture.md                # This file
│   └── bmm-workflow-status.yaml      # Workflow progress tracking
│
└── README.md                          # Project overview and setup
```

---

## Functional Area to Architecture Mapping

| Functional Area | Frontend Components | Backend Services | Database Models | Key Technologies |
| --------------- | ------------------- | ---------------- | --------------- | ---------------- |
| **Conversation Management** | ConversationThread, MathRenderer | llm_service, socratic_guard, chat routes | Conversation, Message | React, Kea, KaTeX, Flask, Ollama, SymPy |
| **Multimodal Input - Text** | Input, Textarea (shadcn) | chat routes | Message | React, Flask-SocketIO |
| **Multimodal Input - Voice** | VoiceInputButton | voice routes, speech-to-text API | Message | Web Speech API / external STT |
| **Multimodal Input - Images** | ImageUploadButton, Dialog | image routes, vision_service | Message (with image URL) | Ollama Vision, Flask |
| **Multimodal Input - Drawing** | ChatCanvas | chat routes (canvas image persistence) | Message (with canvas image) | HTML5 Canvas API, Flask |
| **Mathematical Computation** | MathRenderer | sympy_service | N/A | SymPy, KaTeX |
| **Visual Problem Solving (Canvas)** | ChatCanvas (8-color toolbox, overlay) | N/A (client-side drawing) | Message (canvas screenshots) | HTML5 Canvas, Pointer Events API |
| **Celebration System** | CelebrationOverlay, audio playback | N/A (client-side animations) | N/A | CSS animations, SVG, Audio API |
| **Math Rendering** | MathRenderer | N/A | N/A | KaTeX, LaTeX |
| **Text-to-Speech** | TTSToggle | N/A (client-side TTS) | N/A | Web Speech API |
| **User Experience (Responsive, A11y)** | All components, Radix UI primitives | N/A | N/A | Tailwind CSS, ARIA labels, keyboard nav |

---

## Technology Stack Details

### Frontend Stack

**Core Framework:**
- **React 18.3.1:** Component-based UI, concurrent rendering for smooth animations
- **TypeScript 5.7.x:** Type safety for complex state management (Kea logic stores, canvas state)
- **Vite 6.x:** Lightning-fast dev server (HMR for canvas/celebration iteration), optimized production builds

**UI/Styling:**
- **shadcn/ui (latest 2025):** Copy-paste accessible components (Button, Input, Dialog, Toast, etc.)
- **Radix UI v1.x:** Unstyled, accessible primitives (foundation for shadcn/ui)
- **Tailwind CSS v4.0:** Utility-first CSS, new high-performance engine (5x faster builds)

**State Management:**
- **Kea 3.1.6:** Composable state management, connects 25+ logic stores via parent appLogic

**Math & Rendering:**
- **KaTeX (via react-katex 3.1.0):** Fast LaTeX rendering for inline and display math equations

**Real-time Communication:**
- **Socket.IO Client:** WebSocket connection to Flask-SocketIO backend for chat messages

**Additional Libraries:**
- **Pointer Events API:** Unified touch/mouse/stylus input for canvas drawing
- **Web Speech API:** Speech-to-text (voice input) and text-to-speech (TTS)
- **HTML5 Canvas API:** Drawing surface for visual problem-solving
- **Audio API:** Audio cheer playback (7+ variations)

### Backend Stack

**Core Framework:**
- **Flask 3.1.2:** Lightweight Python web framework, flexible routing, production-ready

**Extensions:**
- **Flask-SocketIO 5.5.1:** Real-time bi-directional communication (WebSocket + long-polling fallback)
- **Flask-CORS 6.0.1:** Cross-Origin Resource Sharing for frontend API access
- **SQLAlchemy:** ORM for PostgreSQL database interactions
- **Alembic:** Database migration management

**Math & AI:**
- **SymPy 1.14.0:** Symbolic mathematics for deterministic computational accuracy
- **Ollama Python 0.6.0:** LLM integration (local dev: Llama 3.2 Vision via Ollama; production: cloud GPU endpoints)

**Vision & Multimodal:**
- **Vision-capable LLM (via Ollama):** OCR and handwriting recognition from uploaded images

### Data Layer

**Primary Database:**
- **PostgreSQL 18:** Relational database for structured data (conversations, messages, students)
  - **JSON columns:** For flexible message metadata (canvas images, celebration streaks)
  - **Full-text search:** For conversation history search (future feature)

**Cache & Messaging:**
- **Redis 7.4:** In-memory data store
  - **Caching:** LLM prompt/response caching to reduce inference costs
  - **Pub/Sub:** WebSocket message distribution across multiple Flask workers

### Deployment & Infrastructure

**Hosting Platform:**
- **Railway:** All-in-one platform for frontend + backend + managed PostgreSQL + Redis
  - **Pricing:** $5 trial credit, then usage-based (Hobby plan includes $5/month)
  - **Services:**
    - Frontend (Vite static build served via Railway)
    - Backend (Flask API with Flask-SocketIO)
    - PostgreSQL (managed database)
    - Redis (managed cache)

**LLM Inference:**
- **Local Development:** Ollama running on Mac (Llama 3.2 Vision)
- **Production:** Cloud GPU endpoint (Modal, Replicate, or RunPod) for hosted inference
  - **Model:** TBD based on cost/performance testing (candidates: Llama 3.2 Vision, Mistral, etc.)

---

## Integration Points

### Frontend ↔ Backend Communication

**REST API Endpoints:**
- `POST /api/chat/send` - Send student message, receive tutor response (Socratic question)
- `POST /api/image/upload` - Upload image, extract problem via Vision AI OCR
- `POST /api/voice/transcribe` - Convert voice recording to text
- `GET /api/conversations/:id` - Retrieve conversation thread
- `POST /api/conversations` - Create new conversation thread

**WebSocket Events (via Socket.IO):**
- `student_message` (client → server) - Student sends chat message
- `tutor_response` (server → client) - Tutor responds with Socratic question
- `tutor_typing` (server → client) - Typing indicator while LLM generates response
- `celebration_trigger` (server → client) - Notify client to trigger celebration (3 correct in a row)

**Request/Response Format:**
```json
// POST /api/chat/send
{
  "conversation_id": "uuid",
  "message": "Is the answer x = 5?",
  "canvas_image": "data:image/png;base64,..." // optional
}

// Response
{
  "success": true,
  "data": {
    "message_id": "uuid",
    "tutor_response": "Great thinking! What makes you say x = 5? Can you explain your reasoning?",
    "is_correct": true, // for celebration tracking
    "streak_count": 2,
    "latex_equations": ["x = 5"]
  }
}
```

### Backend ↔ SymPy Integration

**Purpose:** Deterministic mathematical computation for 100% accuracy

**Flow:**
1. Student submits answer → Backend extracts mathematical expression
2. Backend calls `sympy_service.py` → SymPy validates/computes correct answer
3. LLM uses SymPy result to inform Socratic response (never gives answer directly)

**Example:**
```python
# sympy_service.py
from sympy import symbols, solve, simplify

def validate_equation(student_answer: str, problem: str) -> dict:
    """
    Returns: {
        "is_correct": bool,
        "correct_answer": str,  # for internal use, never shown to student
        "symbolic_form": str
    }
    """
    x = symbols('x')
    student_expr = simplify(student_answer)
    correct_expr = solve(problem, x)[0]
    return {
        "is_correct": student_expr == correct_expr,
        "correct_answer": str(correct_expr),
        "symbolic_form": str(student_expr)
    }
```

### Backend ↔ Ollama (LLM) Integration

**Local Development:**
- Ollama server runs locally on Mac
- Python client (`ollama.Client()`) connects to `http://localhost:11434`
- Model: `llama3.2-vision` for text + image processing

**Production:**
- Cloud GPU endpoint (Modal/Replicate/RunPod)
- REST API calls to hosted model inference
- Model: TBD (cost/performance optimization)

**Socratic Guard Enforcement:**
```python
# socratic_guard.py
def enforce_socratic_method(llm_response: str) -> str:
    """
    Architectural constraint: Never allow direct answers.
    Rewrites LLM response if it contains direct answers.
    """
    forbidden_phrases = ["the answer is", "x =", "x equals", "the solution is"]

    if any(phrase in llm_response.lower() for phrase in forbidden_phrases):
        # Rewrite as Socratic question
        return rewrite_as_question(llm_response)

    return llm_response
```

### Backend ↔ PostgreSQL

**ORM Models:**
```python
# models/conversation.py
class Conversation(db.Model):
    id = db.Column(UUID, primary_key=True)
    student_id = db.Column(UUID, db.ForeignKey('student.id'))
    created_at = db.Column(DateTime, default=datetime.utcnow)
    topic = db.Column(String)  # e.g., "Algebra - Solving Equations"
    messages = db.relationship('Message', backref='conversation', lazy=True)

# models/message.py
class Message(db.Model):
    id = db.Column(UUID, primary_key=True)
    conversation_id = db.Column(UUID, db.ForeignKey('conversation.id'))
    sender = db.Column(String)  # 'student' or 'tutor'
    content = db.Column(Text)
    timestamp = db.Column(DateTime, default=datetime.utcnow)
    metadata = db.Column(JSON)  # {canvas_image, streak_count, is_correct, etc.}
```

---

## Novel Architectural Pattern: ChatCanvas Overlay

**Problem:** Students need to draw diagrams/graphs while maintaining chat context - traditional UIs force "chat OR draw" choice.

**Solution:** Semi-transparent canvas overlay that never blocks text input.

**Architecture:**

**Frontend (React + HTML5 Canvas):**
- **Component:** `ChatCanvas.tsx`
- **State Management:** `canvasLogic.ts` (Kea)
  - `isCanvasVisible`: boolean
  - `selectedColor`: string (1 of 8 colors)
  - `drawingHistory`: Array of stroke objects
  - `canvasImage`: base64 PNG screenshot

**Drawing Flow:**
1. User toggles canvas button → `canvasLogic.setCanvasVisible(true)`
2. Canvas overlay slides in (CSS transform), z-index: 10
3. User draws with Pointer Events API → strokes saved to `drawingHistory`
4. User toggles canvas off → Canvas converts to PNG via `toDataURL()`
5. PNG sent to backend as part of message metadata

**Backend Integration:**
- Canvas images stored as base64 in `Message.metadata.canvas_image`
- Vision AI can analyze student's drawings if needed

**Z-Index Layering:**
- Chat messages: `z-index: 1`
- Canvas overlay: `z-index: 10`
- Color picker toolbox: `z-index: 11`
- Text input area: `z-index: 100` (never blocked)

**Platform Adaptations:**
- **Desktop:** 70-80% viewport, top-right overlay
- **Tablet:** Full screen minus input bar
- **Mobile:** Full screen minus input bar, bottom sheet for colors

---

## Implementation Patterns (Consistency Rules for AI Agents)

### Naming Conventions

| Category | Convention | Example | Enforcement |
| -------- | ---------- | ------- | ----------- |
| **React Components** | PascalCase | `ChatCanvas.tsx`, `VoiceInputButton.tsx` | All agents MUST use PascalCase for component files |
| **Kea Logic Stores** | camelCase + "Logic" suffix | `conversationLogic.ts`, `canvasLogic.ts` | All agents MUST follow this pattern |
| **API Endpoints** | kebab-case, plural nouns | `/api/conversations`, `/api/chat/send` | REST conventions, plural for collections |
| **Database Tables** | snake_case, plural | `conversations`, `messages`, `students` | PostgreSQL convention |
| **Database Columns** | snake_case | `student_id`, `created_at`, `is_correct` | PostgreSQL convention |
| **Environment Variables** | SCREAMING_SNAKE_CASE | `DATABASE_URL`, `OLLAMA_API_KEY` | Standard convention |
| **CSS Classes** | Tailwind utilities only | `bg-blue-500`, `text-lg`, `p-4` | No custom CSS classes unless absolutely necessary |

### Code Organization Patterns

**Frontend:**
- **Components:** One component per file, exported as default
- **Logic Stores:** One logic store per file, use `kea()` factory
- **Types:** Centralized in `types/index.ts`, interfaces prefixed with `I` (e.g., `IMessage`)
- **API Calls:** Centralized in `lib/api.ts`, use async/await pattern
- **Tests:** Co-located with components (`ChatCanvas.test.tsx`)

**Backend:**
- **Routes:** Grouped by feature in `routes/` folder, blueprints for modularity
- **Services:** Business logic in `services/`, pure functions where possible
- **Models:** SQLAlchemy ORM in `models/`, one model per file
- **Tests:** Separate `tests/` folder, use pytest

### API Response Format

**Success Response:**
```json
{
  "success": true,
  "data": {
    // response payload
  }
}
```

**Error Response:**
```json
{
  "success": false,
  "error": {
    "code": "INVALID_INPUT",
    "message": "Please enter your answer",
    "details": {} // optional
  }
}
```

**All agents MUST use this format for API responses.**

### Error Handling Pattern

**Frontend:**
```typescript
// lib/api.ts
async function sendMessage(message: string): Promise<IApiResponse> {
  try {
    const response = await fetch('/api/chat/send', {
      method: 'POST',
      body: JSON.stringify({ message }),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('API Error:', error);
    return {
      success: false,
      error: {
        code: 'NETWORK_ERROR',
        message: 'Connection failed. Please try again.',
      },
    };
  }
}
```

**Backend:**
```python
# routes/chat.py
@chat_bp.route('/send', methods=['POST'])
def send_message():
    try:
        data = request.json
        validate_input(data)  # raises ValueError if invalid

        # Process message
        response = process_chat(data)

        return jsonify({
            "success": True,
            "data": response
        }), 200

    except ValueError as e:
        return jsonify({
            "success": False,
            "error": {
                "code": "INVALID_INPUT",
                "message": str(e)
            }
        }), 400

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return jsonify({
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "Something went wrong. Please try again."
            }
        }), 500
```

**All agents MUST follow these error handling patterns.**

### Logging Strategy

**Frontend:**
- **Development:** `console.log()` for debugging
- **Production:** Structured logging to external service (e.g., LogRocket, Sentry)
- **Format:** `[Component/Logic] Action: Details`
  - Example: `[ChatCanvas] Drawing started: color=blue`

**Backend:**
- **Library:** Python `logging` module
- **Levels:** DEBUG (dev only), INFO (normal operations), WARNING (recoverable issues), ERROR (failures)
- **Format:** `[timestamp] [level] [module] message`
  - Example: `[2025-11-03 14:23:45] [INFO] [llm_service] Generating Socratic response`

**All agents MUST log API calls, LLM interactions, and errors.**

### State Management Pattern (Kea)

**All Kea logic stores MUST follow this structure:**

```typescript
// conversationLogic.ts
import { kea } from 'kea';
import type { conversationLogicType } from './conversationLogicType';

export const conversationLogic = kea<conversationLogicType>({
  path: ['logic', 'conversation'],

  actions: {
    sendMessage: (message: string) => ({ message }),
    receiveMessage: (message: IMessage) => ({ message }),
    // ... more actions
  },

  reducers: {
    messages: [
      [] as IMessage[],
      {
        receiveMessage: (state, { message }) => [...state, message],
      },
    ],
    // ... more reducers
  },

  listeners: ({ actions }) => ({
    sendMessage: async ({ message }) => {
      // API call, side effects
      const response = await api.sendMessage(message);
      actions.receiveMessage(response.data);
    },
  }),
});
```

**All agents MUST generate TypeScript types with `kea-typegen`.**

---

## Data Architecture

### Database Schema

**Conversations Table:**
| Column | Type | Constraints | Description |
| ------ | ---- | ----------- | ----------- |
| `id` | UUID | PRIMARY KEY | Unique conversation identifier |
| `student_id` | UUID | FOREIGN KEY → students.id | Student who owns conversation |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Conversation start time |
| `topic` | VARCHAR(255) | NULL | e.g., "Algebra - Solving Equations" |

**Messages Table:**
| Column | Type | Constraints | Description |
| ------ | ---- | ----------- | ----------- |
| `id` | UUID | PRIMARY KEY | Unique message identifier |
| `conversation_id` | UUID | FOREIGN KEY → conversations.id | Parent conversation |
| `sender` | VARCHAR(10) | NOT NULL, CHECK (sender IN ('student', 'tutor')) | Message sender |
| `content` | TEXT | NOT NULL | Message text content |
| `timestamp` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Message timestamp |
| `metadata` | JSONB | NULL | Flexible data: `{canvas_image, is_correct, streak_count, latex_equations}` |

**Students Table:**
| Column | Type | Constraints | Description |
| ------ | ---- | ----------- | ----------- |
| `id` | UUID | PRIMARY KEY | Unique student identifier |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Account creation time |
| `preferences` | JSONB | NULL | `{tts_enabled, celebration_enabled}` |

**Indexes:**
- `conversations.student_id` - For fetching user's conversation history
- `messages.conversation_id` - For retrieving all messages in a thread
- `messages.timestamp` - For chronological ordering

---

## API Contracts

### REST Endpoints

**Chat Endpoints:**

`POST /api/chat/send`
- **Request:** `{conversation_id: UUID, message: string, canvas_image?: string}`
- **Response:** `{success: true, data: {message_id: UUID, tutor_response: string, is_correct: bool, streak_count: int, latex_equations: string[]}}`
- **Status Codes:** 200 (success), 400 (invalid input), 500 (server error)

`GET /api/conversations/:id`
- **Response:** `{success: true, data: {id: UUID, topic: string, messages: IMessage[]}}`
- **Status Codes:** 200 (success), 404 (not found), 500 (server error)

`POST /api/conversations`
- **Request:** `{topic?: string}`
- **Response:** `{success: true, data: {conversation_id: UUID}}`
- **Status Codes:** 201 (created), 500 (server error)

**Image Upload:**

`POST /api/image/upload`
- **Request:** `multipart/form-data {image: File, conversation_id: UUID}`
- **Response:** `{success: true, data: {extracted_text: string, confidence: float}}`
- **Status Codes:** 200 (success), 400 (invalid image), 413 (file too large), 500 (server error)

**Voice Transcription:**

`POST /api/voice/transcribe`
- **Request:** `multipart/form-data {audio: File}`
- **Response:** `{success: true, data: {transcription: string}}`
- **Status Codes:** 200 (success), 400 (invalid audio), 500 (server error)

### WebSocket Events

**Client → Server:**
- `student_message` - `{conversation_id: UUID, message: string}`

**Server → Client:**
- `tutor_response` - `{message_id: UUID, content: string, is_correct: bool, streak_count: int}`
- `tutor_typing` - `{conversation_id: UUID, is_typing: bool}`
- `celebration_trigger` - `{type: string, message: string}` (when streak_count === 3)

---

## Security Architecture

**Authentication:** Not implemented in MVP (single-user dev environment)

**Future (Production):**
- OAuth 2.0 or JWT-based authentication
- Session management via Flask-Session + Redis

**CORS Configuration:**
```python
# app/__init__.py
from flask_cors import CORS

CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:5173", "https://supertutors.railway.app"],
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type", "Authorization"],
    }
})
```

**Input Validation:**
- **Frontend:** TypeScript type checking, form validation
- **Backend:** Pydantic models or Flask-WTF for request validation
- **Database:** SQLAlchemy ORM prevents SQL injection

**Data Protection:**
- **In Transit:** HTTPS for production (Railway provides SSL certificates)
- **At Rest:** PostgreSQL encryption (Railway managed)
- **Secrets:** Environment variables, never hardcoded

**Rate Limiting:** Not implemented in MVP (Future: Flask-Limiter)

---

## Performance Considerations

### Response Time NFRs

- **Text-based questions:** <2 seconds from student submit → tutor response
- **Image upload + OCR:** <5 seconds from upload → extracted text confirmation
- **Canvas rendering:** 60 FPS drawing performance (smooth strokes)
- **Celebration animations:** 60 FPS animations (balloons, confetti)

### Optimization Strategies

**Frontend:**
- **Code Splitting:** Vite automatic code splitting for faster initial load
- **Lazy Loading:** React.lazy() for non-critical components (CelebrationOverlay, ChatCanvas)
- **Image Optimization:** Compress canvas screenshots before upload (WebP format)
- **Animation Performance:** CSS transforms (GPU-accelerated) for canvas slide-in, celebration overlays

**Backend:**
- **LLM Response Caching:** Redis cache for identical prompts (reduces inference costs)
- **Database Query Optimization:** Indexed queries, pagination for large conversation threads
- **WebSocket Connection Pooling:** Reuse connections for multiple messages

**Infrastructure:**
- **CDN:** Serve static assets (audio cheers, celebration assets) from CDN (future)
- **Database Connection Pooling:** SQLAlchemy connection pooling for concurrent requests

---

## Deployment Architecture

### Railway Services

**Service 1: Frontend (Vite Build)**
- **Build Command:** `npm run build`
- **Start Command:** Serve static files via Railway's built-in static hosting
- **Environment Variables:** `VITE_API_URL`, `VITE_WS_URL`

**Service 2: Backend (Flask API)**
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `gunicorn -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker -w 1 run:app`
- **Environment Variables:** `DATABASE_URL`, `REDIS_URL`, `OLLAMA_API_KEY`, `FLASK_ENV`
- **Port:** 5000 (Railway auto-detects)

**Service 3: PostgreSQL (Managed)**
- **Railway-provided:** Automatic backups, connection pooling
- **Connection String:** Injected as `DATABASE_URL` environment variable

**Service 4: Redis (Managed)**
- **Railway-provided:** In-memory caching, pub/sub for WebSocket
- **Connection String:** Injected as `REDIS_URL` environment variable

### Production LLM Inference

**Option 1: Modal**
- Deploy Llama 3.2 Vision as serverless function
- Pay-per-inference pricing
- Cold start: ~5s (acceptable for <5s NFR)

**Option 2: Replicate**
- Hosted model inference via REST API
- Pricing: Per-second GPU usage
- Easy integration with Python `replicate` library

**Option 3: RunPod**
- Dedicated GPU instances
- More cost-effective for high usage
- Requires manual scaling

**Decision:** Test all three during implementation, select based on cost/performance.

---

## Development Environment

### Prerequisites

**Required Software:**
- **Node.js:** v18+ (for Vite, React, TypeScript)
- **Python:** 3.9+ (for Flask, SymPy, Ollama client)
- **PostgreSQL:** 14+ (local dev database)
- **Redis:** 7.x (local dev cache)
- **Ollama:** Latest (local LLM inference)

**Optional:**
- **Docker:** For containerized PostgreSQL + Redis (alternative to local installs)
- **Postman/Insomnia:** API testing

### Setup Commands

**Frontend Setup:**
```bash
cd frontend
npm install
npm run dev  # Starts Vite dev server on http://localhost:5173
```

**Backend Setup:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Initialize database
flask db upgrade

# Start Flask server
python run.py  # Runs on http://localhost:5000
```

**Ollama Setup (Local LLM):**
```bash
# Install Ollama from https://ollama.ai
ollama pull llama3.2-vision  # Download vision-capable model
ollama serve  # Start server on http://localhost:11434
```

**Database Setup (Docker alternative):**
```bash
docker-compose up -d  # Starts PostgreSQL + Redis containers
```

---

## Architecture Decision Records (ADRs)

### ADR-001: Use Vite instead of Create React App

**Status:** Accepted
**Date:** 2025-11-03
**Context:** Need fast development iteration for canvas animations and celebration effects.
**Decision:** Use Vite for React + TypeScript setup.
**Rationale:** Vite provides instant HMR (Hot Module Replacement), significantly faster than CRA. Critical for rapid iteration on canvas drawing UX and celebration animations.
**Consequences:** Faster dev experience, smaller bundle size, better developer satisfaction.

---

### ADR-002: Use Kea for State Management (not Zustand/Redux)

**Status:** Accepted
**Date:** 2025-11-03
**Context:** PRD specifies Kea for state management. Kea has declining adoption in 2025 (vs. Zustand).
**Decision:** Stick with Kea as specified in PRD.
**Rationale:** User explicitly confirmed preference for Kea over Zustand. Kea 3.1.6 is stable and functional.
**Consequences:** Smaller community support, but composable state management works well for SuperTutors' complexity (25+ logic stores: conversation, canvas, celebration, settings).

---

### ADR-003: Use SymPy for Mathematical Computation

**Status:** Accepted
**Date:** 2025-11-03
**Context:** LLMs can make computational errors. SuperTutors requires 100% math accuracy.
**Decision:** Use SymPy 1.14.0 as deterministic computation engine.
**Rationale:** SymPy is the industry-standard Python library for symbolic mathematics. Provides 100% accurate computation, eliminating "confident but wrong" LLM errors.
**Consequences:** Backend must parse student answers into SymPy expressions, but ensures computational integrity (critical NFR).

---

### ADR-004: Use Flask-SocketIO for Real-Time Chat

**Status:** Accepted
**Date:** 2025-11-03
**Context:** Chat requires real-time bi-directional communication (student → tutor, tutor → student).
**Decision:** Use Flask-SocketIO 5.5.1 for WebSocket support.
**Rationale:** Flask-SocketIO integrates seamlessly with Flask, provides WebSocket + long-polling fallback, and supports multi-worker deployments with Redis pub/sub.
**Consequences:** Requires eventlet/gevent WSGI server (gunicorn with gevent workers). Adds complexity vs. REST-only, but enables typing indicators and instant message delivery.

---

### ADR-005: Deploy on Railway (not Vercel/AWS)

**Status:** Accepted
**Date:** 2025-11-03
**Context:** Need simple deployment for full-stack app (React frontend + Flask backend + PostgreSQL + Redis).
**Decision:** Use Railway for all services.
**Rationale:** Railway provides managed PostgreSQL + Redis, simple deployment (Git push), and $5 trial credit. Simpler than AWS, more full-stack-friendly than Vercel (which is frontend-focused).
**Consequences:** Usage-based pricing after $5 trial. Vendor lock-in (mitigated by Docker containers for future portability).

---

### ADR-006: Use Tailwind CSS v4.0 (not v3.x)

**Status:** Accepted
**Date:** 2025-11-03
**Context:** Tailwind v4.0 released with major performance improvements (5x faster builds, 100x faster incremental builds).
**Decision:** Use Tailwind CSS v4.0.
**Rationale:** New high-performance engine, automatic content detection (no manual config), CSS-first configuration. Aligns with "latest 2025" tech stack goal.
**Consequences:** Bleeding-edge version, but stable release. Potential migration overhead if breaking changes occur (mitigated by active community support).

---

### ADR-007: Architectural Constraint - Socratic Guard

**Status:** Accepted
**Date:** 2025-11-03
**Context:** SuperTutors must NEVER give direct answers (core pedagogical principle).
**Decision:** Implement `socratic_guard.py` service that rewrites LLM responses containing direct answers.
**Rationale:** Architecturally enforce Socratic integrity. Even if LLM fails prompt engineering, guard catches direct answers and rewrites as questions.
**Consequences:** Adds processing latency (~100ms), but ensures 100% Socratic integrity (critical success metric). All AI agents MUST route LLM responses through this guard.

---

_Generated by BMAD Decision Architecture Workflow v1.0_
_Date: 2025-11-03_
_For: caiojoao_
