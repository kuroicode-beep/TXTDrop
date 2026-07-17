# tts_client.py — SVIL TTS 프록시(:8765) HTTP 클라이언트
import json
import re
import time
import urllib.request
import urllib.error

import config
from i18n import t

TTS_URL   = "http://127.0.0.1:8765"
WEB_URL   = "http://127.0.0.1:3000"   # SVIL 웹 백엔드 — 로컬 서비스 자동 기동 (MCP svil_tts_speak과 동일 경로)
MAX_CHARS = 2000   # SVIL TTS 운영 상한 — 초과분은 잘라서 낭독
AUTOSTART_TIMEOUT = 60   # 자동 기동 요청 후 헬스체크 대기 상한(초)


def is_running() -> bool:
    # 프록시 헬스체크 (2초 타임아웃)
    try:
        urllib.request.urlopen(f"{TTS_URL}/health", timeout=2)
        return True
    except Exception:
        return False


def _start_service() -> bool:
    """SVIL 웹 백엔드에 TTS 서비스 시작을 요청한다 (MCP svil_tts_speak과 동일한 자동 기동 경로)."""
    payload = json.dumps({"action": "start", "id": "tts"}).encode()
    try:
        req = urllib.request.Request(
            f"{WEB_URL}/api/local-server",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            result = json.loads(r.read())
            ok = bool(result.get("ok"))
            if not ok:
                config.log_add("WARN", "tts", f"자동 기동 요청 거부: {result}")
            return ok
    except Exception as e:
        config.log_add("WARN", "tts", f"자동 기동 요청 실패: {type(e).__name__}: {e}")
        return False


def _ensure_running(on_starting=None) -> bool:
    """TTS 프록시가 꺼져 있으면 웹 백엔드를 통해 자동 기동을 시도한다."""
    if is_running():
        return True

    config.log_add("INFO", "tts", "TTS 서버 미실행 — 자동 기동 시도")
    if on_starting:
        on_starting()
    if not _start_service():
        return False

    deadline = time.monotonic() + AUTOSTART_TIMEOUT
    while time.monotonic() < deadline:
        if is_running():
            config.log_add("INFO", "tts", "자동 기동 완료 — 서버 응답 확인")
            return True
        time.sleep(2)

    config.log_add("WARN", "tts", f"자동 기동 후 {AUTOSTART_TIMEOUT}초 내 응답 없음")
    return False


def _clean(text: str) -> str:
    # 음성 친화 정리: URL·마크다운 기호 제거, 공백 정규화
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    text = re.sub(r"[*_`#>|~\[\]]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


# ── 설정 → pipeline 요청 필드 변환 ────────────────────────────────────────────

def _speed_to_pct(speed) -> int:
    """배속 문자열(1.0=보통)을 서버 speed_pct 오프셋(-50~+50, 0=보통)으로 변환."""
    try:
        pct = round((float(speed) - 1.0) * 100)
    except (TypeError, ValueError):
        return 0
    return max(-50, min(50, pct))


def _settings_overrides() -> dict:
    """저장된 tts_* 설정을 pipeline 요청 필드로 변환한다 (auto/빈 값은 생략)."""
    o: dict = {}
    engine = (config.get("tts_engine") or "auto").strip()
    if engine and engine != "auto":
        o["engine"] = engine
    voice = (config.get("tts_voice") or "").strip()
    if voice:
        o["voice_name"] = voice
    pct = _speed_to_pct(config.get("tts_speed") or "1.0")
    if pct:
        o["speed_pct"] = pct
    use_rvc = config.get_bool("tts_use_rvc")
    o["use_rvc"] = use_rvc
    model = (config.get("tts_rvc_model") or "").strip()
    if use_rvc and model:
        o["rvc_model"] = model
    return o


def capabilities() -> dict:
    """
    설정 UI용: 엔진 로드 상태(/status가 진실)·보이스·RVC 모델을 한 번에 조회.
    서버 오프라인이면 online=False, 개별 목록 실패는 빈 리스트로 가린다.
    """
    def _get(path, default):
        # status는 내부에서 엔진 3종 헬스체크(각 2s)를 돌아 오프라인이 많으면 느리다
        try:
            with urllib.request.urlopen(f"{TTS_URL}{path}", timeout=12) as r:
                return json.loads(r.read())
        except Exception:
            return default

    status = _get("/api/tts/status", None)
    if status is None:
        return {"online": False, "engines": {}, "rvc_online": False,
                "default_engine": "", "voices": [], "rvc_models": []}
    return {
        "online": True,
        "engines": {
            "gptsovits": bool(status.get("gptsovits")),
            "qwen3":     bool(status.get("qwen3")),
        },
        "rvc_online":     bool(status.get("rvc")),
        "default_engine": status.get("default_engine") or "",
        "voices":         _get("/api/tts/voices", []) or [],
        "rvc_models":     _get("/api/rvc/models", []) or [],
    }


def speak(text: str, on_starting=None) -> tuple[bool, str]:
    """
    클립보드 텍스트를 SVIL TTS 파이프라인으로 낭독 (저장된 tts_* 설정 적용).
    (성공 여부, 실패 시 사용자용 메시지)를 반환한다.
    서버가 생성 후 재생 큐에 넣으므로(play_async) 응답까지 수십 초 걸릴 수 있다.
    TTS 서버가 꺼져 있으면 MCP svil_tts_speak과 동일하게 자동 기동을 먼저 시도한다.
    """
    cleaned = _clean(text)
    if not cleaned:
        return False, t("save_fail_empty")
    truncated = len(cleaned) > MAX_CHARS
    cleaned = cleaned[:MAX_CHARS]

    log = f"낭독 요청 → {len(cleaned)}자" + (" (2000자 초과 잘림)" if truncated else "")
    return _pipeline(cleaned, _settings_overrides(), log, on_starting)


def preview(engine: str, voice: str, speed: str, rvc: str,
            on_starting=None) -> tuple[bool, str]:
    """
    설정 화면 미리듣기 — 저장 전 조합을 그대로 합성해 서버 재생 큐로 재생한다.
    rvc: "off"=사용 안 함, ""=자동(서버 기본), 그 외=RVC 모델 이름.
    """
    o: dict = {}
    if engine and engine != "auto":
        o["engine"] = engine
    if voice:
        o["voice_name"] = voice
    pct = _speed_to_pct(speed)
    if pct:
        o["speed_pct"] = pct
    if rvc == "off":
        o["use_rvc"] = False
    else:
        o["use_rvc"] = True
        if rvc:
            o["rvc_model"] = rvc
    return _pipeline(t("tts_preview_text"), o,
                     f"미리듣기 → engine={engine or 'auto'}, voice={voice or '기본'}, rvc={rvc or '자동'}",
                     on_starting)


def _pipeline(text: str, overrides: dict, log_msg: str,
              on_starting=None) -> tuple[bool, str]:
    """공용 pipeline 호출 — 자동 기동, 요청, 에러 메시지 정리까지 처리."""
    if not _ensure_running(on_starting):
        return False, t("tts_offline")

    payload = json.dumps({
        "text":           text,
        "category":       "narration",
        "play":           True,
        "play_async":     True,
        "register_asset": False,
        **overrides,
    }).encode()

    config.log_add("INFO", "tts", log_msg)
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
