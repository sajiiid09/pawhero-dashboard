from fastapi import APIRouter

from app.api.routes import (
    auth,
    check_in,
    dashboard,
    documents,
    emergency_chain,
    emergency_profile,
    health,
    notifications,
    pets,
    public,
    push,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(public.router)
api_router.include_router(dashboard.router)
api_router.include_router(pets.router)
api_router.include_router(documents.router, prefix="/pets")
api_router.include_router(emergency_chain.router)
api_router.include_router(check_in.router)
api_router.include_router(emergency_profile.router)
api_router.include_router(notifications.router)
api_router.include_router(push.router)
