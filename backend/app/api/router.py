from fastapi import APIRouter

from app.api.routes import check_in, dashboard, emergency_chain, emergency_profile, health, pets

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(dashboard.router)
api_router.include_router(pets.router)
api_router.include_router(emergency_chain.router)
api_router.include_router(check_in.router)
api_router.include_router(emergency_profile.router)
