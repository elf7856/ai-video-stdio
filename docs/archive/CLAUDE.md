# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Application
```bash
# Start development server with auto-reload
python -m uvicorn app.main:app --reload

# Alternative: Use the run script
python run.py
```

### Testing
```bash
# Run comprehensive test suite (recommended)
python run_tests.py

# Run specific test files
python tests/test_system_health.py
python tests/test_stable_llm.py
python tests/test_video_creator_platform.py

# Run pytest directly
python -m pytest tests/ -v
python -m pytest tests/test_video_creator_platform.py -v
```

### Health Checks
```bash
# Check API status and available services
python check_api_status.py

# Manual system component check
python tests/test_system_health.py
```

## Architecture Overview

This is an AI-powered video creation platform with a layered architecture:

### Core AI Director System
- **NewAIDirector** (`app/services/director/new_ai_director.py`) - Central orchestrator for video creation workflows
- **ProjectManager** - Handles project lifecycle and metadata
- **TimingAllocator** - Intelligent duration allocation for video segments
- **RealAPIOrchestrator** - Manages multiple video generation APIs (Runway, Google, etc.)

### Video Creation Pipeline
1. **Script Analysis** → Content segmentation using LLM
2. **Shot Planning** → Automated storyboard generation
3. **Timing Allocation** → Smart duration distribution
4. **Parallel Generation** → Concurrent video clip creation
5. **Audio Integration** → Optional TTS narration
6. **Final Assembly** → Video merging and post-processing

### Service Architecture
```
FastAPI App (app/main.py)
├── API Routes (app/api/)
│   ├── projects.py - Project management endpoints
│   ├── videos.py - Video processing APIs
│   └── gateway.py - Unified API gateway
├── Core Services (app/services/)
│   ├── director/ - AI Director system
│   ├── llm/ - Multi-provider LLM abstraction
│   ├── video/ - Video processing pipeline
│   ├── audio/ - TTS and audio processing
│   └── mcp/ - Model Context Protocol integration
└── Models (app/models/)
    ├── project.py - Project data models
    ├── shot.py - Video shot definitions
    └── timing.py - Timing allocation models
```

### LLM Integration
- **Unified Service** (`app/services/llm/unified_service.py`) - Multi-provider abstraction
- **Adapters** - Provider-specific implementations (OpenAI, Anthropic, Google)
- **Stable Service** - Fallback mechanisms and error handling

### Video Generation APIs
The platform integrates multiple video generation services:
- Runway ML, Google Video AI, OpenAI, Luma Dream Machine
- Auto-failover and provider selection based on content type
- Concurrent generation for faster processing

## Key Components

### Project Workflow
Projects follow this state machine:
```
CREATED → ANALYZING → PLANNING → GENERATING → COMPLETED/FAILED
```

### Video Processing Pipeline
The `VideoProcessor` handles:
- Format conversion and codec optimization
- Video merging with timing synchronization
- Audio track integration (narration + background)
- Quality optimization and compression

### Configuration Management
- Environment variables in `.env` (copy from `.env.example`)
- Central config in `app/core/config.py`
- API key validation and provider availability checking

## Testing Strategy

The test suite includes:
- **System Health** - API connectivity and service availability
- **Stable LLM** - LLM service reliability across providers  
- **Integration Tests** - End-to-end video creation workflows
- **Component Tests** - Individual service testing

Tests are designed to work with limited API keys and include graceful fallbacks.

## API Integration Notes

### Director System API
The AI Director exposes these key methods:
- `create_long_video_from_script()` - Full video creation pipeline
- `get_project_progress()` - Real-time progress monitoring
- `retry_failed_shots()` - Error recovery mechanisms

### Multi-Provider Support
The platform uses adapter pattern for:
- LLM services (OpenAI, Anthropic, Google)
- Video generation APIs (Runway, Luma, etc.)
- TTS services (Edge TTS, ElevenLabs)

Auto-failover ensures service availability even with partial API key configuration.

## File Structure Patterns

### Service Organization
- Each service has a dedicated directory under `app/services/`
- Services follow dependency injection pattern through `unified_service.py`
- Configuration and provider management centralized in `core/`

### Model Definitions
- Pydantic models in `app/models/` define data structures
- Models include validation, serialization, and status management
- Enum classes define states and constants (ProjectStatus, ShotType, etc.)

### API Routes
- FastAPI routers organized by feature in `app/api/`
- WebSocket support for real-time progress updates
- Consistent error handling and response formatting

The platform is designed for extensibility - new video generation providers, LLM services, or processing capabilities can be added through the existing adapter patterns.