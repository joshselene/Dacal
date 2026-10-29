
from fastapi import FastAPI
from app.routers.auth import router as auth_router
from app.routers.projects import router as projects_router
from app.db import engine
from app.models.base import Base
from app import models
from fastapi.middleware.cors import CORSMiddleware
from app.routers.experiences import router as experiences_router
from app.routers.experience_versions import router as experience_versions_router
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
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(projects_router, prefix="/api/v1/projects", tags=["Projects"])
app.include_router(
    experiences_router,
    prefix="/api/v1/experiences",
    tags=["Experiences"],
)
app.include_router(
    experience_versions_router,
    prefix="/api/v1/experience-versions",
    tags=["Experience Versions"],
)
app.include_router(classes_router, prefix="/api/v1/classes", tags=["Classes"])
@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "api",
    }
