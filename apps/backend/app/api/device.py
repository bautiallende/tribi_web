from fastapi import APIRouter, Query
from pydantic import BaseModel

from ..services.device_compatibility import CompatibilityVerdict, classify_user_agent

router = APIRouter(prefix="/api/device", tags=["device"])


class DeviceCompatibilityResponse(BaseModel):
    verdict: CompatibilityVerdict
    message: str
    user_agent: str | None = None


@router.get("/compatibility", response_model=DeviceCompatibilityResponse)
def get_device_compatibility(
    user_agent: str = Query(..., min_length=3, alias="user_agent")
):
    verdict, message = classify_user_agent(user_agent)
    return {
        "verdict": verdict,
        "message": message,
        "user_agent": user_agent,
    }
