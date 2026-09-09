"""Pluggable export serializer.

The module that does the encoding is named in config.yaml so deployments can
swap it without touching code. Anything that exposes ``dumps(obj, option=...)``
or ``dumps(obj, indent=...)`` works.
"""
import importlib
from functools import lru_cache
from types import ModuleType

from app.config import load_file_config


@lru_cache
def get_serializer() -> ModuleType:
    name = load_file_config()["export"]["serializer"]
    return importlib.import_module(name)


def dump_notes(payload: list[dict]) -> bytes:
    cfg = load_file_config()["export"]
    mod = get_serializer()
    if hasattr(mod, "OPT_INDENT_2"):
        option = mod.OPT_INDENT_2 if cfg.get("indent") else 0
        return mod.dumps(payload, option=option)
    out = mod.dumps(payload, indent=2 if cfg.get("indent") else None)
    return out.encode() if isinstance(out, str) else out
