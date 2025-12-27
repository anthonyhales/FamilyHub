import json
from datetime import datetime
from sqlalchemy import text


def log_activity(
    db,
    request=None,
    action: str = "",
    entity_type: str | None = None,
    entity_id: int | None = None,
    details: dict | None = None,
):
    try:
        actor_user_id = None
        actor_email = None

        if request and hasattr(request.state, "user") and request.state.user:
            actor_user_id = request.state.user.id
            actor_email = request.state.user.email

        db.execute(
            text("""
                INSERT INTO activity_log (
                    timestamp,
                    actor_user_id,
                    actor_email,
                    action,
                    entity_type,
                    entity_id,
                    details
                )
                VALUES (:ts, :uid, :email, :action, :etype, :eid, :details)
            """),
            {
                "ts": datetime.utcnow(),
                "uid": actor_user_id,
                "email": actor_email,
                "action": action,
                "etype": entity_type,
                "eid": entity_id,
                "details": json.dumps(details) if details else None,
            },
        )
        db.commit()
    except Exception as e:
        print(f"[ACTIVITY_LOG] Failed: {e}")
