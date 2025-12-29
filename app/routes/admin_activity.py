from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..core.db import get_db
from ..deps import get_current_user
from ..routes._render import templates, ctx
from .. import models
from datetime import datetime

router = APIRouter(prefix="/admin", tags=["admin"])


ACTION_LABELS = {
    "auth.login.success": "Login successful",
    "auth.login.failed": "Login failed",
    "auth.login.mfa_required": "Login – MFA required",
    "auth.mfa.success": "MFA verification successful",
    "auth.mfa.failed": "MFA verification failed",
    "auth.logout": "Logout",
    "auth.mfa.enabled": "MFA enabled",
    "auth.mfa.disabled": "MFA disabled",
    "admin.user.created": "User created",
    "admin.user.role_changed": "User role changed",
    "admin.user.status_changed": "User enabled / disabled",
    "admin.user.password_reset": "User password reset",
}


@router.get("/activity", include_in_schema=False)
def activity_log(
    request: Request,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    raw_rows = db.execute(
        text("""
            SELECT
                al.timestamp,
                al.actor_email,
                al.action,
                u.display_name AS target_name,
                u.email AS target_email,
                al.details
            FROM activity_log al
            LEFT JOIN users u
                ON al.entity_type = 'user'
               AND al.entity_id = u.id
            ORDER BY al.timestamp DESC
            LIMIT 500
        """)
    ).fetchall()

    rows = []
    for r in raw_rows:
    data = dict(r._mapping)

    ts = data.get("timestamp")
    if isinstance(ts, str):
        try:
            data["timestamp"] = datetime.fromisoformat(ts)
        except ValueError:
            data["timestamp"] = None

    data["action_label"] = ACTION_LABELS.get(data["action"], data["action"])
    rows.append(data)

    return templates.TemplateResponse(
        "admin/activity_log.html",
        ctx(request, rows=rows),
    )
