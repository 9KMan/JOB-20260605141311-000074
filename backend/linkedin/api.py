"""
LinkedIn Profile Optimizer — FastAPI router.

POST /linkedin/optimize  → take pasted profile text + target role,
                            return OptimizationReport
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .models import OptimizationReport
from .optimizer import optimize_profile


router = APIRouter(prefix="/linkedin", tags=["linkedin"])


class OptimizeRequest(BaseModel):
    profile_text: str = Field(..., min_length=20, description="Pasted LinkedIn profile text")
    target_role: str = Field("", description="Target role (e.g. 'Senior Backend Engineer')")


@router.post("/optimize", response_model=OptimizationReport)
async def optimize(req: OptimizeRequest) -> OptimizationReport:
    """Parse, score, and rewrite a LinkedIn profile.

    The optimizer is deterministic — same input always produces the same report.
    No LLM dependency, no API cost per request.
    """
    try:
        report = optimize_profile(req.profile_text, req.target_role)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Optimization failed: {e}") from e
    return report
