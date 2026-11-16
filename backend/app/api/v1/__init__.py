from fastapi import APIRouter

from app.api.v1 import analysis, auth, dashboard, jobs, resumes, users

api_router = APIRouter(prefix="/api/v1")
for module in (auth, users, resumes, jobs, analysis, dashboard):
    api_router.include_router(module.router)
