# tts_client.py — SVIL TTS 프록시(:8765) HTTP 클라이언트
import json
import re
import urllib.request
import urllib.error

import config
from i18n import t

TTS_URL   = "http://127.0.0.1:8765"
MAX_CHARS = 2000   # SVIL TTS 운영 상한 — 초과분은 잘라서 낭독


def is_running() -> bool:
    # 프록시 헬스체크 (2초 타임아웃)
    try:
        urllib.request.urlopen(f"{TTS_URL}/health", timeout=2)
        return True
    except Exception:
        return False


def _clean(text: str) -> str:
    # 음성 친화 정리: URL·마크다운 기호 제거, 공백 정규화
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    text = re.sub(r"[*_`#>|~\[\]]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def speak(text: str) -> tuple[bool, str]:
    """
    클립보드 텍스트를 SVIL TTS 파이프라인으로 낭독.
    (성공 여부, 실패 시 사용자용 메시지)를 반환한다.
    서버가 생성 후 재생 큐에 넣으므로(play_async) 응답까지 수십 초 걸릴 수 있다.
    """
    cleaned = _clean(text)
    if not cleaned:
        return False, t("save_fail_empty")
    truncated = len(cleaned) > MAX_CHARS
    cleaned = cleaned[:MAX_CHARS]

    payload = json.dumps({
        "text":           cleaned,
        "category":       "narration",
        "play":           True,
        "play_async":     True,
        "register_asset": False,
    }).encode()

    config.log_add("INFO", "tts",
                   f"낭독 요청 → {len(cleaned)}자" + (" (2000자 초과 잘림)" if truncated else ""))
    try:
        req = urllib.request.Request(
            f"{TTS_URL}/api/tts/pipeline",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=180) as r:
            result = json.loads(r.read())
            if result.get("ok"):
                config.log_add("INFO", "tts",
                               f"생성 완료 — {result.get('duration_sec', '?')}초, "
                               f"재생 큐 등록: {result.get('played')}")
                return True, ""
            config.log_add("WARN", "tts", f"응답 이상: {result}")
            return False, t("tts_fail_response")
    except urllib.error.HTTPError as e:
        try:
            detail = json.loads(e.read()).get("detail", "")
        except Exception:
            detail = ""
        config.log_add("ERROR", "tts", f"HTTP {e.code}: {detail}")
        return False, detail or f"HTTP {e.code}"
    except urllib.error.URLError as e:
        config.log_add("ERROR", "tts", f"연결 실패: {e.reason}")
        return False, t("tts_offline")
    except TimeoutError:
        config.log_add("WARN", "tts", "타임아웃 (180s)")
        return False, t("tts_timeout")
    except Exception as e:
        config.log_add("ERROR", "tts", f"예외: {type(e).__name__}: {e}")
        return False, str(e)
