from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.db.session import get_db
from app.api.auth import get_current_user  # adjust import to your auth dependency
from app.services.ai_router import ai_router  # your router instance
from datetime import datetime

# Minimal user model for role checking; adjust to your schema
class CurrentUser(BaseModel):
    id: str
    email: str
    role: str

def admin_guard(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if getattr(user, "role", "user") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    return user

router = APIRouter(prefix="/api/admin/ai-router", tags=["Admin - AI Router"])

# DB model import (you created it earlier)
from sqlalchemy import Table, MetaData
# If you have an ORM model, import it instead. For pure SQL:
metadata = MetaData()
# Assuming ORM model exists; otherwise use text() queries.

# Pydantic schemas
class AIRouterConfigPayload(BaseModel):
    chat_fast: Optional[list[str]] = None
    chat_quality: Optional[list[str]] = None
    embeddings: Optional[list[str]] = None
    vision: Optional[list[str]] = None
    image_gen: Optional[list[str]] = None

    @field_validator("*", mode="before")
    @classmethod
    def allow_csv_or_array(cls, v):
        # Accept CSV string or array; normalize to array of "provider:model"
        if v is None:
            return v
        if isinstance(v, str):
            parts = [p.strip() for p in v.split(",") if p.strip()]
            return parts
        if isinstance(v, list):
            return v
        raise ValueError("Must be list of strings or CSV string")

class AIRouterConfigResponse(BaseModel):
    config: Dict[str, list[str]]
    updated_at: Optional[datetime] = None
    updated_by: Optional[str] = None

# Helpers
async def _get_active_config(db: AsyncSession) -> dict:
    result = await db.execute(
        select(
            # Using raw JSON fields (adjust to ORM model if present)
            # If using ORM, do: select(AIRouterConfig).where(AIRouterConfig.key == "active", AIRouterConfig.is_active == True)
            # and then row.config_json
            # For SQL text, you can use text("SELECT config_json, updated_at, updated_by FROM ai_router_config WHERE key='active' AND is_active = TRUE LIMIT 1")
        ).select_from(None)  # placeholder to force edit if you paste directly
    )
    raise NotImplementedError("Replace _get_active_config with your ORM or text() query")

async def _set_active_config(db: AsyncSession, config_json: dict, updated_by: str):
    from sqlalchemy import text
    q = text("""
        UPDATE ai_router_config
        SET config_json = :cfg::jsonb,
            updated_at = NOW(),
            updated_by = :by
        WHERE key = 'active' AND is_active = TRUE
    """)
    await db.execute(q, {"cfg": json_dumps(config_json), "by": updated_by})
    await db.commit()

# Simple JSON dumps without importing orjson (keep dependencies minimal)
import json
def json_dumps(d: Any) -> str:
    return json.dumps(d, separators=(",", ":"), ensure_ascii=False)

def _validate_entries(entries: list[str]) -> None:
    for item in entries:
        if ":" not in item:
            raise HTTPException(status_code=422, detail=f"Invalid provider:model '{item}'")

@router.get("/config", response_model=AIRouterConfigResponse, dependencies=[Depends(admin_guard)])
async def get_config(db: AsyncSession = Depends(get_db)):
    from sqlalchemy import text
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
    # Normalize CSV strings -> arrays if any legacy values exist
    normalized: Dict[str, list[str]] = {}
    for use_case, value in cfg.items():
        if isinstance(value, list):
            normalized[use_case] = value
        elif isinstance(value, str):
            normalized[use_case] = [p.strip() for p in value.split(",") if p.strip()]
        else:
            normalized[use_case] = []
    return AIRouterConfigResponse(config=normalized, updated_at=row[1], updated_by=row[2])

@router.put("/config", response_model=AIRouterConfigResponse, dependencies=[Depends(admin_guard)])
async def update_config(payload: AIRouterConfigPayload, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    # Load current config
    from sqlalchemy import text
    q = text("""
        SELECT config_json
        FROM ai_router_config
        WHERE key = 'active' AND is_active = TRUE
        LIMIT 1
    """)
    res = await db.execute(q)
    row = res.first()
    current = row[0] if row else {}

    # Merge updates (only provided fields)
    new_cfg: Dict[str, Any] = dict(current or {})
    for field in ["chat_fast", "chat_quality", "embeddings", "vision", "image_gen"]:
        value = getattr(payload, field)
        if value is not None:
            _validate_entries(value)
            new_cfg[field] = value  # store as array

    # Save
    q2 = text("""
        UPDATE ai_router_config
        SET config_json = :cfg::jsonb,
            updated_at = NOW(),
            updated_by = :by
        WHERE key = 'active' AND is_active = TRUE
    """)
    await db.execute(q2, {"cfg": json_dumps(new_cfg), "by": getattr(user, "email", "admin")})
    await db.commit()

    return AIRouterConfigResponse(config=new_cfg, updated_at=datetime.utcnow(), updated_by=getattr(user, "email", "admin"))

@router.get("/health", dependencies=[Depends(admin_guard)])
async def health_snapshot():
    # Expose router's in-memory health cache (non-sensitive)
    # Format: [{provider, model, ok, ts}]
    items = []
    for (name, model), (ok, ts) in ai_router.health.items():
        items.append({"provider": name, "model": model, "ok": bool(ok), "last_change_ts": ts})
    return {"health": items}