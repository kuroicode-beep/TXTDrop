# memory_client.py — TXTAIMemory 캡처 클라이언트 (:47530, control API)
import json
import os
import datetime
import urllib.request
import urllib.error

import config
from i18n import t

MEMORY_URL = "http://127.0.0.1:47530"
DEFAULT_MAX_CHARS = 8000   # PRD 기본 상한


def is_running() -> bool:
    # control API 헬스체크 (2초 타임아웃)
    try:
        urllib.request.urlopen(f"{MEMORY_URL}/health", timeout=2)
        return True
    except Exception:
        return False


def _fallback_dir() -> str:
    base = config.get("text_save_folder") or os.getcwd()
    d = os.path.join(base, "ai_memory_inbox")
    os.makedirs(d, exist_ok=True)
    return d


def _write_fallback(text: str) -> str | None:
    """TXTAIMemory 오프라인 시 JSON 라인으로 로컬 보관 (일자별 파일).
    실패 시 None을 반환한다."""
    try:
        path = os.path.join(_fallback_dir(), f"{datetime.datetime.now():%Y%m%d}.jsonl")
        record = {
            "content": text,
            "source": "drop",
            "captured_at": datetime.datetime.now().isoformat(),
        }
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        return path
    except OSError as e:
        config.log_add("ERROR", "memory", f"폴백 저장 실패: {e}")
        return None


def capture(text: str, origin_app: str | None = None) -> tuple[bool, str, bool]:
    """
    선택/클립보드 텍스트를 TXTAIMemory 원장(raw)에 기록한다 (source=drop).
    TXTAIMemory가 꺼져 있으면 자동 기동하지 않고 로컬 파일로 폴백 저장한다.
    (성공 여부, 사용자 메시지, 폴백 사용 여부)를 반환한다.
    """
    text = (text or "").strip()
    if not text:
        return False, t("save_fail_empty"), False

    max_chars = int(config.get("memory_char_limit") or DEFAULT_MAX_CHARS)
    truncated = len(text) > max_chars
    text = text[:max_chars]

    if not is_running():
        config.log_add("WARN", "memory", "TXTAIMemory 오프라인 — 폴백 저장 시도")
        path = _write_fallback(text)
        if path:
            return True, t("memory_fallback_saved"), True
        return False, t("memory_fallback_failed"), False

    payload = json.dumps({
        "content":    text,
        "source":     "drop",
        "origin_app": origin_app,
    }).encode()

    config.log_add("INFO", "memory",
                   f"캡처 요청 → {len(text)}자" + (" (상한 초과 잘림)" if truncated else ""))
    try:
        req = urllib.request.Request(
            f"{MEMORY_URL}/write",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            result = json.loads(r.read())
            config.log_add("INFO", "memory", f"캡처 완료 — id={result.get('id')}")
            return True, "", False
    except Exception as e:
        config.log_add("ERROR", "memory", f"전송 실패: {type(e).__name__}: {e}")
        path = _write_fallback(text)
        if path:
            return True, t("memory_fallback_saved"), True
        return False, t("memory_fallback_failed"), False
