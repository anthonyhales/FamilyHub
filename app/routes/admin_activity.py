from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.db import get_db
from app.deps import admin_required
from app.routes._render import templates, ctx

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/activity", include_in_schema=False)
def activity_log(
    request: Request,
    db: Session = Depends(get_db),
    _=Depends(admin_required),
):
    rows = db.execute(
        text("""
            SELECT
                timestamp,
                actor_email,
                action,
                entity_type,
                entity_id,
                details
            FROM activity_log
            ORDER BY timestamp DESC
            LIMIT 500
        """)
    ).fetchall()

    return templates.TemplateResponse(
        "admin/activity_log.html",
        ctx(request, rows=rows),
    )
