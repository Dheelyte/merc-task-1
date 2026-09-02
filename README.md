# Notes API

A small FastAPI service for keeping markdown notes. Notes live in SQLite
(via SQLAlchemy) and are rendered to HTML on read.

## Endpoints

| Method | Path            | Notes                          |
|--------|-----------------|--------------------------------|
| GET    | /health         | uptime and memory use          |
| POST   | /auth/token     | demo login, returns a JWT      |
| POST   | /notes          | create a note                  |
| GET    | /notes          | list, `?tag=`, `limit`, `offset` |
| GET    | /notes/export   | JSON dump of all notes         |
| GET    | /notes/{id}     | fetch one note                 |
| PUT    | /notes/{id}     | partial update                 |
| DELETE | /notes/{id}     | needs a bearer token           |

Prometheus metrics are exposed at `/metrics`.

## Running locally

    python -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt
    uvicorn app.main:app --reload

## Tests

    pytest

## Docker

    docker build -t notes-api .
    docker run -p 8000:8000 notes-api

## Configuration

Environment variables prefixed with `NOTES_` (see `app/config.py`) and a
`.env` file are supported. Pluggable pieces such as the export serializer are
selected in `config.yaml`. `scripts/serve_prod.sh` is the launcher we use on
the VM.
