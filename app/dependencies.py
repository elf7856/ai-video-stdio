# This file will hold shared, initialized instances of services
# to be used across the application, avoiding circular imports
# and centralizing dependency management.

from typing import Optional
from app.services.video.manager import VideoProcessingManager

# These will be initialized on app startup
video_manager: Optional[VideoProcessingManager] = None
