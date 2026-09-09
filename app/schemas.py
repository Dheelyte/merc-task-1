from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from typing_extensions import TypedDict


class NoteCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    body: str = ""
    tag: str | None = Field(default=None, max_length=50)


class NoteUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    body: str | None = None
    tag: str | None = Field(default=None, max_length=50)


class NoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    slug: str
    body: str
    html: str
    tag: str | None
    created_at: datetime
    updated_at: datetime


class TokenOut(TypedDict):
    access_token: str
    token_type: str


class LoginIn(BaseModel):
    username: str
    password: str
