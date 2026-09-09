import time
from contextlib import asynccontextmanager

import anyio
import humanize
import psutil
from fastapi import Depends, FastAPI, HTTPException, Query, Response
from prometheus_client import Counter, make_asgi_app
from slugify import slugify
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette import status
from starlette.middleware.base import BaseHTTPMiddleware

from app.auth import create_token, require_user
from app.config import get_settings, load_file_config
from app.db import get_session, init_db
from app.logging_config import setup_logging
from app.models import Note
from app.rendering import render_html
from app.schemas import LoginIn, NoteCreate, NoteOut, NoteUpdate, TokenOut
from app.serializers import dump_notes

STARTED_AT = time.time()
REQUESTS = Counter("notes_requests_total", "HTTP requests", ["method", "path"])


class CountingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        REQUESTS.labels(request.method, request.url.path).inc()
        return await call_next(request)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(get_settings().log_level)
    init_db()
    yield


app = FastAPI(title=load_file_config()["app"]["title"], lifespan=lifespan)
app.add_middleware(CountingMiddleware)
app.mount("/metrics", make_asgi_app())


def to_out(note: Note) -> NoteOut:
    out = NoteOut.model_validate({**note.__dict__, "html": ""})
    out.html = render_html(note.id, note.updated_at, note.body)
    return out


def get_or_404(session: Session, note_id: int) -> Note:
    note = session.get(Note, note_id)
    if note is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "note not found")
    return note


@app.get("/health")
def health():
    uptime = time.time() - STARTED_AT
    return {
        "status": "ok",
        "uptime": humanize.naturaldelta(uptime),
        "rss_mb": round(psutil.Process().memory_info().rss / 1024 / 1024, 1),
    }


@app.post("/auth/token", response_model=None)
def login(creds: LoginIn) -> TokenOut:
    # demo auth: any non-empty password is accepted for the "admin" user
    if creds.username != "admin" or not creds.password:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "bad credentials")
    return {"access_token": create_token(creds.username), "token_type": "bearer"}


@app.post("/notes", response_model=NoteOut, status_code=status.HTTP_201_CREATED)
def create_note(payload: NoteCreate, session: Session = Depends(get_session)):
    note = Note(title=payload.title, slug=slugify(payload.title), body=payload.body, tag=payload.tag)
    session.add(note)
    session.commit()
    return to_out(note)


@app.get("/notes", response_model=list[NoteOut])
def list_notes(
    tag: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
):
    stmt = select(Note).order_by(Note.id).limit(limit).offset(offset)
    if tag:
        stmt = stmt.where(Note.tag == tag)
    return [to_out(n) for n in session.scalars(stmt)]


@app.get("/notes/export")
async def export_notes(session: Session = Depends(get_session)):
    rows = [
        {"id": n.id, "title": n.title, "tag": n.tag, "created_at": n.created_at.isoformat()}
        for n in session.scalars(select(Note).order_by(Note.id))
    ]
    body = await anyio.to_thread.run_sync(dump_notes, rows)
    return Response(body, media_type="application/json")


@app.get("/notes/{note_id}", response_model=NoteOut)
def get_note(note_id: int, session: Session = Depends(get_session)):
    return to_out(get_or_404(session, note_id))


@app.put("/notes/{note_id}", response_model=NoteOut)
def update_note(note_id: int, payload: NoteUpdate, session: Session = Depends(get_session)):
    note = get_or_404(session, note_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(note, field, value)
    if payload.title:
        note.slug = slugify(payload.title)
    session.commit()
    return to_out(note)


@app.delete("/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(note_id: int, session: Session = Depends(get_session), _user: str = Depends(require_user)):
    session.delete(get_or_404(session, note_id))
    session.commit()
