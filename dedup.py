# dedup.py — 저장 기록 중복 검사 (중복 row를 trash 테이블로 이동, 파일은 유지)
import re
import hashlib
import threading
from difflib import SequenceMatcher

import config
from i18n import t

MAX_COMPARE_CHARS = 4000    # 비교용 텍스트 길이 상한 (앞부분만)
MAX_READ_CHARS    = 20000


def _read(filepath: str) -> str | None:
    # 저장된 텍스트 파일 읽기. 파일이 없거나 못 읽으면 None
    try:
        with open(filepath, encoding="utf-8", errors="ignore") as f:
            return f.read(MAX_READ_CHARS)
    except OSError:
        return None


def _normalize(text: str) -> str:
    # 공백/줄바꿈 차이는 무시하고 비교
    return re.sub(r"\s+", " ", text).strip()[:MAX_COMPARE_CHARS]


def _hash(norm: str) -> str:
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()


def _similarity(a: str, b: str, threshold: float) -> float:
    """정규화된 두 텍스트의 유사도(0~1). 기준 미달이 확실하면 조기 탈락."""
    la, lb = len(a), len(b)
    if la == 0 or lb == 0:
        return 0.0
    if min(la, lb) / max(la, lb) < threshold * 0.8:
        return 0.0                      # 길이 차이만으로 기준 미달
    sm = SequenceMatcher(None, a, b)
    if sm.real_quick_ratio() < threshold or sm.quick_ratio() < threshold:
        return 0.0
    return sm.ratio()


def _find_duplicate(norm: str, h: str, keepers: list[dict],
                    threshold: float) -> tuple[dict | None, int]:
    """keepers 중 중복 대상을 찾는다. (대상, 유사도 %) 반환."""
    for k in keepers:
        if k["hash"] == h:
            return k, 100
    for k in keepers:
        r = _similarity(norm, k["norm"], threshold)
        if r >= threshold:
            return k, round(r * 100)
    return None, 0


def scan_existing(threshold_pct: int,
                  progress_cb=None) -> tuple[list[dict], int]:
    """
    기존 텍스트 저장 기록 전체를 오래된 순으로 검사한다.
    가장 먼저 저장된 문서를 원본으로 남기고, 중복은 trash로 이동.
    (이동된 row 목록, 파일 없음으로 건너뛴 수)를 반환한다.
    """
    threshold = threshold_pct / 100.0
    rows = config.history_rows("text")
    keepers: list[dict] = []
    moved:   list[dict] = []
    missing = 0

    for i, row in enumerate(rows):
        if progress_cb:
            progress_cb(i + 1, len(rows))
        raw = _read(row["filepath"])
        if raw is None:
            missing += 1
            continue
        norm = _normalize(raw)
        if not norm:
            continue
        h = _hash(norm)

        dup_of, pct = _find_duplicate(norm, h, keepers, threshold)
        if dup_of:
            reason = t("dedup_reason", name=dup_of["filename"], pct=pct)
            if config.history_move_to_trash(row["id"], reason):
                moved.append({**row, "reason": reason})
        else:
            keepers.append({"norm": norm, "hash": h,
                            "filename": row["filename"]})

    config.log_add("INFO", "dedup",
                   f"전체 검사 완료 — {len(rows)}건 중 {len(moved)}건 이동, "
                   f"파일 없음 {missing}건 (기준 {threshold_pct}%)")
    return moved, missing


def check_new_async(hist_id: int, filename: str, text: str, on_dup=None):
    """
    방금 저장된 텍스트를 백그라운드에서 기존 기록과 비교한다.
    중복이면 해당 row를 trash로 이동하고 on_dup(reason)을 호출한다.
    """
    if not config.get_bool("dedup_auto"):
        return

    def _run():
        try:
            threshold_pct = int(config.get("dedup_threshold") or "90")
            threshold = threshold_pct / 100.0
            norm = _normalize(text)
            if not norm:
                return
            h = _hash(norm)

            keepers = []
            for row in config.history_rows("text"):
                if row["id"] == hist_id:
                    continue
                raw = _read(row["filepath"])
                if raw is None:
                    continue
                n2 = _normalize(raw)
                if n2:
                    keepers.append({"norm": n2, "hash": _hash(n2),
                                    "filename": row["filename"]})

            dup_of, pct = _find_duplicate(norm, h, keepers, threshold)
            if not dup_of:
                return
            reason = t("dedup_reason", name=dup_of["filename"], pct=pct)
            if config.history_move_to_trash(hist_id, reason):
                config.log_add("INFO", "dedup", f"자동 검사: {filename} → 휴지통 ({reason})")
                if on_dup:
                    on_dup(reason)
        except Exception as e:
            config.log_add("ERROR", "dedup", f"자동 검사 예외: {type(e).__name__}: {e}")

    threading.Thread(target=_run, daemon=True).start()
