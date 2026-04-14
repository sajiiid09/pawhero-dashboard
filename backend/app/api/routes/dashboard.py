from fastapi import APIRouter

from app.api.dependencies import DbSession, OwnerId
from app.schemas.dashboard import DashboardSummaryDTO
from app.services.dashboard import build_dashboard_summary

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard/summary", response_model=DashboardSummaryDTO)
def get_dashboard_summary(session: DbSession, owner_id: OwnerId) -> DashboardSummaryDTO:
    return build_dashboard_summary(session, owner_id)
