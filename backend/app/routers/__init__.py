from .auth import router as auth_router
from .users import router as users_router  
from .photos import router as photos_router
from .sessions import router as sessions_router

__all__ = ["auth_router", "users_router", "photos_router", "sessions_router"]