# registry_client.py — SVIL 패밀리 로컬 디스커버리 레지스트리 기록 (TXTAIMemory registry.py 패턴 이식)
"""자기 항목을 %LOCALAPPDATA%\\SVIL\\registry.json에 기록해, TXT Tray 등 소비 측이
설치된 앱과 버전을 발견할 수 있게 한다(TXT 패밀리 연결프로토콜 v2.0 Phase 5).

TXTDrop은 서버가 없으므로 port·health_endpoint는 기록하지 않는다 — 소비 측은
전부 .get()으로 읽으므로 없어도 하위호환. exe_path는 PyInstaller frozen 빌드에서만
기록한다(개발 환경의 python.exe는 실행 대상이 아님).
이 기록 자체가 실패해도 앱 기동을 막지 않는다.
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from version import APP_VERSION


def _registry_path() -> Path:
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    return Path(base) / "SVIL" / "registry.json"


def register_app() -> None:
    """txtdrop 항목을 레지스트리에 기록(다른 앱이 이미 써둔 항목은 그대로 보존).

    실패(권한/디스크 오류 등)해도 예외를 삼킨다 — 단 원인은 stderr에 남긴다.
    """
    try:
        path = _registry_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {"schema_version": "1.0", "apps": {}}
        if path.exists():
            try:
                loaded = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(loaded, dict) and isinstance(loaded.get("apps"), dict):
                    data = loaded
            except (json.JSONDecodeError, OSError):
                pass
        entry = {
            "schema_version": "1.0",
            "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "app_version": APP_VERSION,
        }
        if getattr(sys, "frozen", False):
            entry["exe_path"] = sys.executable
        data.setdefault("apps", {})["txtdrop"] = entry
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(path)  # 원자적 교체 — 동시 기록 시 파일이 반쯤 쓰인 채로 노출되지 않음
    except Exception as e:
        # 레지스트리 기록 실패가 앱 기동을 막지 않도록 — 단 원인은 stderr에 남긴다
        print(f"[registry] register_app failed: {e}", file=sys.stderr)
