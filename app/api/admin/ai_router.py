# app/api/admin/ai_router.py
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import datetime
import json

from app.db.session import get_db
from app.api.auth import get_current_active_user  # FIXED: use existing dependency
from app.services.ai_router import ai_router

router = APIRouter(prefix="/api/admin/ai-router", tags=["Admin - AI Router"])

def admin_guard(user=Depends(get_current_active_user)):
    # Your dependency likely returns a user model with .role/.email
    # If it returns a dict, these lines still handle it.
    role = getattr(user, "role", None) or (user.get("role") if isinstance(user, dict) else None)
    if (role or "").lower() != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    return user

class AIRouterConfigPayload(BaseModel):
    chat_fast: Optional[list[str]] = None
    chat_quality: Optional[list[str]] = None
    embeddings: Optional[list[str]] = None
    vision: Optional[list[str]] = None
    image_gen: Optional[list[str]] = None

    @field_validator("*", mode="before")
    @classmethod
    def allow_csv_or_array(cls, v):
        # Accept CSV string or array; normalize to array
        if v is None:
            return v
        if isinstance(v, str):
            return [p.strip() for p in v.split(",") if p.strip()]
        if isinstance(v, list):
            return v
        raise ValueError("Must be list of strings or CSV string")

class AIRouterConfigResponse(BaseModel):
    config: Dict[str, list[str]]
    updated_at: Optional[datetime] = None
    updated_by: Optional[str] = None

def json_dumps(d: Any) -> str:
    return json.dumps(d, separators=(",", ":"), ensure_ascii=False)

def _validate_entries(entries: list[str]) -> None:
    for item in entries:
        if ":" not in item:
            raise HTTPException(status_code=422, detail=f"Invalid provider:model '{item}'")

@router.get("/config", response_model=AIRouterConfigResponse, dependencies=[Depends(admin_guard)])
async def get_config(db: AsyncSession = Depends(get_db)):
    q = text("""
        SELECT config_json, updated_at, updated_by
        FROM ai_router_config
        WHERE key = 'active' AND is_active = TRUE
        LIMIT 1
    """)
    res = await db.execute(q)
    row = res.first()
    if not row:
        raise HTTPException(status_code=404, detail="Active config not found")
    cfg = row[0] or {}
    normalized: Dict[str, list[str]] = {}
    # Normalize values: array preferred; support legacy CSV strings
    for use_case, value in cfg.items():
        if isinstance(value, list):
            normalized[use_case] = value
        elif isinstance(value, str):
            normalized[use_case] = [p.strip() for p in value.split(",") if p.strip()]
        else:
            normalized[use_case] = []
    return AIRouterConfigResponse(config=normalized, updated_at=row[1], updated_by=row[2])

@router.put("/config", response_model=AIRouterConfigResponse, dependencies=[Depends(admin_guard)])
async def update_config(
    payload: AIRouterConfigPayload,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_active_user),
):
    # Load current
    q = text("""
        SELECT config_json
        FROM ai_router_config
        WHERE key = 'active' AND is_active = TRUE
        LIMIT 1
    """)
    res = await db.execute(q)
    row = res.first()
    current = row[0] if row else {}

    new_cfg: Dict[str, Any] = dict(current or {})
    for field in ["chat_fast", "chat_quality", "embeddings", "vision", "image_gen"]:
        value = getattr(payload, field)
        if value is not None:
            _validate_entries(value)
            new_cfg[field] = value  # store as array

    q2 = text("""
        UPDATE ai_router_config
        SET config_json = :cfg::jsonb,
            updated_at = NOW(),
            updated_by = :by
        WHERE key = 'active' AND is_active = TRUE
    """)
    updated_by = getattr(user, "email", None) or (user.get("email") if isinstance(user, dict) else "admin")
    await db.execute(q2, {"cfg": json_dumps(new_cfg), "by": updated_by})
    await db.commit()

    return AIRouterConfigResponse(config=new_cfg, updated_at=datetime.utcnow(), updated_by=updated_by)

@router.get("/health", dependencies=[Depends(admin_guard)])
async def health_snapshot():
    items = []
    for (name, model), (ok, ts) in ai_router.health.items():
        items.append({"provider": name, "model": model, "ok": bool(ok), "last_change_ts": ts})
    return {"health": items}