# Video Creator Platform — Repository Guidelines

## Project Overview

AI-driven end-to-end video creation platform: from creative concept, AI director, Google Veo video generation, to professional web-based NLE (non-linear editing), all in one place.

- **Backend**: FastAPI + Python 3.12, SQLite (dev) / PostgreSQL (prod), Alembic migrations
- **Frontend**: React + Vite + MUI + Zustand, TypeScript
- **Core AI**: Google Gemini (Veo video generation, Gemini image/text), LiteLLM (multi-provider LLM routing)
- **Video processing**: MoviePy, FFmpeg, OpenCV, WebAV (browser-side canvas engine)

---

## Project Structure & Module Organization

```
.
├── app/                        # FastAPI backend
│   ├── api/                    # Route handlers (one file per feature area)
│   ├── core/                   # Global config (settings via pydantic-settings)
│   ├── crud/                   # DB query helpers
│   ├── models/                 # SQLAlchemy ORM models
│   ├── prompts/                # LLM prompt templates (structured Python modules)
│   ├── schemas/                # Pydantic request/response schemas
│   ├── services/               # Core business logic
│   │   ├── analysis/           # Video/content analysis
│   │   ├── image/              # Image generation (multi-provider)
│   │   ├── llm/                # LLM service layer + adapters + smart router
│   │   │   ├── adapters/       # Per-provider LLM adapters
│   │   │   ├── analyzer.py     # Video analyzer
│   │   │   └── service.py      # LLM service facade
│   │   ├── video/              # Video download, processing, management
│   │   ├── video_generation/   # AI video generation orchestration
│   │   │   ├── agents/         # Generation strategy agents
│   │   │   ├── orchestrator.py # Top-level generation orchestrator
│   │   │   └── smart_router.py # Provider routing logic
│   │   ├── tts/                # TTS (text-to-speech) generation
│   │   ├── quality/            # Quality evaluation
│   │   └── web/                # Website crawler
│   ├── utils/                  # DB init, helpers
│   └── main.py                 # App entry point, service wiring
├── frontend/
│   └── src/
│       ├── api/                # Axios API client modules
│       ├── components/         # Reusable UI components
│       │   ├── generate/       # AI generation flow components
│       │   ├── project/        # Project management components
│       │   └── studio/         # NLE editor components (Timeline, Preview, etc.)
│       ├── engine/             # Browser-side canvas/WebAV render engine
│       ├── hooks/              # React hooks
│       ├── pages/              # Page-level components
│       ├── stores/             # Zustand state management
│       ├── types/              # TypeScript type definitions
│       └── utils/              # Utility functions
├── alembic/                    # DB migration scripts
├── outputs/                    # Generated artifacts (Docker volume mount)
│   └── projects/               # Per-project archived assets
├── uploads/                    # User uploaded files
├── scripts/                    # Utility scripts
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

---

## Build, Test, and Development Commands

### Backend

```bash
# Install dependencies
pip install -r requirements.txt

# Run DB migrations
alembic upgrade head

# Create a new migration
alembic revision --autogenerate -m "<description>"

# Start dev server (hot reload)
python -m uvicorn app.main:app --reload --port 8000

# API docs available at
# http://localhost:8000/docs   (Swagger UI)
# http://localhost:8000/redoc
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start dev server (http://localhost:3000)
npm run dev

# Production build
npm run build

# Preview production build
npm run preview

# Lint
npm run lint
```

### Docker (recommended for full-stack local testing)

```bash
# Copy env and fill in keys
cp env.example .env

# Build and start
docker-compose up --build -d

# Access: http://localhost:80
```

---

## Environment Variables

All keys go in `.env` (never committed). See `env.example` for the full list. Key variables:

| Variable | Purpose |
|---|---|
| `GOOGLE_API_KEY` | Google Gemini API (video + image generation). **Required.** |
| `RUNWAY_API_KEY` | Runway ML video generation (optional) |
| `LUMA_API_KEY` | Luma Dream Machine (optional) |
| `PIKA_API_KEY` | Pika Labs (optional) |
| `KLING_API_KEY` | Kling AI (optional) |
| `PEXELS_API_KEY` | Pexels stock footage (optional) |
| `ELEVENLABS_API_KEY` | ElevenLabs TTS (optional) |
| `STABILITY_API_KEY` | Stability AI image generation (optional) |
| `DATABASE_URL` | Defaults to `sqlite:///./video_creator.db` |

- Never commit real API keys, real video files, or real user data.
- Use obviously fake placeholders in tests, docs, and examples.

---

## Coding Style & Conventions

### Backend (Python)

- Python 3.12+; strict typing with Pydantic v2 and type annotations throughout.
- Use `pydantic-settings` (`app/core/config.py`) for all config; never hardcode env values.
- Keep API route handlers thin — delegate logic to `services/`.
- Keep service files focused; split when a file exceeds ~400 LOC.
- Log with the standard `logging` module (`logging.getLogger(__name__)`); no bare `print()` in production paths.
- Use `async def` for route handlers and I/O-bound service methods.
- Dependency injection via FastAPI `Depends()` and the `app/dependencies.py` module.
- DB access: always go through `crud/` helpers; do not write raw SQLAlchemy queries in route files.

### Frontend (TypeScript / React)

- Strict TypeScript; avoid `any`. Add types to `src/types/`.
- State management: Zustand stores in `src/stores/`. Keep store slices small and focused.
- Component style: functional components + hooks only; no class components.
- UI library: MUI v5 (`@mui/material`). Use the theme in `src/theme.ts`; avoid inline `sx` style overrides for shared patterns.
- Canvas/video engine: `src/engine/` wraps `@webav/av-canvas` and `@webav/av-cliper`. Keep raw WebAV calls inside `engine/`; components interact through engine abstractions.
- API calls: use modules in `src/api/`; never call `axios` directly from components or stores.
- Brief comments for non-obvious logic; keep files under ~500 LOC.

### Prompt Templates

- All LLM prompts live in `app/prompts/`. Each module exports structured prompt strings or builder functions.
- When modifying prompts, test against both `google_aistudio_client` and `openai_client` adapters if the prompt is shared.
- Use the `llm-prompt-optimizer` skill for prompt quality review.

---

## Architecture — Key Patterns

### LLM Provider Routing

`app/services/llm/` uses a smart router (`smart_router.py`) to dispatch to multiple providers (Google AI Studio, OpenAI, Runway, etc.) via LiteLLM. Add new providers by implementing an adapter in `llm/adapters/` and registering it in `client_factory.py`.

### Video Generation Pipeline

1. **Script** — `app/api/scripts.py` → AI director generates shot scripts
2. **Storyboard** — static images generated per shot (user confirms before video render)
3. **Video generation** — `app/services/video_generation/orchestrator.py` dispatches to provider clients; `smart_scheduler.py` handles parallel/sequential scheduling
4. **NLE editing** — frontend `engine/` plays back generated clips on a WebAV canvas timeline

### Service Initialization

Services are instantiated once at startup in `app/main.py` (`startup_event`) and injected into `app/dependencies.py`. Route handlers retrieve them via `Depends()`. Do not instantiate services inside route handlers.

---

## API Conventions

- All routes are prefixed by feature: `/api/videos`, `/api/projects`, `/api/scripts`, `/api/video-generation`, `/api/editor`, `/api/quality`, etc.
- Use Pydantic schemas from `app/schemas/` for request and response bodies.
- Return consistent error shapes via FastAPI `HTTPException`.
- Health check: `GET /health` — returns `{"status": "healthy"}`.
- API docs: `GET /docs` (Swagger), `GET /redoc`.

---

## Database & Migrations

- ORM: SQLAlchemy (models in `app/models/`)
- Migrations: Alembic (`alembic/`)
- **Always generate a migration** when changing model fields: `alembic revision --autogenerate -m "<msg>"`
- **Never** edit the DB schema by hand in production; always go through migration files.
- Dev default: SQLite (`video_creator.db`). Production: set `DATABASE_URL` to a PostgreSQL connection string.

---

## File Storage

- `uploads/` — user-uploaded source files
- `outputs/` — all AI-generated artifacts, organized as `outputs/projects/<project_id>/`
- Both directories are mounted as static file servers (`/uploads`, `/outputs`) by FastAPI.
- In Docker, `outputs/` is volume-mounted so data persists across container restarts.
- Maximum upload size: 100 MB (configurable via `MAX_FILE_SIZE` in settings).

---

## Security Notes

- CORS is currently set to `allow_origins=["*"]` for development. **Before production deployment**, restrict `allow_origins` to the actual frontend domain.
- Never commit `.env` or any file containing real API keys.
- Do not log API keys or user PII; scrub them from log output.
- Auth routes: `app/api/auth.py` and `app/api/users.py`. Protect sensitive endpoints with the auth dependency.

---

## Collaboration Notes

- In chat replies, use repo-root relative file paths (e.g., `app/services/llm/smart_router.py:42`), not absolute paths.
- When answering questions, verify in code before replying; do not guess.
- Do not change version strings without explicit request.
- Do not add large new dependencies without discussing trade-offs first.
- When touching the generation pipeline or LLM router, run a quick smoke test against the `/api/video-generation` endpoint before declaring done.
- Keep the many `*_IMPLEMENTATION.md` / `*_COMPLETE.md` status docs as-is unless asked to clean them up — they document historical decisions.
