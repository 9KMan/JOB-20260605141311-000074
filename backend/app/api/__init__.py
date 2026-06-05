"""API routes package."""
from fastapi import APIRouter

from app.api import auth, resumes, jobs, applications

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(resumes.router, prefix="/resumes", tags=["Resumes"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["Jobs"])
api_router.include_router(applications.router, prefix="/applications", tags=["Applications"])

__all__ = ["api_router"]
