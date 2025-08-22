# Complex logic routers for FastAPI
from .sessions import router as sessions_router
from .websocket import router as websocket_router

__all__ = ["sessions_router", "websocket_router"]

# Note: auth, users, photos routers removed - using Supabase directly from frontend
# Only complex logic routers (sessions for AI/CIST evaluation) remain