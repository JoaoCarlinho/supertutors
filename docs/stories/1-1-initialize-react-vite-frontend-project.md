# Story 1.1: Initialize React + Vite Frontend Project

Status: ready-for-dev

## Story

As a developer,
I want a properly configured React + Vite project with TypeScript,
So that I can build modern, type-safe frontend features efficiently.

## Acceptance Criteria

1. Vite project created with React 18.3.1 and TypeScript 5.7.x
2. Tailwind CSS v4.0 configured with custom design tokens
3. shadcn/ui component library installed and configured
4. Kea state management library installed (version 3.1.6)
5. ESLint and Prettier configured for code quality
6. `npm run dev` starts development server successfully on `http://localhost:5173`
7. Hot Module Replacement (HMR) works for instant feedback

## Tasks / Subtasks

- [ ] **Task 1: Initialize Vite + React + TypeScript project** (AC: #1)
  - [ ] Run `npm create vite@latest frontend -- --template react-ts`
  - [ ] Navigate to frontend directory and run `npm install`
  - [ ] Verify `package.json` contains React 18.3.1+ and TypeScript 5.7.x+
  - [ ] Create base project structure: `src/components/ui/`, `src/components/custom/`, `src/logic/`, `src/lib/`, `src/types/`, `src/assets/`

- [ ] **Task 2: Configure Tailwind CSS v4.0** (AC: #2)
  - [ ] Install Tailwind CSS: `npm install -D tailwindcss@4 postcss autoprefixer`
  - [ ] Initialize Tailwind: `npx tailwindcss init`
  - [ ] Configure `tailwind.config.js` with content paths
  - [ ] Update `src/index.css` with Tailwind directives (`@tailwind base; @tailwind components; @tailwind utilities;`)
  - [ ] Verify Tailwind classes render correctly in `App.tsx`

- [ ] **Task 3: Install and configure shadcn/ui** (AC: #3)
  - [ ] Run `npx shadcn-ui@latest init` (select Tailwind CSS, TypeScript)
  - [ ] Install initial components: `npx shadcn-ui@latest add button input dialog toast card label`
  - [ ] Verify components are importable from `@/components/ui/`
  - [ ] Test render a Button component in `App.tsx`

- [ ] **Task 4: Install Kea state management** (AC: #4)
  - [ ] Install Kea: `npm install kea@3.1.6 kea-typegen@3.1.6`
  - [ ] Create `src/logic/appLogic.ts` as parent logic store
  - [ ] Configure `kea-typegen` in `package.json` scripts
  - [ ] Verify Kea imports work without errors

- [ ] **Task 5: Configure ESLint and Prettier** (AC: #5)
  - [ ] Verify ESLint is configured (Vite template includes it)
  - [ ] Install Prettier: `npm install -D prettier eslint-config-prettier`
  - [ ] Create `.prettierrc` with project standards (semi: true, singleQuote: true, tabWidth: 2)
  - [ ] Add Prettier script to `package.json`: `"format": "prettier --write \"src/**/*.{ts,tsx}\""`
  - [ ] Run `npm run format` to verify

- [ ] **Task 6: Verify development server and HMR** (AC: #6, #7)
  - [ ] Run `npm run dev`
  - [ ] Verify server starts on `http://localhost:5173`
  - [ ] Make a change to `App.tsx` (e.g., change text)
  - [ ] Verify HMR updates browser instantly without full reload
  - [ ] Test that no console errors appear

## Dev Notes

### Architecture Context

This story establishes the foundational frontend infrastructure for the SuperTutors platform, implementing the React TypeScript stack as specified in the architecture document.

**Key Architecture Decisions:**
- **ADR-001 (Vite):** Fast HMR is critical for rapid iteration on canvas drawing UX and celebration animations in future epics
- **ADR-002 (Kea):** State management library for composable logic stores (25+ stores anticipated: conversationLogic, canvasLogic, celebrationLogic, settingsLogic)
- **ADR-006 (Tailwind v4.0):** New high-performance engine provides 5x faster builds, 100x faster incremental builds

**Technology Stack Rationale:**
- **React 18.3.1:** Concurrent rendering for smooth animations, largest ecosystem
- **TypeScript 5.7.x:** Type safety essential for complex state management across 25+ Kea logic stores
- **Vite 6.x:** Instant HMR (<100ms updates), critical for canvas/celebration development workflow
- **shadcn/ui + Radix UI:** WCAG 2.1 AA accessible components (required by Epic 7), copy-paste pattern for customization
- **Tailwind CSS v4.0:** Utility-first CSS, automatic content detection, CSS-first configuration

### Project Structure Notes

**Alignment with Unified Project Structure:**

This story creates the `frontend/` directory structure as specified in [docs/architecture.md#Project-Structure]:

```
frontend/
├── src/
│   ├── components/
│   │   ├── ui/                    # shadcn/ui components (Button, Input, Dialog, etc.)
│   │   └── custom/                # Reserved for future stories (ChatCanvas, CelebrationOverlay, etc.)
│   ├── logic/                     # Kea state management stores (appLogic created this story)
│   ├── lib/                       # Utilities (api.ts, socket.ts, utils.ts - future stories)
│   ├── types/                     # TypeScript type definitions (index.ts)
│   ├── assets/                    # Static assets (audio/, images/ - future epics)
│   ├── App.tsx                    # Root component
│   ├── main.tsx                   # Entry point
│   └── index.css                  # Tailwind CSS imports
├── public/                        # Static assets
├── tailwind.config.js             # Tailwind CSS v4.0 config
├── tsconfig.json                  # TypeScript configuration
├── vite.config.ts                 # Vite build configuration
└── package.json
```

**Naming Conventions (enforced):**
- React Components: PascalCase (e.g., `App.tsx`)
- Kea Logic Stores: camelCase + "Logic" suffix (e.g., `appLogic.ts`)
- TypeScript interfaces: Prefix with `I` (e.g., `IMessage`)
- CSS: Tailwind utilities only, no custom CSS classes unless absolutely necessary

**No Conflicts:** This is the first story, establishing baseline structure.

### Testing Standards

**Unit Testing Framework:** Vitest (Vite-native testing)
- Not required for this story (no complex logic yet)
- Future stories will add tests for Kea logic stores and utility functions
- Target coverage: >70% for critical utilities

**Manual Testing Checklist:**
- [ ] `npm run dev` starts successfully on `http://localhost:5173`
- [ ] HMR works (change `App.tsx` text, verify instant update)
- [ ] No console errors in browser
- [ ] Tailwind classes render correctly (test with `className="bg-blue-500 text-white p-4"`)
- [ ] shadcn/ui Button component renders and is clickable
- [ ] ESLint reports no errors: `npm run lint`
- [ ] Prettier formats code: `npm run format`

### References

**Technical Specifications:**
- [Source: docs/tech-spec-epic-1.md#Epic-1-Story-1.1] - Detailed implementation requirements
- [Source: docs/tech-spec-epic-1.md#Frontend-Dependencies] - Exact dependency versions
- [Source: docs/tech-spec-epic-1.md#Workflows-Story-1.1] - Step-by-step execution sequence

**Architecture Documentation:**
- [Source: docs/architecture.md#Project-Structure] - Directory layout specification
- [Source: docs/architecture.md#Frontend-Stack] - Technology stack details
- [Source: docs/architecture.md#ADR-001] - Vite decision rationale
- [Source: docs/architecture.md#ADR-002] - Kea state management decision
- [Source: docs/architecture.md#ADR-006] - Tailwind v4.0 decision
- [Source: docs/architecture.md#Naming-Conventions] - Code style enforcement

**Epic Context:**
- [Source: docs/epics.md#Epic-1-Story-1.1] - User story and acceptance criteria
- [Source: docs/PRD.md#Technology-Stack] - Product requirements context

### Dependencies and Prerequisites

**Prerequisites:** None (first story in Epic 1)

**Dependencies for Future Stories:**
- Story 1.2 (Backend) can run in parallel
- Story 1.7 (Error Handling) depends on this story for frontend error boundary
- Epic 2 (Chat UI) depends on this foundation
- Epic 5 (Canvas) depends on this foundation

### Non-Functional Requirements

**Performance Targets (from tech spec):**
- Vite dev server startup: <1s
- HMR update time: <100ms
- Tailwind CSS v4.0 builds: 5x faster than v3.x
- Frontend bundle size target: <500KB gzipped

**Build Performance:**
- Initial build time: <10s (Vite optimization)
- Incremental builds: <1s (Tailwind v4.0 engine)

### Environment Variables

**Development:**
- `VITE_API_URL`: `http://localhost:5000` (will be set in future stories when backend is available)
- `VITE_WS_URL`: `ws://localhost:5000` (WebSocket endpoint, future stories)

**Production (Railway):**
- `VITE_API_URL`: Railway backend URL (configured in Story 1.6)
- `VITE_WS_URL`: Railway WebSocket URL (configured in Story 1.6)

### Change Log

- **2025-11-04:** Story created by SM agent (caiojoao) via create-story workflow
  - Initial draft based on tech-spec-epic-1.md and epics.md
  - Status: drafted (ready for review and dev)

## Dev Agent Record

### Context Reference

- [Story Context XML](docs/stories/1-1-initialize-react-vite-frontend-project.context.xml)

### Agent Model Used

<!-- Dev agent will fill this in during implementation -->

### Debug Log References

<!-- Dev agent will add debug log paths here -->

### Completion Notes List

<!-- Dev agent will document:
- New files created
- New patterns/services established
- Architectural decisions made
- Technical debt deferred
- Warnings for next story
-->

### File List

<!-- Dev agent will list:
- NEW: files created
- MODIFIED: files changed
- DELETED: files removed
-->
