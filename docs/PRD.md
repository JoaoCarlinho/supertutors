# supertutors - Product Requirements Document

**Author:** caiojoao
**Date:** 2025-11-03
**Version:** 1.0

---

## Executive Summary

SuperTutors is an AI-powered math tutor that guides 9th-grade students through problem-solving using Socratic questioning methodology. Unlike generic AI chatbots that simply provide answers, SuperTutors embodies the patience and persistence of an exceptional human tutor—never giving up, never showing frustration, and guiding students to discover solutions themselves.

The system accepts math problems through multiple input methods (text, screenshots, handwritten images) and conducts multi-turn conversations that help students build genuine understanding. By integrating with deterministic computational engines, SuperTutors ensures mathematical accuracy while maintaining the gentle, encouraging teaching approach that builds student confidence.

**Target Users:** 9th-grade students (ages 14-15) working on algebra, geometry, and introductory math concepts, accessible through any web browser.

**Core Problem Solved:** Students need help with math homework but lack access to patient, knowledgeable tutors. Generic AI tools give direct answers (promoting cheating) or make computational errors. Human tutors are expensive and not always available.

**Our Solution:** A web-based AI tutor that combines:
- Socratic questioning that never gives direct answers
- Visual input processing (OCR/Vision AI) for handwritten problems
- Deterministic computation engines for mathematical accuracy
- Conversation persistence to track student learning journeys
- Unwavering patience encoded in every interaction

### What Makes This Special

**The feeling of having a patient tutor who never gives up on you.**

This isn't just about getting homework help—it's about experiencing what it feels like to have someone believe in your ability to understand, no matter how many times you struggle. Every interaction reinforces: "You can figure this out, and I'll be here as long as it takes."

**What differentiates SuperTutors:**

1. **Computational Integrity** - Integration with symbolic math engines (e.g., SymPy, Wolfram Alpha API) ensures correct answers, eliminating the "confident but wrong" problem of LLMs
2. **Visual Intelligence** - Students can snap a photo of their textbook, upload a whiteboard sketch, or draw directly—the system understands messy handwriting and mathematical notation
3. **Conversational Memory** - Unlike disposable chat sessions, SuperTutors maintains conversation threads so students can return to problems, review their learning journey, and build on prior sessions
4. **Pedagogical Discipline** - The system is architecturally constrained to NEVER give direct answers, maintaining Socratic integrity even when students beg for solutions

### Pedagogical Framework: Math Academy Way + Socratic Method

SuperTutors implements evidence-based cognitive learning strategies from the Math Academy Way methodology in conjunction with Socratic questioning to ensure pedagogical effectiveness. This dual approach combines the power of discovery-based learning with scientifically proven techniques that accelerate retention and understanding.

**Core Principles Integrated:**

1. **Active Learning + Socratic Questioning** - Students actively work through problems via guided questions rather than passively consuming solutions. The Socratic method ensures every interaction is a learning exercise, not a lecture.

2. **Deliberate Practice with Desirable Difficulty** - The system introduces productive struggle through carefully crafted questions that challenge students just beyond their current ability. This "desirable difficulty" slows immediate performance but dramatically improves long-term retention and transfer.

3. **Mastery Learning Through Conversation Tracking** - Before moving to more advanced topics, students must demonstrate proficiency in prerequisite concepts. The system tracks conversation history to identify knowledge gaps and ensure foundational understanding.

4. **Minimizing Cognitive Load** - Complex problems are broken into tiny steps through incremental questioning. Each Socratic exchange focuses on one small concept, preventing cognitive overload while building toward complete solutions.

5. **Spaced Repetition via Thread Continuity** - Conversation threads allow students to revisit problems over multiple sessions, spacing practice over time rather than cramming. This distributed practice strengthens long-term memory consolidation.

6. **Interleaving Through Mixed Problem Types** - The system encourages students to work on varied problem types rather than repetitive drills of the same concept, helping them learn to match problems with appropriate solution techniques.

7. **Retrieval Practice (Testing Effect)** - The Socratic method inherently implements retrieval practice—students must actively recall and apply knowledge to answer guiding questions, rather than passively reviewing reference material.

8. **Non-Interference Through Concept Spacing** - The system avoids teaching conceptually similar material consecutively, reducing interference effects that impede recall of related knowledge.

**Why This Combination Works:**

The Socratic method provides the *how* (guided discovery through questioning), while the Math Academy Way provides the *what* and *when* (which cognitive strategies to apply and when to apply them). Together, they create a tutoring experience that:

- Feels supportive and patient (Socratic encouragement)
- Produces genuine understanding (active discovery learning)
- Maximizes long-term retention (spaced repetition, interleaving, retrieval practice)
- Accelerates learning efficiency (deliberate practice, mastery learning, minimizing cognitive load)

**Implementation Note:** The system is designed to embrace "desirable difficulty"—students may feel challenged during problem-solving sessions (increased cognitive effort), but this productive struggle is precisely what drives deep learning. The tutor's unwavering patience and encouragement counterbalances this difficulty, preventing frustration while maintaining the cognitive activation necessary for true learning.

---

## Project Classification

**Technical Type:** Web Application (browser-based, responsive for mobile browsers)
**Domain:** EdTech (Educational Technology)
**Complexity:** Medium

**Technology Stack:**
- **Frontend:** React with Kea state management, KaTeX for math rendering
- **Backend:** Python Flask API server
- **LLM:** Locally deployable model on Mac (Llama 3.2 Vision, Ollama, or similar) for development; cloud-hosted inference for production
- **Computation:** SymPy for symbolic math, deterministic computation engine
- **Vision Processing:** Local vision-capable LLM for OCR and handwriting recognition
- **Database:** PostgreSQL for conversation persistence and user data
- **Caching/Real-time:** Redis for caching and WebSocket messaging
- **Deployment:** Railway (Frontend + Flask API + PostgreSQL + Redis); LLM inference endpoint TBD (potentially Modal, Replicate, or RunPod for GPU hosting)

**Deployment Architecture:**
- Railway hosts: React frontend (static build), Flask API, PostgreSQL, Redis
- LLM inference: Cloud GPU endpoint (Modal/Replicate/RunPod) for production, local Ollama for development
- Vision processing: Integrated with LLM endpoint or separate OCR service

---

## Success Criteria

**Success means students experience the patient tutor feeling and achieve genuine mathematical understanding.**

### Pedagogical Success Metrics

1. **Socratic Integrity** (Critical)
   - 100% of tutor responses use guiding questions, never direct answers
   - Students solve problems through discovery (measured by conversation patterns)
   - Average 3-5 question exchanges before student reaches solution independently

2. **Student Engagement**
   - Students complete problem-solving sessions (>80% completion rate for started problems)
   - Students return to the platform (>40% weekly active users from previous week)
   - Students continue old conversation threads (>30% of sessions are continuations)

3. **Learning Effectiveness**
   - Students demonstrate understanding by solving similar problems faster in subsequent sessions
   - Positive student feedback on "feeling supported" (>4.0/5.0 rating on patience/encouragement)

### Technical Success Metrics

4. **Computational Accuracy**
   - 100% mathematical correctness on validated problem sets (via SymPy integration)
   - Zero instances of confident but incorrect answers
   - Deterministic computation always matches expected results

5. **Visual Intelligence**
   - >85% accuracy on OCR/handwriting recognition for standard printed math problems
   - >70% accuracy on student handwritten problems (messy notebooks, whiteboard photos)
   - System successfully processes 5+ input formats (typed text, LaTeX, images, screenshots, drawings)

6. **System Reliability**
   - <2 second response time for text-based questions
   - <5 second processing time for image uploads
   - 99.5% uptime during school hours (3pm-9pm ET weekdays)
   - Conversation threads persist indefinitely, zero data loss

### Adoption Success Metrics

7. **User Love** (The Real Test)
   - 100 students who use SuperTutors for 5+ problems over 2+ weeks
   - Students choose SuperTutors over ChatGPT when both are available
   - Qualitative feedback includes words like: "patient," "helpful," "never gave up," "believed in me"

8. **Demo Quality**
   - 5-minute demo video clearly shows: problem input variety, Socratic dialogue, visual processing, thread continuation
   - Live demo completes end-to-end problem-solving session without errors

---

## Product Scope

### In Scope (MVP - Version 1.0)

**Core Tutoring Features:**
- Socratic questioning dialogue for 9th-grade math topics (algebra, geometry)
- Multi-turn conversation with context retention within single session
- Conversation thread persistence across sessions
- Mathematical computation via SymPy integration (symbolic math, equation solving)
- Visual problem input via image upload (screenshots, photos, whiteboard captures)
- Text-based problem input (typed, LaTeX notation)
- Drawing canvas for visual problem-solving (sketch graphs, diagrams)
- Real-time chat interface with typing indicators
- Math rendering using KaTeX (inline and display modes)

**User Experience:**
- Single-user development environment (no multi-user authentication)
- Web browser access (responsive for desktop, tablet, mobile browsers)
- Celebration system for positive reinforcement (3-in-a-row correct answers)
- Audio cheer feedback for correct answers
- Visual celebration animations (balloons, confetti, flash text)

**Technical Foundation:**
- PostgreSQL database for conversation persistence
- Redis caching for LLM response optimization
- Flask API backend with WebSocket support
- React frontend with Kea state management
- Local Ollama development (Llama 3.2 Vision for vision + text)
- Vision AI OCR for handwritten math problems

**Problem Domain:**
- 9th-grade mathematics: Algebra I, Geometry basics, introductory functions
- Standard math notation and symbolism
- English language instruction only (MVP)

### Out of Scope (Deferred to Post-MVP)

**Not in Version 1.0:**
- Multi-user authentication and authorization (OAuth, user accounts)
- User profiles, progress tracking dashboards, or analytics
- Rate limiting and abuse prevention
- Advanced math topics beyond 9th grade (calculus, statistics, advanced geometry)
- Multiple language support (non-English)
- Voice input/output (speech-to-text, text-to-speech)
- Parent/teacher dashboards or monitoring tools
- Gamification beyond basic celebration system (badges, leaderboards, streaks)
- Collaborative features (group problem solving, peer tutoring)
- Curriculum alignment with specific textbooks or standards
- Assessment or grading features
- Export/print functionality for conversation history
- Mobile native apps (iOS, Android) - web-only for MVP
- Advanced LLM features (custom fine-tuning, model selection)
- Production monitoring and observability infrastructure
- Content moderation or safety filters (single-user dev environment)

### Scope Boundaries

**What SuperTutors IS:**
- A patient Socratic tutor for 9th-grade math homework help
- A tool for building genuine understanding through guided discovery
- A computational engine for mathematical accuracy
- A web-based platform accessible through any browser

**What SuperTutors IS NOT:**
- A homework answer generator (architecturally prevents direct answers)
- A comprehensive learning management system (LMS)
- A replacement for structured curriculum or classroom instruction
- A standardized test preparation tool
- An AI that explains solutions (explains through questions, not exposition)

### MVP Success Definition

The MVP is successful when:
1. **Core Functionality Complete:** All in-scope features implemented and tested
2. **Pedagogical Integrity Maintained:** 100% Socratic questioning (zero direct answers)
3. **Mathematical Accuracy Achieved:** SymPy integration ensures computational correctness
4. **User Experience Validated:** 10+ students complete 5+ problems with positive feedback
5. **Technical Stability Proven:** System handles end-to-end sessions without crashes
6. **Demo-Ready:** 5-minute video demo and live demo session executable

**MVP Deployment:** Single-user development environment deployed to Railway, accessible via URL, tested with real 9th-grade students for feedback.

---

## Functional Requirements

### FR-1: Socratic Tutoring Conversation

**FR-1.1** The system SHALL conduct multi-turn conversations using Socratic questioning methodology
- Guide students through problem-solving with questions, never direct answers
- Ask follow-up questions based on student responses
- Maintain conversation context throughout session

**FR-1.2** The system SHALL implement Socratic Guard service
- Architecturally enforce "never give direct answers" constraint
- Rewrite any LLM responses that contain direct solutions
- Validate all tutor responses before sending to student

**FR-1.3** The system SHALL provide encouraging feedback
- Celebrate correct answers with positive reinforcement
- Maintain patient, supportive tone even when student struggles
- Never show frustration or give up on student

### FR-2: Mathematical Computation

**FR-2.1** The system SHALL integrate SymPy for symbolic math computation
- Solve algebraic equations deterministically
- Simplify expressions and evaluate formulas
- Provide 100% accurate mathematical results

**FR-2.2** The system SHALL validate student answers
- Compare student responses to computed solutions
- Detect partially correct answers and guide toward completion
- Handle multiple valid solution forms (e.g., 1/2 = 0.5)

**FR-2.3** The system SHALL render mathematical notation
- Display math equations using KaTeX rendering
- Support inline and display math modes
- Handle LaTeX notation input from students

### FR-3: Multimodal Input Processing

**FR-3.1** The system SHALL accept text-based problem input
- Plain text descriptions of math problems
- LaTeX notation for mathematical expressions
- Copy-paste support from external sources

**FR-3.2** The system SHALL process image uploads
- Accept image uploads (JPG, PNG, HEIC formats)
- Extract text and math notation via Vision AI OCR
- Display uploaded images in conversation thread

**FR-3.3** The system SHALL provide drawing canvas functionality
- Semi-transparent canvas overlay for visual problem-solving
- 8-color drawing toolbox with color selection
- Canvas-to-image conversion and persistence
- Z-index layering: messages → canvas → toolbox → input (never block input)

**FR-3.4** The system SHALL confirm OCR interpretation
- Show extracted problem text to student for verification
- Allow student to correct misinterpreted notation
- Proceed with tutoring only after student confirmation

### FR-4: Conversation Persistence

**FR-4.1** The system SHALL persist conversation threads
- Save all messages to PostgreSQL database
- Maintain conversation context and metadata
- Store canvas drawings as images within conversation

**FR-4.2** The system SHALL allow thread continuation
- Students can return to previous conversations
- Context is restored when resuming thread
- Conversation history visible and scrollable

**FR-4.3** The system SHALL retain conversation data indefinitely
- No automatic deletion of conversation threads
- Students can review past problem-solving sessions
- Support indefinite data retention (MVP has no deletion feature)

### FR-5: Celebration System

**FR-5.1** The system SHALL track correct answer streaks
- Detect 3 consecutive correct answers
- Maintain streak counter per conversation session
- Reset streak on incorrect answer

**FR-5.2** The system SHALL provide audio feedback
- Play audio cheer on every correct answer
- Provide 7+ audio cheer variations for variety
- Allow muting via accessibility controls

**FR-5.3** The system SHALL trigger visual celebrations
- Display celebration animations on 3-in-a-row streak
- Provide 5+ celebration variants (balloons, confetti, flash text)
- Animations are non-blocking (overlay, students can continue working)
- Support reduced motion preferences (WCAG accessibility)

### FR-6: Real-Time Chat Interface

**FR-6.1** The system SHALL provide WebSocket-based real-time messaging
- Instant message delivery (<2s for text responses)
- Typing indicators when tutor is composing response
- Smooth auto-scroll to latest message

**FR-6.2** The system SHALL display conversation thread UI
- Tutor messages: left-aligned, light blue background
- Student messages: right-aligned, white background
- Timestamps for message history
- Auto-scroll behavior with manual scroll override

**FR-6.3** The system SHALL provide input controls
- Text input area with multimodal buttons
- Image upload button with file picker
- Canvas toggle button
- Send button (or Enter key to submit)

### FR-7: User Experience

**FR-7.1** The system SHALL be responsive across devices
- Desktop layout (>1024px width)
- Tablet layout (768px-1024px)
- Mobile layout (<768px)
- Touch-friendly controls (44x44px minimum touch targets)

**FR-7.2** The system SHALL comply with WCAG 2.1 AA accessibility standards
- Keyboard navigation for all interactive elements
- Screen reader support with ARIA labels
- Color contrast ratios: 4.5:1 (normal text), 3:1 (large text)
- Focus indicators visible (2px blue outline)
- Reduced motion support via prefers-reduced-motion media query

**FR-7.3** The system SHALL load within acceptable performance thresholds
- <2 second response time for text-based questions
- <5 second processing time for image uploads
- Canvas drawing at 60 FPS
- Celebration animations at 60 FPS

### FR-8: System Integration

**FR-8.1** The system SHALL integrate with Ollama LLM
- Local development: Llama 3.2 Vision via Ollama
- Vision + text capabilities for OCR
- Streaming responses for real-time chat

**FR-8.2** The system SHALL cache LLM responses
- Redis caching for frequently asked similar problems
- Reduce LLM API costs and improve latency
- Cache invalidation strategy for correct behavior

**FR-8.3** The system SHALL handle errors gracefully
- Friendly error messages for network failures
- Retry logic for transient errors
- Fallback behaviors for OCR failures ("Can you try taking another photo?")
- Never crash or lose conversation state on error

---

## Non-Functional Requirements

### NFR-1: Performance

**NFR-1.1** Response Time (Latency)
- Text-based questions: <2 seconds from send to tutor response display
- Image upload processing: <5 seconds from upload to OCR completion
- Canvas rendering: 60 FPS drawing performance
- Celebration animations: 60 FPS animation performance
- Page load time: <3 seconds initial load on standard broadband connection

**NFR-1.2** Throughput
- Support single concurrent user (MVP - single-user dev environment)
- Handle 100+ messages per conversation session without degradation
- Process 50+ canvas drawing operations per session smoothly

**NFR-1.3** Resource Utilization
- Frontend bundle size: <500KB gzipped
- Memory usage: <200MB for frontend application
- Database query optimization: All queries <100ms on indexed fields

### NFR-2: Reliability & Availability

**NFR-2.1** Uptime
- 99.5% availability during school hours (3pm-9pm ET weekdays)
- Graceful degradation when backend services unavailable
- No data loss during service interruptions

**NFR-2.2** Error Handling
- All errors logged with contextual information
- User-facing error messages are friendly and actionable
- Automatic retry for transient network failures (3 attempts)
- Conversation state preserved through refresh/reload

**NFR-2.3** Data Integrity
- Zero conversation data loss (100% persistence)
- Database transactions for conversation operations
- Atomic saves for canvas drawings

### NFR-3: Scalability

**NFR-3.1** Current Capacity (MVP)
- Single user environment (no multi-user scaling required)
- Support 1 active conversation at a time
- Handle conversation threads with 500+ messages

**NFR-3.2** Future Scalability Considerations
- Architecture designed for horizontal scaling (stateless API)
- Database schema supports multiple users (future enhancement)
- Redis caching reduces LLM API load

### NFR-4: Security

**NFR-4.1** Authentication & Authorization (MVP Limitations)
- **NOT IMPLEMENTED IN MVP:** No user authentication
- **MVP CONSTRAINT:** Single-user development environment only
- **SECURITY WARNING:** Do not expose to public internet without auth

**NFR-4.2** Data Protection
- HTTPS only (TLS 1.2+) for all client-server communication
- Environment variables for sensitive configuration (API keys, database credentials)
- No sensitive data logged (conversation content not logged at INFO level)

**NFR-4.3** Input Validation
- Sanitize all user input before processing
- Validate image uploads (file type, size limits: 10MB max)
- Prevent injection attacks (SQL injection, XSS)

### NFR-5: Maintainability

**NFR-5.1** Code Quality
- TypeScript for frontend (strict mode enabled)
- Python type hints for backend
- ESLint + Prettier for frontend code formatting
- Black + Flake8 for backend code formatting
- Test coverage: >70% for critical paths (Socratic Guard, SymPy integration, OCR)

**NFR-5.2** Documentation
- Architecture decision records (ADRs) for major technical choices
- API documentation for all endpoints
- Component documentation for custom React components
- Database schema documentation

**NFR-5.3** Logging & Monitoring
- **MVP:** Basic console logging (development)
- **FUTURE:** Structured logging with correlation IDs
- **FUTURE:** Application monitoring (error rates, performance metrics)

### NFR-6: Usability

**NFR-6.1** Accessibility (WCAG 2.1 AA)
- Keyboard navigation for all interactive elements
- Screen reader support (ARIA labels, semantic HTML)
- Color contrast ratios: 4.5:1 for normal text, 3:1 for large text/UI
- Focus indicators: 2px blue outline, 3px offset
- Touch targets: 44x44px minimum (mobile/tablet)
- Reduced motion support via `prefers-reduced-motion` media query

**NFR-6.2** Responsiveness
- Mobile-first responsive design
- Breakpoints: <768px (mobile), 768px-1024px (tablet), >1024px (desktop)
- Touch-friendly controls on mobile/tablet
- No horizontal scrolling on any device size

**NFR-6.3** Browser Compatibility
- Chrome/Edge (latest 2 versions)
- Firefox (latest 2 versions)
- Safari (latest 2 versions)
- Mobile browsers: iOS Safari, Android Chrome

### NFR-7: Compatibility & Portability

**NFR-7.1** Platform Support
- Web application (no native mobile apps)
- Responsive web design for mobile browsers
- No platform-specific code (cross-platform web standards)

**NFR-7.2** Deployment Environment
- Railway platform deployment
- PostgreSQL 18+
- Redis 7.4+
- Node.js 20+ (frontend build)
- Python 3.11+ (backend runtime)

**NFR-7.3** Development Environment
- macOS, Linux, Windows development support
- Local Ollama for LLM development
- Docker optional but not required

### NFR-8: Compliance & Standards

**NFR-8.1** Web Standards
- HTML5 semantic markup
- CSS3 modern features (Grid, Flexbox, custom properties)
- ECMAScript 2022+ features (TypeScript compilation target)
- WebSocket (RFC 6455) for real-time messaging

**NFR-8.2** Accessibility Standards
- WCAG 2.1 Level AA compliance
- Section 508 compliance (US federal accessibility requirements)
- ARIA 1.2 specification for screen reader support

**NFR-8.3** Educational Context
- Age-appropriate design for 9th-grade students (14-15 years old)
- Content appropriate for educational environment
- No inappropriate content or distractions

### NFR-9: Operational Requirements

**NFR-9.1** Deployment
- Automated deployment via Railway CI/CD
- Zero-downtime deployments (future: blue-green or rolling)
- Environment-specific configuration (dev, staging, production)

**NFR-9.2** Backup & Recovery
- **DATABASE:** PostgreSQL automated backups (Railway managed service)
- **DISASTER RECOVERY:** Restore from backup <1 hour (Railway automation)
- **MVP:** No custom backup/restore procedures (rely on Railway)

**NFR-9.3** Cost Constraints (MVP)
- Railway hosting: Free tier or <$20/month
- LLM inference: Local Ollama (free for development)
- Total infrastructure cost: <$20/month for MVP

### NFR-10: Development & Testing

**NFR-10.1** Testing Strategy
- Unit tests for critical business logic (Socratic Guard, SymPy integration)
- Integration tests for API endpoints
- E2E tests for critical user journeys (future: Playwright/Cypress)
- Manual testing with real 9th-grade students (10+ testers)

**NFR-10.2** Continuous Integration
- Automated linting and formatting checks
- Automated test execution on commit
- Automated build verification

**NFR-10.3** Development Workflow
- Git version control with feature branches
- Pull request reviews before merging
- Semantic versioning for releases

---

## Implementation Planning

### Epic Breakdown Required

Requirements must be decomposed into epics and bite-sized stories (200k context limit).

**Next Step:** Run `workflow epics-stories` to create the implementation breakdown.

---

## References

---

## Next Steps

1. **Epic & Story Breakdown** - Run: `workflow epics-stories`
2. **UX Design** (if UI) - Run: `workflow ux-design`
3. **Architecture** - Run: `workflow create-architecture`

---

_This PRD captures the essence of supertutors_

_Created through collaborative discovery between caiojoao and AI facilitator._
