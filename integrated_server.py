import os
import sys
import uvicorn
from fastapi import HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the REAL backend app
from app.main import app

# Configuration
FRONTEND_DIR = os.path.join("frontend", "dist")

def start_integrated_server():
    print(f"🚀 Starting Integrated Server (Backend + Frontend)")
    
    # 1. Check if frontend build exists
    if not os.path.exists(FRONTEND_DIR):
        print(f"❌ Frontend build not found at {FRONTEND_DIR}")
        print("   Please run 'cd frontend && npm run build' first.")
        return

    # 2. Remove the default root route from app.main (which returns JSON)
    #    so we can serve index.html instead
    new_routes = [r for r in app.router.routes if getattr(r, "path", "") != "/"]
    app.router.routes = new_routes
    
    # 3. Mount static assets
    #    /assets -> frontend/dist/assets
    assets_dir = os.path.join(FRONTEND_DIR, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
    
    # 4. Serve index.html at root
    @app.get("/")
    async def serve_root():
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

    # 5. Catch-all route for SPA (React Router)
    #    This allows routes like /generate, /editor to work when reloading the page.
    #    We exclude API and static file paths to ensure 404s are handled correctly for them.
    @app.get("/{full_path:path}")
    async def catch_all(full_path: str):
        # If it looks like an API or static file call that wasn't matched by previous routes, return 404
        if full_path.startswith("api/") or full_path.startswith("uploads/") or full_path.startswith("outputs/"):
             raise HTTPException(status_code=404, detail="Not Found")
        
        # Check if it's a real file in frontend/dist (e.g., favicon.ico, manifest.json)
        file_path = os.path.join(FRONTEND_DIR, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
             return FileResponse(file_path)
             
        # SPA Fallback: Serve index.html for any other route (React handles the routing)
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

    print("✅ Integrated Server Ready")
    print("   🌐 Access: http://localhost:8000")
    print("   📚 API Docs: http://localhost:8000/docs")

    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    start_integrated_server()
