# 완료보고 — AI 기억 캡처 (Ctrl+Shift+M, TXTAIMemory 연계)

- 일자: 2026-07-10
- 작업자: Claude Code
- 브랜치: master

## 배경

Outline 위키(TXTDrop 프로젝트 위키) 하위에 유미가 작성한 "TXTDrop v0.8 업데이트 PRD — TXTAIMemory 연계" 증분 PRD가 있었다. 선택 텍스트를 파일이 아니라 TXTAIMemory(AI 대화·작업 맥락 기억 시스템) 원장에 직접 캡처하는 새 단축키를 제안하는 문서로, v0.7 기존 구현은 건드리지 않는 증분 설계였다.

## PRD 대비 실제 구현 확인 사항

PRD 작성 시점(2026-07-09 10:52) 가정과 달리, 확인해보니 TXTAIMemory는 이미 v0.7.0으로 상당히 진행되어 있었다:

- control API가 `http://127.0.0.1:47530`에서 실제로 기동 중 (`/health` 확인)
- `POST /write` 엔드포인트가 PRD의 `memory_write` 계약과 거의 동일한 스펙(`content`, `source`, `ai_id`, `origin_app`, `importance`)으로 이미 구현됨
- TXTAIMemory 쪽에 `capture_cli.py`라는 "TXTDrop 능동 캡처 진입점"까지 미리 마련되어 있었으나, 별도 실행파일로 패키징되어 있지 않아 PyInstaller로 얼린 TXTDrop에서 직접 호출 불가능 (Python 인터프리터·패키지 의존)
- control API 코드 주석에 **"localhost 전용, 인증 없음(같은 머신의 자기 앱만 호출한다는 전제)"**로 명시되어 있어, PRD §3.4가 제안한 페어링/토큰 절차는 실제로 존재하지 않는 개념이었음

이에 따라 **HTTP `/write` 직접 호출** 방식으로 구현하고, PRD의 페어링 절차는 생략했다 (TTS·중복제거와 동일하게 로컬 서비스에 직접 붙는 기존 TXTDrop 패턴과 일치).

## 변경 내역

| 파일 | 내용 |
|------|------|
| `memory_client.py` (신규) | TXTAIMemory control API(:47530) 클라이언트. `POST /write`(source=drop), 오프라인 시 자동 기동하지 않고 `ai_memory_inbox/YYYYMMDD.jsonl`에 JSON 라인 폴백 저장 |
| `config.py` | 기본값 `memory_enabled=false`(옵트인), `memory_hotkey=ctrl+shift+m`, `memory_char_limit=8000` |
| `main.py` | `_grab_selection`에 trigger_key 매개변수 추가(x/m 공용), `_active_window_title()`(origin_app용, best-effort), `capture_memory()`, 활성화 토글에 따라 단축키를 등록/해제하는 로직 |
| `settings_window.py` | "AI 기억 (TXTAIMemory)" 섹션 — 사용 여부 체크박스 + 단축키 캡처 행 |
| `i18n.py` | AI 기억 관련 ko/en 문자열 |
| `docs/기능명세.md` | 4.2절 AI 기억 캡처 신설, 설정 항목·기본값·로그 카테고리 갱신 |

## PRD 대비 축소/보류한 항목

- §3.4 페어링/토큰: TXTAIMemory 실제 API에 해당 개념이 없어 생략
- `ai_id` 자동 판별: PRD 자체가 best-effort로 규정했고, 판별 로직 없이 비워 보내 TXTAIMemory가 미분류 처리하도록 함 (§3.2와 일치)
- 이중 저장(파일+메모리 병행) 옵션: PRD §10 열린 결정사항 중 하나로, 기본(메모리만)만 구현하고 옵션은 보류
- `memory_history` 별도 테이블: 기존 `log` 테이블(`memory` 카테고리)로 감사 추적을 충분히 커버한다고 판단해 생략

## 검증

- 모킹 테스트 3종: 오프라인 폴백 저장(JSON 라인 확인), 빈 텍스트 거부, 온라인 실서버 캡처
- 실서버 E2E: `memory_client.capture()` 호출 → TXTAIMemory `/raw`에서 `source=drop`으로 즉시 조회됨
- 재빌드·배포 후 실제 설치본에서 `memory_enabled=true`로 전환 → 시작 로그에 "AI 기억 단축키 등록: ctrl+shift+m" 확인 → 실제 `Ctrl+Shift+M` 입력 → 로그의 캡처 id와 TXTAIMemory 원장의 id가 일치함을 확인
- 검증 후 `memory_enabled`를 기본값(`false`)으로 복원, 재시작 확인

## 참고

- 기본이 비활성(opt-in)이라, 기존 사용자는 이번 업데이트로 동작이 전혀 바뀌지 않는다.
- TXTAIMemory가 꺼져 있어도 앱이 죽지 않고 로컬 파일로 안전하게 넘어간다 (자동 기동 시도는 하지 않음 — TTS와 다른 정책, PRD §3.3에 명시된 설계).
