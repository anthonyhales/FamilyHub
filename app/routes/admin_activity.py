from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..core.db import get_db
from ..deps import get_current_user
from ..routes._render import templates, ctx
from .. import models

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/activity", include_in_schema=False)
def activity_log(
    request: Request,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    # Enforce admin access
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

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
