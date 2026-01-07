from fastapi import APIRouter, HTTPException, Depends
from typing import List, Any
from app.services.media.pexels import PexelsClient

router = APIRouter(prefix="/api/templates", tags=["Templates"])
pexels_client = PexelsClient()

@router.get("/featured")
async def get_featured_templates():
    """
    Get featured templates (from Pexels Curated or Fallback)
    """
    # Try fetching from Pexels
    photos = await pexels_client.get_curated_photos(per_page=10)
    
    if photos:
        # Map Pexels data to our Template format
        return {
            "source": "pexels",
            "templates": [
                {
                    "id": p["id"],
                    "title": p.get("alt", "Untitled"),
                    "thumbnail": p["src"]["landscape"],
                    "author": p["photographer"],
                    "url": p["url"]
                }
                for p in photos
            ]
        }
    
    # Fallback if no API key or error
    return {
        "source": "local",
        "templates": []
    }
