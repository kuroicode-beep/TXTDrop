import json
import re
import time
import threading
import urllib.request
import urllib.error

OLLAMA_URL = "http://localhost:11434"

_FALLBACK_MODELS = [
    "llama3", "llama3.2", "phi3", "mistral", "gemma3", "qwen2.5",
]

# ── Cached status ─────────────────────────────────────────────────────────────
_cache_lock     = threading.Lock()
_cached_running: bool | None = None
_cache_time:     float       = 0.0


def is_running() -> bool:
    try:
        urllib.request.urlopen(OLLAMA_URL, timeout=2)
        return True
    except Exception:
        return False


def is_running_cached(ttl: int = 10) -> bool:
    """
    Return cached Ollama status.  If the cache is older than *ttl* seconds,
    kick off a background refresh and return the stale value immediately.
    On first call (no cache yet) falls back to a synchronous check.
    """
    global _cached_running, _cache_time
    with _cache_lock:
        now   = time.monotonic()
        stale = _cached_running
        age   = now - _cache_time

    if stale is None:
        # first call — synchronous (only once)
        result = is_running()
        with _cache_lock:
            _cached_running = result
            _cache_time     = time.monotonic()
        return result

    if age >= ttl:
        # cache expired — refresh in background, return stale immediately
        threading.Thread(target=_refresh_cache, daemon=True).start()

    return stale


def _refresh_cache():
    global _cached_running, _cache_time
    result = is_running()
    with _cache_lock:
        _cached_running = result
        _cache_time     = time.monotonic()


def list_models() -> list[str]:
    try:
        with urllib.request.urlopen(f"{OLLAMA_URL}/api/tags", timeout=5) as r:
            data  = json.loads(r.read())
            names = [m["name"] for m in data.get("models", [])]
            return names if names else _FALLBACK_MODELS
    except Exception:
        return _FALLBACK_MODELS


def resolve_model(model: str) -> str:
    """
    Resolve configured model name against actually installed models.

    Priority:
      1. Exact match           ("llama3.2:3b"    → "llama3.2:3b")
      2. Add :latest suffix    ("llama3"         → "llama3:latest")
      3. Name prefix match     ("llama3"         → "llama3.2:3b")
      4. First available model (ultimate fallback)
    """
    available = list_models()
    if not available or available == _FALLBACK_MODELS:
        return model

    if model in available:
        return model

    with_latest = f"{model}:latest"
    if with_latest in available:
        return with_latest

    prefix_matches = [m for m in available if m.startswith(model)]
    if prefix_matches:
        return sorted(prefix_matches, key=len)[0]

    return available[0]


def generate_title(text: str, model: str) -> str | None:
    """
    Ask Ollama to produce a short, file-safe title for *text*.
    Returns a sanitized string, or None on any failure.
    Timeout: 20 s.
    """
    import config

    resolved = resolve_model(model)
    config.log_add("INFO", "ollama", f"제목 요청 → model={resolved}")

    prompt = (
        "다음 텍스트의 핵심을 3~5단어로 요약한 파일명용 짧은 제목을 만들어줘. "
        "한글, 영어, 숫자, 하이픈(-)만 사용하고 다른 특수문자는 쓰지 마. "
        "결과 제목만 한 줄로 출력해. 설명 없이 제목만:\n\n"
        + text[:800]
    )
    payload = json.dumps({
        "model":  resolved,
        "prompt": prompt,
        "stream": False,
    }).encode()

    try:
        req = urllib.request.Request(
            f"{OLLAMA_URL}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=20) as r:
            result = json.loads(r.read())
            if "error" in result:
                config.log_add("WARN", "ollama", f"API 오류: {result['error']}")
                return None
            raw   = result.get("response", "").strip()
            title = _sanitize(raw) or None
            if title:
                config.log_add("INFO", "ollama", f"제목 수신 ← \"{title}\"  (raw: \"{raw[:60]}\")")
            else:
                config.log_add("WARN", "ollama", f"제목 비어있음 (raw: \"{raw[:60]}\")")
            return title
    except urllib.error.URLError as e:
        config.log_add("ERROR", "ollama", f"URLError: {e.reason}")
        return None
    except TimeoutError:
        config.log_add("WARN", "ollama", "타임아웃 (20s)")
        return None
    except Exception as e:
        config.log_add("ERROR", "ollama", f"예외: {type(e).__name__}: {e}")
        return None


def _sanitize(title: str) -> str:
    title = title.strip().splitlines()[0]
    title = re.sub(r"[^\w\s가-힣a-zA-Z0-9\-]", "", title)
    title = re.sub(r"\s+", "-", title.strip())
    return title[:50]
