# 완료보고 — TXTDrop 클립보드 낭독 단축키 (Ctrl+Shift+X)

- 일자: 2026-07-08
- 작업자: Claude Code
- 브랜치: claude/svil-tts-mcp-shortcut-341aa2

## 요약

`Ctrl+Shift+X`를 누르면 클립보드 텍스트를 SVIL TTS 파이프라인(GPT-SoVITS + RVC)으로 즉시 낭독하는 기능을 추가했다. MCP tool(`svil_tts_speak`)이 사용하는 것과 동일한 백엔드인 TTS 프록시(`http://127.0.0.1:8765`)의 `POST /api/tts/pipeline`을 직접 호출한다.

## 변경 내역

| 파일 | 내용 |
|------|------|
| `tts_client.py` (신규) | TTS 프록시 HTTP 클라이언트. 음성 친화 전처리(URL·코드블록·마크다운 기호 제거), 2,000자 상한, 180초 타임아웃, 실패 유형별 한국어 메시지 반환 |
| `main.py` | `speak_clipboard()` 추가, 저장/낭독 단축키 등록 로직 공통화(`_register`/`_rebind`), 설정 저장 시 낭독 단축키도 재등록 |
| `config.py` | 기본값 `tts_hotkey: ctrl+shift+x` 추가 |
| `settings_window.py` | 단축키 섹션에 "낭독 단축키" 캡처 행 추가, 저장 처리 |
| `i18n.py` | 낭독 관련 ko/en 문자열 추가, 기존 단축키 라벨을 "저장 단축키"로 명확화 |
| `docs/기능명세.md` | 4장 단축키 표 갱신 + 4.1 클립보드 낭독 절 신설, 기본 설정값·로그 카테고리 갱신 |

## 동작 흐름

1. `Ctrl+Shift+X` → 클립보드 텍스트 확인 (비어 있으면 로그만 남김)
2. "음성 낭독 준비 중" 토스트 표시
3. 백그라운드 스레드에서 `POST /api/tts/pipeline` 호출 (`category: narration`, `play_async: true`, `register_asset: false`)
4. 서버가 음성 생성 후 재생 큐에 등록 → 워크스테이션 스피커 재생
5. 실패 시(서버 미기동·타임아웃 등) 오류 토스트 + `tts` 카테고리 로그

## 검증

- `py_compile` 5개 파일 통과
- 실서버 E2E: `/health` 응답 확인, 전처리 함수 결과 확인, `speak()` 호출 → `ok: true`, 음성 생성·재생 큐 등록 확인 (2026-07-08)

## 참고

- TTS 서버가 꺼져 있으면 MCP tool과 달리 자동 기동하지 않는다. 이 경우 "SVIL TTS 서버(:8765)에 연결할 수 없습니다." 토스트가 뜨며, 트레이(svil-tray)에서 TTS를 켠 뒤 다시 시도하면 된다.
- 낭독 결과 WAV는 서버 정책에 따라 `tts_system/output/narration/`에 저장되지만, TXTDrop에서는 assets 등록을 하지 않는다(`register_asset: false`).
