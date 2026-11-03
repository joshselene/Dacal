
import uuid
from fastapi import FastAPI, Request
from app.routers.auth import router as auth_router
from app.routers.projects import router as projects_router
from app.db import engine
from app.models.base import Base
from app import models  # noqa: F401
from fastapi.middleware.cors import CORSMiddleware
from app.routers.experiences import router as experiences_router
from app.routers.experience_versions import router as experience_versions_router
from app.routers.studio_srs import router as studio_srs_router
from app.modules.classes.interfaces.http.routes import router as classes_router

# Create all tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Chernyx AI Studio API",
    version="0.1.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_trace_id(request: Request, call_next):
    trace_id = request.headers.get("X-Trace-ID") or str(uuid.uuid4())
    request.state.trace_id = trace_id
    response = await call_next(request)
    response.headers["X-Trace-ID"] = trace_id
    return response


app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(projects_router, prefix="/api/v1/projects", tags=["Projects"])
app.include_router(
    experiences_router,
    prefix="/api/v1/experiences",
    tags=["Experiences"],
)
app.include_router(
    experience_versions_router,
    prefix="/api/v1/experiences",
    tags=["Experience Versions"],
)
app.include_router(
    experience_versions_router,
    prefix="/api/v1/experience-versions",
    tags=["Experience Versions"],
)
app.include_router(classes_router, prefix="/api/v1/classes", tags=["Classes"])
app.include_router(studio_srs_router, prefix="/api/v1")


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "api",
    }
