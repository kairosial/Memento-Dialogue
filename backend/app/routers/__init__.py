# Only sessions router is needed for complex logic processing
from .sessions import router as sessions_router

__all__ = ["sessions_router"]

# Note: auth, users, photos routers removed - using Supabase directly from frontend
# Only complex logic routers (sessions for AI/CIST evaluation) remain