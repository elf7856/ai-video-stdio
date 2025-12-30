# Simplified Prompt Management System

# Import core components
from .base import (
    PromptTemplate, PromptManager,
    register_prompt, render_prompt, prompt_manager
)

# Import legacy modules for backward compatibility
from . import video_analysis
from . import tts
from . import image_generation
from . import system
from . import llm_analysis

# Export main functions and classes
__all__ = [
    # Core classes
    'PromptTemplate', 'PromptManager',
    
    # Functions
    'register_prompt', 'render_prompt',
    
    # Global instances
    'prompt_manager'
] 