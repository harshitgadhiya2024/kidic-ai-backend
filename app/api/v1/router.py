"""API v1 Router"""

from fastapi import APIRouter
from app.api.v1.endpoints import auth, files, templates, generate_kid_photoshoot, contact_us, credits

# Create main API router
api_router = APIRouter(prefix="/api/v1")

# Include endpoint routers
api_router.include_router(auth.router)
api_router.include_router(files.router)
api_router.include_router(templates.router)
api_router.include_router(generate_kid_photoshoot.router)
api_router.include_router(contact_us.router)
api_router.include_router(credits.router)
