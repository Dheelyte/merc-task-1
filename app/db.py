from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool
from tenacity import retry, stop_after_attempt, wait_fixed

from app.config import get_settings


class Base(DeclarativeBase):
    pass


def _make_engine(url: str):
    kwargs: dict = {}
    if url in ("sqlite://", "sqlite:///:memory:"):
        kwargs.update(connect_args={"check_same_thread": False}, poolclass=StaticPool)
    elif url.startswith("sqlite"):
        kwargs.update(connect_args={"check_same_thread": False})
    return create_engine(url, **kwargs)


engine = _make_engine(get_settings().database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@retry(stop=stop_after_attempt(3), wait=wait_fixed(0.2), reraise=True)
def init_db() -> None:
    # the sqlite file can be briefly locked when several workers boot at once
    Base.metadata.create_all(engine)


def get_session() -> Iterator[Session]:
    with SessionLocal() as session:
        yield session
