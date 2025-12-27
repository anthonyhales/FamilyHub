from __future__ import annotations

from fastapi import Request
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="app/templates")


def ctx(request: Request, **kwargs):
    base = {
        "request": request,
        "user": getattr(request.state, "user", None),
        "csrf": kwargs.pop("csrf", None),
        "flash": request.session.pop("flash", None),
        "settings": {
            "app_name": "FamilyHub",
        },
    }
    base.update(kwargs)
    return base

from datetime import timedelta
templates.env.globals['timedelta'] = timedelta
