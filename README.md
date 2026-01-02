# FamilyHub (family organiser)

A small self-hosted app for your household with:

- Email + password login
- Optional TOTP MFA (authenticator apps)
- Calendar (basic events)
- Chores (simple recurrence + completion)
- Meal plan (weekly grid)

Tech:
- FastAPI + Jinja2 templates
- SQLAlchemy + SQLite (v1)
- SB Admin 2 layout

## Deploy with Portainer (Docker Compose)

1. In Portainer, create a new Stack and paste `docker-compose.yml`.
2. Change env vars:
   - `SECRET_KEY` (random long string)
   - `BOOTSTRAP_ADMIN_EMAIL`
   - `BOOTSTRAP_ADMIN_PASSWORD`

4. Deploy.

App will listen on:
- `http://<host>:8085`

### First login

Use the `BOOTSTRAP_ADMIN_EMAIL` and `BOOTSTRAP_ADMIN_PASSWORD`.

Then go to:
- Admin -> Users
and add the rest of the family.

## Adding SB Admin 2 assets

This repo includes a minimal placeholder CSS/JS so it runs immediately.

If you already have SB Admin 2 files:
- copy them into `app/static/sbadmin2/` and keep the paths:
  - `app/static/sbadmin2/css/sb-admin-2.min.css`
  - `app/static/sbadmin2/js/sb-admin-2.min.js`
  - `app/static/sbadmin2/vendor/...` (jquery, bootstrap, fontawesome etc.)

## Notes / roadmap

This is version 1. Next sensible steps:
- full calendar month view
- chore history page + points
- meal plan recipes + shopping list
- multi-household support + invite flow
- email sending (password reset) once you want it

There are elements of vibe coding within this project.
