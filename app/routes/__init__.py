from app.routes.public import router as public_router
from app.routes.admin import router as admin_router
from app.routes.api import router as api_router

__all__ = ["public_router", "admin_router", "api_router"]
