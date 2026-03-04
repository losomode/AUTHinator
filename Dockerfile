# syntax=docker/dockerfile:1

# ── Dev stage (Django runserver, source volume-mounted) ──────────────────────
FROM python:3.12-slim AS dev

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/

RUN mkdir -p /app/backend/data

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

EXPOSE 8001

CMD ["python", "backend/manage.py", "runserver", "0.0.0.0:8001"]

# ── Prod stage (Gunicorn, static files collected) ────────────────────────────
FROM python:3.12-slim AS prod

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY backend/ ./backend/

RUN mkdir -p /app/backend/data /app/backend/staticfiles

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=config.settings

RUN cd backend && python manage.py collectstatic --noinput

EXPOSE 8001

CMD ["gunicorn", "--chdir", "backend", "--bind", "0.0.0.0:8001", "--workers", "2", "config.wsgi:application"]
