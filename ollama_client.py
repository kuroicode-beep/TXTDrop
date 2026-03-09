import json
import re
import urllib.request
import urllib.error

OLLAMA_URL = "http://localhost:11434"

_FALLBACK_MODELS = [
    "llama3", "llama3.2", "phi3", "mistral", "gemma3", "qwen2.5",
]


def is_running() -> bool:
    try:
        urllib.request.urlopen(OLLAMA_URL, timeout=2)
        return True
    except Exception:
        return False


def list_models() -> list[str]:
    try:
        with urllib.request.urlopen(f"{OLLAMA_URL}/api/tags", timeout=5) as r:
            data = json.loads(r.read())
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

    # 1. Exact
    if model in available:
        return model

    # 2. :latest
    with_latest = f"{model}:latest"
    if with_latest in available:
        return with_latest

    # 3. Prefix — pick shortest match (most specific)
    prefix_matches = [m for m in available if m.startswith(model)]
    if prefix_matches:
        return sorted(prefix_matches, key=len)[0]

    # 4. First available
    return available[0]


def generate_title(text: str, model: str) -> str | None:
    """
    Ask Ollama to produce a short, file-safe title for *text*.
    Returns a sanitized string, or None on any failure.
    """
    resolved = resolve_model(model)

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
        with urllib.request.urlopen(req, timeout=30) as r:
            result = json.loads(r.read())

            # Ollama returns {"error": "..."} on model-not-found etc.
            if "error" in result:
                return None

            raw = result.get("response", "").strip()
            return _sanitize(raw) or None
    except Exception:
        return None


def _sanitize(title: str) -> str:
    title = title.strip().splitlines()[0]          # first line only
    title = re.sub(r"[^\w\s가-힣a-zA-Z0-9\-]", "", title)
    title = re.sub(r"\s+", "-", title.strip())
    return title[:50]
