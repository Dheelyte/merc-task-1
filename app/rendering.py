import markdown
from cachetools import TTLCache

# rendering markdown on every read is wasteful for big notes
_cache: TTLCache = TTLCache(maxsize=256, ttl=300)


def render_html(note_id: int, updated_at, body: str) -> str:
    key = (note_id, updated_at)
    if key not in _cache:
        _cache[key] = markdown.markdown(body, extensions=["fenced_code"])
    return _cache[key]
