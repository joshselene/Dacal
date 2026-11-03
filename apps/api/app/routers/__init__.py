"""Router package for FastAPI API.
Exports the auth router so that it can be imported as
``from .routers import auth as auth_router``.
"""

from .auth import router as router
