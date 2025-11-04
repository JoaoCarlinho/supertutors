# supertutors - Epic Breakdown

**Author:** caiojoao
**Date:** 2025-11-03
**Project Level:** 2 (Medium - Multiple epics, 10+ stories)
**Target Scale:** 7 epics, 45 stories, ~60 developer-days (12 weeks)

---

## Overview

This document provides the detailed epic breakdown for supertutors, expanding on the high-level epic list in the [PRD](./PRD.md).

Each epic includes:

- Expanded goal and value proposition
- Complete story breakdown with user stories
- Acceptance criteria for each story
- Story sequencing and dependencies

**Epic Sequencing Principles:**

- Epic 1 establishes foundational infrastructure and initial functionality
- Subsequent epics build progressively, each delivering significant end-to-end value
- Stories within epics are vertically sliced and sequentially ordered
- No forward dependencies - each story builds only on previous work

---

## Epic 1: Foundation & Infrastructure Setup

**Business Goal:** Establish the technical foundation for the SuperTutors platform

**Value Proposition:** Enables all subsequent feature development with proper infrastructure, deployment pipeline, and development workflow

**Estimated Effort:** 6.5 developer-days

**Sprint Assignment:** Sprint 1 (Phase 1: Foundation)

### Stories

**Story 1.1: Initialize React + Vite Frontend Project**

As a developer,
I want a properly configured React + Vite project with TypeScript,
So that I can build modern, type-safe frontend features efficiently.

**Acceptance Criteria:**
1. Vite project created with React 18.3.1 and TypeScript
2. Tailwind CSS v4.0 configured with custom design tokens
3. shadcn/ui component library installed and configured
4. ESLint and Prettier configured for code quality
5. `npm run dev` starts development server successfully
6. Hot module replacement (HMR) works for instant feedback

**Prerequisites:** None (first story)

---

**Story 1.2: Initialize Flask Backend API**

As a developer,
I want a properly structured Flask API with WebSocket support,
So that I can build real-time backend features with clean architecture.

**Acceptance Criteria:**
1. Flask 3.1.2 project created with proper folder structure
2. Flask-SocketIO configured for WebSocket support
3. CORS configured for local development and Railway deployment
4. Python type hints enabled (mypy configuration)
5. Pylint configured for code quality
6. `flask run` starts API server successfully
7. Health check endpoint returns 200 OK

**Prerequisites:** None (parallel to 1.1)

---

**Story 1.3: Configure PostgreSQL Database**

As a developer,
I want a PostgreSQL database with ORM and migrations,
So that I can persist conversation data reliably with schema versioning.

**Acceptance Criteria:**
1. PostgreSQL 18 installed locally and configured on Railway
2. SQLAlchemy ORM configured with Flask integration
3. Alembic migrations set up with initial migration
4. Database connection pooling configured (max 20 connections)
5. Initial schema created (conversations, messages tables)
6. Indexes created on frequently queried columns
7. Database health check endpoint returns connection status

**Prerequisites:** Story 1.2 (Flask backend)

---

**Story 1.4: Configure Redis Cache**

As a developer,
I want a Redis cache with connection pooling,
So that I can cache LLM responses and conversation context for performance.

**Acceptance Criteria:**
1. Redis 7.4 installed locally and configured on Railway
2. redis-py client configured with connection pooling
3. Cache health check endpoint returns connection status
4. Basic cache operations work (set, get, expire)
5. TTL management configured (default 1 hour)
6. Cache key naming convention documented

**Prerequisites:** Story 1.2 (Flask backend)

---

**Story 1.5: Integrate Ollama LLM**

As a developer,
I want Ollama LLM integrated with proper service abstraction,
So that I can generate Socratic questions and validate responses using AI.

**Acceptance Criteria:**
1. Ollama installed locally with Llama 3.2 Vision model (11B)
2. LLM service abstraction layer created (isolates Ollama API calls)
3. Basic prompt/response flow works (send prompt, receive completion)
4. Timeout wrapper implemented (max 10s per LLM call)
5. Error handling for LLM failures (network, timeout, rate limit)
6. LLM health check endpoint returns model status
7. Example prompts tested successfully

**Prerequisites:** Story 1.2 (Flask backend)

---

**Story 1.6: Configure Railway Deployment**

As a developer,
I want automated deployment to Railway,
So that I can deploy changes quickly and reliably to production.

**Acceptance Criteria:**
1. Railway project created and linked to GitHub repository
2. Environment variables configured (DATABASE_URL, REDIS_URL, OLLAMA_API_URL)
3. PostgreSQL and Redis Railway add-ons provisioned
4. Build and deploy pipeline configured (nixpacks buildpack)
5. Start command configured: `gunicorn --worker-class eventlet -w 1 app:app`
6. Successful deployment to Railway staging environment
7. Health check endpoints accessible via Railway URL

**Prerequisites:** Stories 1.2, 1.3, 1.4 (backend infrastructure)

---

**Story 1.7: Implement Error Handling & Logging**

As a developer,
I want comprehensive error handling and structured logging,
So that I can debug issues quickly and provide graceful error experiences to users.

**Acceptance Criteria:**
1. Python logging configured with structured JSON format
2. Frontend error boundary component created (catches React errors)
3. Global error handler in Flask (catches unhandled exceptions)
4. Error response standardization (consistent JSON error format)
5. Logging levels configured (DEBUG for dev, INFO for prod)
6. Request/response logging middleware added
7. Error tracking works (errors logged to console for MVP)
8. Graceful degradation for LLM failures (user sees friendly message)

**Prerequisites:** Story 1.2 (Flask backend), Story 1.1 (React frontend)

---

## Epic 2: Core Chat Interface & Conversation Threading

**Business Goal:** Enable students to have persistent, multi-turn conversations with the AI tutor

**Value Proposition:** Core UX for student-tutor interaction - the primary user journey

**Estimated Effort:** 8 developer-days

**Sprint Assignment:** Sprint 2 (Phase 2: Core Chat Experience)

### Stories

**Story 2.1: Implement WebSocket Connection**

As a student,
I want reliable real-time communication with the tutor,
So that I can see responses instantly without page refreshes.

**Acceptance Criteria:**
1. SocketIO client configured in React
2. Connection/disconnection handlers implemented
3. Reconnection logic with exponential backoff (1s, 2s, 4s, 8s, max 30s)
4. Connection status indicator in UI (connected, disconnecting, disconnected)
5. Event listeners for `connect`, `disconnect`, `connect_error`
6. Heartbeat/ping mechanism to detect stale connections
7. WebSocket connection successful to Flask-SocketIO backend

**Prerequisites:** Epic 1 (Story 1.2 Flask backend, Story 1.1 React frontend)

---

**Story 2.2: Build Message Data Model**

As a developer,
I want well-designed database models for conversations and messages,
So that I can store and retrieve conversation data efficiently.

**Acceptance Criteria:**
1. `conversations` table created (id UUID, title TEXT, created_at TIMESTAMP, updated_at TIMESTAMP)
2. `messages` table created (id UUID, conversation_id FK, role ENUM, content TEXT, metadata JSONB, created_at TIMESTAMP)
3. Database relationships configured (one conversation has many messages)
4. Indexes created on `(conversation_id, created_at DESC)` for fast thread retrieval
5. SQLAlchemy models defined with type hints
6. Alembic migration created and applied
7. Basic CRUD operations tested (create conversation, add message, retrieve thread)

**Prerequisites:** Story 1.3 (PostgreSQL database)

---

**Story 2.3: Implement Real-Time Message Exchange**

As a student,
I want to send and receive messages in real-time,
So that the conversation feels natural and responsive.

**Acceptance Criteria:**
1. `message:send` event handler (client → server)
2. `message:receive` event handler (server → client)
3. Typing indicators implemented (`typing:start`, `typing:stop` events)
4. Message delivery confirmation (server sends ACK to client)
5. Message ordering guaranteed (server-side timestamps)
6. Duplicate message detection and prevention
7. Messages display in correct order in chat UI
8. Typing indicator shows when tutor is "thinking"

**Prerequisites:** Story 2.1 (WebSocket connection), Story 2.2 (Message data model)

---

**Story 2.4: Build Conversation Thread Persistence**

As a student,
I want my conversations saved automatically,
So that I can continue learning where I left off across sessions.

**Acceptance Criteria:**
1. Auto-save conversation to PostgreSQL on each message
2. Load conversation by thread_id endpoint (`GET /api/threads/:id`)
3. List recent threads endpoint (`GET /api/threads?limit=20`)
4. Thread metadata includes title, last message preview, updated_at timestamp
5. Auto-generate thread title from first student message (truncate at 50 chars)
6. Thread continuation works (load thread → send new message → appears in conversation)
7. Thread retention policy: keep all threads indefinitely for MVP

**Prerequisites:** Story 2.2 (Message data model), Story 2.3 (Message exchange)

---

**Story 2.5: Create Chat Input Component**

As a student,
I want an intuitive chat input field,
So that I can easily type and send messages to the tutor.

**Acceptance Criteria:**
1. Multiline textarea with auto-resize (max 5 lines before scrolling)
2. "Send" button (disabled when input is empty or only whitespace)
3. Enter-to-send functionality (Shift+Enter inserts newline)
4. Character count indicator (shows count after 100 characters)
5. Input clears after successful send
6. Input disabled while message is sending
7. Accessible labels and ARIA attributes for screen readers

**Prerequisites:** Story 1.1 (React frontend)

---

**Story 2.6: Create Message Display Component**

As a student,
I want to see my conversation history clearly,
So that I can review previous questions and tutor responses.

**Acceptance Criteria:**
1. Message bubble UI with distinct styles for student vs tutor messages
2. Student messages aligned right, tutor messages aligned left
3. Timestamps displayed below each message (relative time: "2 minutes ago")
4. Message status indicators (sending, sent, error) for student messages
5. Auto-scroll to bottom on new message received
6. Manual scroll preserves position (doesn't auto-scroll if user scrolled up)
7. Empty state message when no messages in thread
8. Accessible semantic HTML (role="log" for message container)

**Prerequisites:** Story 2.3 (Message exchange), Story 2.5 (Chat input)

---

**Story 2.7: Build Thread List Sidebar**

As a student,
I want to see my previous conversations,
So that I can continue old conversations or start new ones.

**Acceptance Criteria:**
1. Thread list UI in left sidebar (scrollable list of threads)
2. Each thread item shows title, last message preview (50 chars), timestamp
3. Thread selection (click thread → loads conversation in main panel)
4. "New Thread" button (creates new thread, clears chat)
5. Thread deletion (trash icon → confirms → deletes thread)
6. Active thread highlighted in sidebar
7. Responsive layout (sidebar collapses on mobile, accessible via menu icon)
8. Threads sorted by updated_at descending (most recent first)

**Prerequisites:** Story 2.4 (Thread persistence), Story 2.6 (Message display)

---

## Epic 3: Socratic Tutoring Engine

**Business Goal:** Deliver pedagogically sound Socratic questioning that guides students without giving answers

**Value Proposition:** Core educational methodology differentiator - the "secret sauce" of SuperTutors

**Estimated Effort:** 9.5 developer-days

**Sprint Assignment:** Sprint 3 (Phase 3: Socratic Intelligence)

### Stories

**Story 3.1: Design Socratic Guard Service**

As a product owner,
I want a well-designed Socratic Guard architecture,
So that the system reliably prevents direct answers and maintains pedagogical integrity.

**Acceptance Criteria:**
1. Socratic Guard service architecture documented (validation flow, retry logic)
2. Validation rules defined (detect direct answers, numerical solutions, step-by-step solutions)
3. Socratic Guard prompt template created (instructs LLM to validate responses)
4. Rule-based fallback logic designed (keyword detection for common answer patterns)
5. Test suite design: 50+ prompt/response pairs for validation testing
6. Retry logic specified (max 3 attempts before fallback to generic Socratic question)
7. Architecture review completed with team

**Prerequisites:** Epic 1 (Story 1.5 LLM integration)

---

**Story 3.2: Implement Socratic Guard Validator**

As a tutor,
I want the system to block direct answers automatically,
So that students are always guided through questions, never given solutions.

**Acceptance Criteria:**
1. LLM-based validator implemented (sends tutor response to LLM, asks "Does this give a direct answer?")
2. Validation response schema: `{is_direct_answer: bool, reason: string, confidence: float}`
3. Rule-based fallback for common patterns (regex: "the answer is", "= [number]", "step 1:", etc.)
4. Validation timeout: 5 seconds (fail-safe to "allow" on timeout)
5. Logging for all validation decisions (approved, rejected, reason)
6. Validation performance: <1 second average latency
7. Test suite passes: 50+ validation scenarios (45+ correct classifications = 90% accuracy)

**Prerequisites:** Story 3.1 (Guard design)

---

**Story 3.3: Integrate Guard into Conversation Flow**

As a student,
I want to only receive Socratic questions from the tutor,
So that I'm guided to discover answers myself rather than being told.

**Acceptance Criteria:**
1. Pre-send validation step added to message send flow (before sending to student)
2. Response regeneration on guard failure (new LLM call with "avoid direct answers" reinforcement)
3. Retry logic implemented (max 3 regeneration attempts)
4. Fallback to generic Socratic question after 3 failures ("What have you tried so far?")
5. Validation bypass flag for testing (environment variable: DISABLE_SOCRATIC_GUARD)
6. Validation adds <500ms to response time (measured via logging)
7. End-to-end test: student asks question → receives Socratic question → no direct answer given

**Prerequisites:** Story 3.2 (Guard validator), Story 2.3 (Message exchange)

---

**Story 3.4: Build Socratic Question Generation**

As a tutor,
I want to generate varied, context-appropriate Socratic questions,
So that I can guide students effectively based on their current understanding.

**Acceptance Criteria:**
1. Socratic prompting strategy documented (question types: clarifying, probing, leading, reflective)
2. Prompt templates created for each question type
3. Context injection implemented (last 5 messages included in prompt)
4. Question diversity algorithm (track recent question types, vary next question)
5. Topic-specific question generation (algebra vs geometry vs word problems)
6. Temperature tuning: 0.7 for creative yet consistent questions
7. Test: 10 consecutive questions show variety (no repeated question patterns)
8. Generated questions feel natural and encouraging

**Prerequisites:** Story 3.3 (Guard integration), Epic 1 (Story 1.5 LLM integration)

---

**Story 3.5: Implement Encouraging Feedback System**

As a student,
I want to receive positive, encouraging feedback from the tutor,
So that I stay motivated even when I'm struggling.

**Acceptance Criteria:**
1. Feedback phrase library created (50+ encouraging phrases: "Good thinking!", "You're on the right track!", etc.)
2. Feedback injection into tutor responses (prepend/append to Socratic questions)
3. Sentiment analysis implemented (detect student frustration via message content)
4. Adaptive encouragement (more supportive phrases when student is struggling)
5. Frustration detection: keywords like "I don't know", "I give up", "this is hard"
6. Escalated encouragement after 3 incorrect answers in a row
7. Test: frustrated student messages receive extra encouragement

**Prerequisites:** Story 3.4 (Question generation)

---

**Story 3.6: Build Conversation Context Management**

As a tutor,
I want to maintain conversation context efficiently,
So that I can reference previous messages without performance degradation.

**Acceptance Criteria:**
1. Context window implementation (last N messages, configurable, default N=5)
2. Context summarization for long conversations (>20 messages summarize to key points)
3. Context pruning strategy (keep: original question, key student answers, tutor guidance)
4. Redis caching for active conversation contexts (TTL: 1 hour)
5. Context retrieval performance: <100ms from cache
6. Context format: JSON array of {role, content, timestamp}
7. Response time target met: <2 seconds from student message to tutor response
8. Test: 50-message conversation maintains context correctly

**Prerequisites:** Story 1.4 (Redis cache), Story 3.4 (Question generation)

---

## Epic 4: Mathematical Computation & Rendering

**Business Goal:** Provide accurate mathematical computation and beautiful notation rendering

**Value Proposition:** Enables math-specific tutoring functionality - essential for 9th grade algebra/geometry

**Estimated Effort:** 9 developer-days

**Sprint Assignment:** Sprint 4 (Phase 4: Mathematical Capabilities)

### Stories

**Story 4.1: Integrate SymPy for Symbolic Math**

As a tutor,
I want symbolic math computation capabilities,
So that I can validate student answers and solve mathematical problems accurately.

**Acceptance Criteria:**
1. SymPy added to backend dependencies (version 1.12+)
2. SymPy service wrapper created (isolates SymPy API calls)
3. Symbolic expression parsing implemented (`sympify()` with error handling)
4. Timeout wrapper for long-running computations (max 5 seconds, then abort)
5. Error handling for invalid expressions (return user-friendly error message)
6. Basic operations tested: parse "x^2 + 2*x + 1", simplify to "(x+1)^2"
7. SymPy health check endpoint returns computation status

**Prerequisites:** Epic 1 (Story 1.2 Flask backend)

---

**Story 4.2: Implement Answer Validation**

As a tutor,
I want to validate student answers automatically,
So that I can provide immediate feedback on correctness.

**Acceptance Criteria:**
1. Answer comparison logic (numerical tolerance: ±0.001, symbolic equivalence)
2. Step-by-step solution generation using SymPy (`solve()`, `factor()`, `simplify()`)
3. Validation response schema: `{correct: bool, student_answer: str, expected_answer: str, explanation: str}`
4. Multiple valid forms detected (e.g., "x^2 - 1" and "(x-1)(x+1)" both correct)
5. Numerical approximation handling (π ≈ 3.14159, √2 ≈ 1.414)
6. Test cases: 20+ validation scenarios (algebra, geometry, fractions)
7. Validation performance: <500ms per answer check

**Prerequisites:** Story 4.1 (SymPy integration)

---

**Story 4.3: Add KaTeX Rendering**

As a student,
I want to see mathematical notation rendered beautifully,
So that equations are easy to read and understand.

**Acceptance Criteria:**
1. KaTeX library integrated in frontend (version 0.16+)
2. Math component created (renders LaTeX strings inline and display modes)
3. LaTeX string parsing in messages (detect $inline$ and $$display$$ syntax)
4. Error handling for invalid LaTeX (show raw LaTeX + error message)
5. Rendering performance: <50ms per equation
6. Test rendering: fractions, exponents, radicals, Greek letters, integrals
7. Accessible alt text for screen readers (MathML fallback or aria-label)

**Prerequisites:** Epic 1 (Story 1.1 React frontend)

---

**Story 4.4: Implement LaTeX Input Support**

As a student,
I want to input mathematical notation using LaTeX,
So that I can express complex equations clearly.

**Acceptance Criteria:**
1. LaTeX input mode toggle in chat input (button: "Math Mode")
2. LaTeX preview pane (live preview of rendered equation as student types)
3. LaTeX shortcuts implemented (common symbols: π, ∫, √, ∑, ∞)
4. LaTeX syntax help tooltip (shows common syntax on hover)
5. LaTeX mode preserves spaces and special characters
6. Switch between plain text and LaTeX modes seamlessly
7. Test: input "\\frac{x^2}{2}" → preview shows x²/2 → sends as LaTeX → renders in message

**Prerequisites:** Story 4.3 (KaTeX rendering), Story 2.5 (Chat input)

---

**Story 4.5: Build Equation Solver**

As a tutor,
I want to solve equations symbolically,
So that I can validate student work and provide hints when needed.

**Acceptance Criteria:**
1. `solve()` wrapper for linear/quadratic equations (e.g., "x^2 - 5*x + 6 = 0")
2. `simplify()` wrapper for algebraic expressions (e.g., "(x+1)^2 - (x-1)^2")
3. `factor()` and `expand()` operations (e.g., factor "x^2 - 1" → "(x-1)(x+1)")
4. Basic calculus: `diff()` for derivatives, `integrate()` for integrals
5. Multiple solutions handled (e.g., "x^2 = 4" → solutions: [2, -2])
6. Unsolvable equations handled gracefully (return "No solution")
7. Test cases: 15+ equations (linear, quadratic, rational, trigonometric)

**Prerequisites:** Story 4.1 (SymPy integration)

---

**Story 4.6: Add Math Notation Parser**

As a student,
I want to type math in natural language,
So that I don't have to learn LaTeX syntax.

**Acceptance Criteria:**
1. Natural language to LaTeX conversion (e.g., "x squared" → "x^2")
2. Common notation detection (fractions: "1/2" → "\\frac{1}{2}", exponents: "x^2", radicals: "sqrt(x)")
3. Parsing error feedback (highlight invalid notation, suggest corrections)
4. Fallback to raw input on parse failure (send as plain text)
5. Parser handles mixed notation (e.g., "x^2 + 1/2")
6. Test cases: 20+ natural language inputs → correct LaTeX output
7. Parsing performance: <100ms per input

**Prerequisites:** Story 4.3 (KaTeX rendering), Story 4.4 (LaTeX input)

---

## Epic 5: Multimodal Problem Input

**Business Goal:** Allow students to input problems in the way that's most natural (text, image, drawing)

**Value Proposition:** Reduces friction, supports diverse learning styles - students can show work via photo or draw diagrams

**Estimated Effort:** 11 developer-days

**Sprint Assignment:** Sprint 5 (Phase 5: Multimodal Input)

### Stories

**Story 5.1: Implement Image Upload Component**

As a student,
I want to upload photos of math problems,
So that I don't have to type complex equations or diagrams.

**Acceptance Criteria:**
1. File input UI (drag-and-drop + click to upload)
2. Image preview before submission (thumbnail with "Remove" button)
3. File size validation (<5MB, show error if exceeded)
4. Supported format check (PNG, JPG, JPEG, WEBP)
5. Image compression for large files (resize to max 2000px width)
6. Upload progress indicator (spinner during upload)
7. Successful upload triggers image processing flow

**Prerequisites:** Epic 2 (Story 2.5 Chat input)

---

**Story 5.2: Integrate Vision AI OCR**

As a system,
I want to extract text and math notation from uploaded images,
So that students can submit photos of handwritten or printed problems.

**Acceptance Criteria:**
1. Vision AI API client configured (or Llama 3.2 Vision via Ollama)
2. Image-to-text extraction endpoint (`POST /api/ocr/extract`)
3. Math notation detection (identify LaTeX expressions in OCR output)
4. OCR error handling (unreadable image, unsupported content)
5. OCR response schema: `{extracted_text: str, confidence: float, math_detected: bool}`
6. Processing time: <5 seconds per image
7. Test cases: 10+ images (printed equations, handwritten notes, whiteboard photos)
8. Accuracy target: >80% correct extraction for clear images

**Prerequisites:** Epic 1 (Story 1.5 LLM integration - Vision model)

---

**Story 5.3: Build OCR Confirmation UI**

As a student,
I want to verify OCR extraction before submitting,
So that I can correct any mistakes in the recognized text.

**Acceptance Criteria:**
1. OCR result displayed to student (extracted text in editable textarea)
2. Confirm/Edit/Retry buttons
3. Inline editing of OCR output (textarea allows modifications)
4. Re-upload option (discard OCR result, upload different image)
5. Confirmation sends corrected text as student message
6. Visual indication of OCR confidence (<70% shows warning: "Please verify accuracy")
7. Accessible screen reader announcements for OCR results

**Prerequisites:** Story 5.1 (Image upload), Story 5.2 (Vision AI OCR)

---

**Story 5.4: Create Drawing Canvas Foundation**

As a student,
I want to draw on a canvas,
So that I can sketch graphs, diagrams, or show my work visually.

**Acceptance Criteria:**
1. KonvaJS library integrated (version 9+)
2. Canvas UI implemented (drawing area sized to fill available space)
3. Basic tools UI (toolbar with tool buttons)
4. Pen tool implemented (freehand drawing with mouse/touch)
5. Clear canvas button (confirm before clearing)
6. Canvas rendering performance: 60 FPS during drawing
7. Touch support for mobile/tablet drawing

**Prerequisites:** Epic 1 (Story 1.1 React frontend)

---

**Story 5.5: Add Canvas Drawing Tools**

As a student,
I want various drawing tools,
So that I can create precise diagrams and show mathematical work.

**Acceptance Criteria:**
1. Shape tools implemented (line, circle, rectangle, arrow)
2. Eraser tool (removes strokes or shapes)
3. Color picker (10+ preset colors + custom color selector)
4. Stroke width control (slider: 1px to 10px)
5. Undo/redo functionality (up to 20 actions)
6. Selection tool (select, move, resize, delete shapes)
7. Tool indicators (active tool highlighted in toolbar)

**Prerequisites:** Story 5.4 (Canvas foundation)

---

**Story 5.6: Implement Canvas Export & Processing**

As a student,
I want to submit my canvas drawing to the tutor,
So that the tutor can see my visual work and provide guidance.

**Acceptance Criteria:**
1. Canvas-to-image conversion (export as PNG, max 1920x1080)
2. Canvas snapshot for LLM processing (captures all layers)
3. "Submit Drawing" button (sends canvas image to tutor)
4. Canvas image integration with Vision AI OCR (extract any text/math from drawing)
5. Drawing sent as special message type (displays image + extracted text)
6. Canvas clears after successful submission (confirm before clearing)
7. Export performance: <1 second for typical canvas (20-30 shapes)

**Prerequisites:** Story 5.5 (Drawing tools), Story 5.2 (Vision AI OCR)

---

**Story 5.7: Build ChatCanvas Overlay Architecture**

As a student,
I want the drawing canvas to overlay the chat smoothly,
So that I can draw while still seeing the conversation context.

**Acceptance Criteria:**
1. Z-index layering implemented (messages z-1, canvas z-10, toolbox z-11, input z-100)
2. Canvas toggle button in chat interface (floating action button)
3. Canvas show/hide animations (slide in from right, fade background)
4. Responsive canvas sizing (adapts to viewport, maintains aspect ratio)
5. Chat messages remain visible behind semi-transparent canvas overlay
6. Toolbox remains accessible on top of canvas
7. Chat input remains accessible (z-100 ensures always on top)
8. Mobile behavior: canvas full-screen mode, swipe to close
9. Accessibility: keyboard shortcut to toggle canvas (Ctrl+D)

**Prerequisites:** Story 5.6 (Canvas export), Epic 2 (Story 2.6 Message display)

---

## Epic 6: Celebration & Motivation System

**Business Goal:** Reinforce positive learning behaviors and maintain student engagement

**Value Proposition:** Increases motivation, reduces frustration, improves persistence through positive reinforcement

**Estimated Effort:** 6 developer-days

**Sprint Assignment:** Sprint 6 (Phase 6: Motivation & Engagement)

### Stories

**Story 6.1: Implement Streak Tracking**

As a system,
I want to track student answer streaks,
So that I can celebrate achievements and reinforce correct thinking.

**Acceptance Criteria:**
1. Streak counter added to conversation state (persisted in messages.metadata JSONB)
2. Streak increment on correct answer (validation result: correct=true)
3. Streak reset on incorrect answer (validation result: correct=false)
4. Streak persists across messages within session (Redis cache)
5. Streak does not persist across sessions (resets to 0 on new thread)
6. Streak displayed in UI (small badge showing current streak count)
7. Test: 3 correct answers → streak = 3, 1 incorrect → streak = 0

**Prerequisites:** Epic 4 (Story 4.2 Answer validation), Epic 3 (Story 3.6 Context management)

---

**Story 6.2: Build Celebration Trigger System**

As a system,
I want to trigger celebrations automatically on streak achievements,
So that students feel rewarded for their effort.

**Acceptance Criteria:**
1. Celebration detection (streak === 3 triggers celebration)
2. Celebration event emitted (`celebration:trigger` WebSocket event)
3. Celebration cooldown implemented (max 1 celebration per 2 minutes, prevent spam)
4. Celebration state management (Kea logic store: celebrationLogic)
5. Celebration metadata (achievement type: "3-in-a-row", timestamp)
6. Test: 3 correct answers → celebration triggers once, 6 correct → triggers twice

**Prerequisites:** Story 6.1 (Streak tracking), Epic 2 (Story 2.1 WebSocket)

---

**Story 6.3: Implement Audio Feedback**

As a student,
I want to hear a cheer sound when I answer correctly,
So that I feel immediate positive reinforcement.

**Acceptance Criteria:**
1. Audio cheer sound files added (3-5 variations: cheer1.mp3, cheer2.mp3, etc.)
2. Audio playback on correct answer (randomize variation to prevent monotony)
3. Volume control setting (default 50%, adjustable in UI)
4. Audio preloading for performance (<100ms playback latency)
5. Audio mute toggle (user preference persisted in localStorage)
6. Browser autoplay policy handling (request permission on first play)
7. Test: correct answer → plays cheer sound within 100ms

**Prerequisites:** Story 6.2 (Celebration triggers), Epic 4 (Story 4.2 Answer validation)

---

**Story 6.4: Build Visual Celebration Animations**

As a student,
I want to see fun animations when I achieve a streak,
So that I feel celebrated and motivated to continue.

**Acceptance Criteria:**
1. Balloon animation (3-5 balloons rise from bottom of screen)
2. Confetti animation (confetti falls from top, physics-based)
3. Flash text animation ("Great job!", "Awesome!", "You're on fire!")
4. Animation performance: 60 FPS (use CSS transforms for hardware acceleration)
5. Animation duration: 3 seconds total (balloons 2s, confetti 3s, flash text 1.5s)
6. Animations respect reduced motion preference (prefers-reduced-motion: reduce)
7. Test: visual regression testing, frame rate monitoring

**Prerequisites:** Story 6.2 (Celebration triggers)

---

**Story 6.5: Add Celebration UI Components**

As a student,
I want the full celebration experience,
So that I feel rewarded and encouraged to keep learning.

**Acceptance Criteria:**
1. Celebration overlay component created (full-screen overlay with semi-transparent background)
2. Animation sequencing (balloons → confetti → flash text in order)
3. Auto-dismiss after 3 seconds (overlay fades out)
4. Skip celebration button (small "×" in corner, allows immediate dismissal)
5. Celebration doesn't block interaction (can still type during celebration)
6. Accessibility: celebration announced to screen readers ("Achievement: 3 correct answers in a row!")
7. End-to-end test: 3 correct answers → full celebration sequence plays

**Prerequisites:** Story 6.3 (Audio feedback), Story 6.4 (Visual animations)

---

## Epic 7: Accessibility & Responsive Polish

**Business Goal:** Ensure SuperTutors is usable by all students across all devices

**Value Proposition:** WCAG 2.1 AA compliance, mobile/tablet support, inclusive design - makes the product usable by everyone

**Estimated Effort:** 10 developer-days

**Sprint Assignment:** Sprint 7 (Phase 7: Accessibility & Polish)

### Stories

**Story 7.1: Implement Keyboard Navigation**

As a keyboard-only user,
I want to navigate the entire app using only my keyboard,
So that I can use SuperTutors without a mouse.

**Acceptance Criteria:**
1. Tab order logical and sequential (follows visual layout)
2. Focus indicators visible on all interactive elements (2px outline, high contrast)
3. Keyboard shortcuts implemented (Ctrl+N: new thread, Ctrl+D: toggle canvas, Enter: send message)
4. Modal dialogs trap focus (Tab cycles within modal, Esc closes modal)
5. Skip navigation link (first tab stop, jumps to main content)
6. Focus management on route changes (focus moves to page heading)
7. Test: navigate entire app using only keyboard, complete full user journey

**Prerequisites:** Epic 2 (Chat UI), Epic 5 (Canvas)

---

**Story 7.2: Add Screen Reader Support**

As a screen reader user,
I want all content announced clearly,
So that I can understand the app structure and receive tutor messages.

**Acceptance Criteria:**
1. ARIA labels on all interactive elements (buttons, inputs, links)
2. ARIA live regions for dynamic content (role="log" for message container, aria-live="polite")
3. Semantic HTML structure (nav, main, aside, article, section)
4. Image alt text for all images (canvas drawings, uploaded images)
5. Form labels associated with inputs (for/id relationship or aria-labelledby)
6. Screen reader announcements for state changes ("Message sent", "Thread deleted")
7. Test with NVDA/JAWS: complete user journey, verify announcements correct

**Prerequisites:** Epic 2 (Chat UI), Epic 5 (Canvas UI)

---

**Story 7.3: Ensure Color Contrast Compliance**

As a user with low vision,
I want sufficient color contrast,
So that I can read all text clearly.

**Acceptance Criteria:**
1. Audit all text/background color combinations (use axe DevTools)
2. Fix any contrast ratios <4.5:1 (WCAG 2.1 AA requirement)
3. High-contrast mode option (user setting: increases all contrast to 7:1)
4. Color blindness testing (simulate deuteranopia, protanopia, tritanopia)
5. No information conveyed by color alone (e.g., error states use icon + color)
6. Test with contrast checker tool: all text meets 4.5:1 minimum
7. Visual regression testing: verify contrast fixes don't break design

**Prerequisites:** Epic 2 (Chat UI), Epic 5 (Canvas UI), Epic 6 (Celebration animations)

---

**Story 7.4: Implement Touch Target Sizing**

As a mobile user,
I want buttons large enough to tap accurately,
So that I can use the app comfortably on my phone.

**Acceptance Criteria:**
1. Audit all interactive elements (buttons, links, inputs)
2. Ensure minimum 44x44px touch targets (WCAG 2.1 AA requirement)
3. Add padding to small buttons (icon buttons, close buttons)
4. Increase tap area without changing visual size (use ::before pseudo-element)
5. Test on mobile device: all buttons tappable without errors
6. Spacing between adjacent touch targets: minimum 8px
7. Canvas toolbox buttons: 48x48px (extra large for drawing tools)

**Prerequisites:** Epic 2 (Chat UI), Epic 5 (Canvas UI)

---

**Story 7.5: Build Responsive Layout**

As a user on any device,
I want the app to adapt to my screen size,
So that I can learn comfortably whether on phone, tablet, or desktop.

**Acceptance Criteria:**
1. Mobile-first responsive design implemented
2. Breakpoints defined (mobile <768px, tablet 768-1024px, desktop >1024px)
3. Thread list sidebar: collapses on mobile, accessible via hamburger menu
4. Chat input: full width on mobile, fixed width on desktop
5. Canvas: full-screen mode on mobile, overlay on desktop
6. Message bubbles: adapt width to screen (max 90% width on mobile)
7. Test on real devices: iPhone 12 (375px), iPad (768px), desktop (1920px)
8. Responsive images: canvas thumbnails resize appropriately

**Prerequisites:** Epic 2 (Chat UI), Epic 5 (Canvas UI)

---

**Story 7.6: Implement ChatCanvas Responsive Behavior**

As a mobile user,
I want the drawing canvas optimized for touchscreens,
So that I can draw comfortably on my phone or tablet.

**Acceptance Criteria:**
1. Canvas z-index layering adjusted for mobile (full-screen overlay)
2. Canvas full-screen mode on mobile (hides chat, shows canvas only)
3. Swipe gestures for canvas toggle (swipe left to open, swipe right to close)
4. Toolbox repositioned for mobile (bottom toolbar instead of side toolbar)
5. Touch-optimized drawing (larger brush sizes, smoother touch tracking)
6. Pinch-to-zoom disabled on canvas (prevents accidental zoom)
7. Test on mobile: draw complex diagram, submit, verify usability

**Prerequisites:** Story 5.7 (ChatCanvas overlay), Story 7.5 (Responsive layout)

---

**Story 7.7: Add Focus Management**

As a keyboard user,
I want focus to be managed intelligently,
So that I always know where I am in the app.

**Acceptance Criteria:**
1. Focus returns to trigger element after modal close (dialog closes → focus returns to button that opened it)
2. Skip navigation links implemented (jump to main content, jump to thread list)
3. Focus moves to appropriate element after route changes (new thread → focus on chat input)
4. Dynamically added content receives focus (new message arrives → announce via live region, don't move focus)
5. Focus trap in modals (Tab/Shift+Tab cycles within modal)
6. Focus visible indicators (never use outline: none without replacement)
7. Test: keyboard-only navigation, verify focus management throughout app

**Prerequisites:** Story 7.1 (Keyboard navigation), Story 7.2 (Screen reader support)

---

## Story Guidelines Reference

**Story Format:**

```
**Story [EPIC.N]: [Story Title]**

As a [user type],
I want [goal/desire],
So that [benefit/value].

**Acceptance Criteria:**
1. [Specific testable criterion]
2. [Another specific criterion]
3. [etc.]

**Prerequisites:** [Dependencies on previous stories, if any]
```

**Story Requirements:**

- **Vertical slices** - Complete, testable functionality delivery
- **Sequential ordering** - Logical progression within epic
- **No forward dependencies** - Only depend on previous work
- **AI-agent sized** - Completable in 2-4 hour focused session
- **Value-focused** - Integrate technical enablers into value-delivering stories

---

**For implementation:** Use the `create-story` workflow to generate individual story implementation plans from this epic breakdown.
