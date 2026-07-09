# TXTDrop 개발진행 히스토리

## 01. 요약

TXTDrop은 v0.7 + AI 기억 캡처 기준으로 Windows 트레이 상주, 전역 단축키 클립보드 저장, Ollama 제목 생성, SVIL TTS 낭독(Ctrl+Shift+X, 자동 기동 포함), AI 기억 캡처(Ctrl+Shift+M, 옵트인, TXTAIMemory 연계), 저장 기록 중복제거(trash), 설정/로그/히스토리/중복제거 UI, PyInstaller onedir/Inno Setup 배포 흐름을 갖춘 상태다. 저장 폴더의 `.txt`는 연계 앱 TXTBrain이 수집한다.

## 02. 주요 마일스톤

### v0.7 후속 2 (2026-07-10) — AI 기억 캡처 (TXTAIMemory 연계)

* Outline 위키에 있던 유미 작성 "v0.8 업데이트 PRD — TXTAIMemory 연계"를 확인·구현
* 새 단축키 `Ctrl+Shift+M`(기본 비활성, 옵트인) — 선택 텍스트를 TXTAIMemory 원장(`source=drop`)에 직접 캡처
* `memory_client.py`: TXTAIMemory control API(:47530) `POST /write` 직접 호출, 자동 기동 없이 오프라인 시 `ai_memory_inbox/*.jsonl` 폴백 저장
* PRD 작성 시점 가정("TXTAIMemory 미구현")과 달리 실제로는 v0.7.0까지 진행되어 있었음을 확인 — 페어링/토큰 절차는 실제 API에 없는 개념이라 생략
* 모킹 테스트 + 실서버 E2E(TXTAIMemory 원장 반영 확인) + 실단축키 통합 테스트 통과, master 병합(`d21a9ff`)

### v0.7 후속 (2026-07-10) — TTS 자동 기동 (MCP 경로 정합)

* TXTDrop이 TTS 프록시(:8765)에 직접 붙어 MCP `svil_tts_speak`의 자동 기동 오케스트레이션을 못 타던 문제 발견·수정
* `tts_client.py`에 `_start_service`/`_ensure_running` 추가 — SVIL 웹 백엔드(:3000) `/api/local-server`로 기동 요청 후 최대 60초 헬스체크 폴링
* 자동 기동 중 "TTS 서버 시작 중" 토스트 표시, 모킹 테스트 4종 + 실서버 E2E 검증

### v0.7 (2026-07-08) — TTS 낭독·중복제거

* **TTS 낭독 단축키(Ctrl+Shift+X)**: 선택 텍스트(없으면 클립보드)를 SVIL TTS 프록시(:8765)로 낭독. 선택 자동 복사 후 클립보드 원복, 2000자 상한, 음성 친화 전처리
* **중복제거(trash)**: 저장 직후 백그라운드에서 기존 기록과 비교(SHA-256 + difflib), 중복이면 `history` row를 `trash`로 이동(파일은 유지). 트레이 "중복제거" 창에서 전체 스캔·유사도 조정·휴지통 복구
* **TXTBrain 연계(2026-07-09)**: TXTBrain 수집 파이프라인에 내용 해시 기반 자동 중복 차단 추가(TXTBrain v1.7.0). TXTDrop이 매번 다른 파일명으로 저장해도 동일 내용을 걸러냄

### v0.6.1 (2026-07-06) — 실행 안정화

* **첫 실행 데드락 수정**: `_first_run()`에서 `call_on_main` + `event.wait()` 제거 → `mainloop()` 전 메인 스레드에서 직접 `messagebox`/`filedialog` 호출
* **단축키 등록 예외 처리**: `keyboard.add_hotkey()` 실패 시 기본값 `ctrl+shift+z`로 재시도, 설정 변경 시에도 try/except
* **절전 핸들러 비활성화**: PyInstaller frozen 런타임 `STATUS_STACK_BUFFER_OVERRUN` 크래시 방지를 위해 WNDPROC 패치를 no-op으로 전환

### v0.6 (2026-07-05) — 기능 확장

* 트레이 메뉴 **"Ollama 새로고침"** 추가 — 상태 확인, 미실행 시 시작, 미설치 시 안내 토스트
* Ollama 미연결 시 파일명 폴백: **클립보드 첫 줄** 기반 제목
* 시작 시 Ollama 자동 시작: `ollama_autostart=true`일 때만 무음 시도 (에러 토스트 없음)
* `os._exit(0)` 종료 — `keyboard` 논데몬 스레드 즉시 종료
* 설정 창 Ollama 상태: `is_running()` 실시간 확인 (stale 캐시 문제 수정)
* Inno Setup `CloseApplications=yes` — 설치 시 실행 중 프로세스 자동 종료

### v0.4 ~ v0.5 — 안정화 이터레이션

* Tkinter `mainloop()` 메인 스레드 이관 (`tray.run_detached()` + `mainloop()`)
* 토스트 work area 기준 위치, 스택, 5초 표시
* Ollama 상태 캐싱, 제목 생성 로깅, 20초 타임아웃
* 설정/로그 창 singleton 재생성 버그 수정
* 다크 트레이 메뉴, 다크 설치 마법사

### v0.2 ~ v0.3 — AI/설정/로그

* Ollama AI 제목 생성, SQLite 마이그레이션
* 설정 창, 로그/저장 이력 창, 토스트 알림
* DB 백업/복원, 단축키 캡처, i18n (한국어/English)

### v0.1 — 초기 완성

* 클립보드 텍스트/이미지 저장, 트레이, 전역 단축키
* PyInstaller + Inno Setup 빌드 파이프라인

## 03. 2026-07-10 AI 기억 캡처 작업 내역

* Outline 위키를 훑어보다 하위에 있던 v0.8 증분 PRD(TXTAIMemory 연계, 유미 작성)를 발견
* TXTAIMemory 프로젝트를 직접 조사 — PRD 가정과 달리 이미 v0.7.0, control API(:47530) 실행 중, `/write` 엔드포인트 존재, `capture_cli.py`(TXTDrop 전용 진입점)까지 마련되어 있었으나 exe로 패키징되지 않음
* control API 코드 주석에서 "localhost 전용, 인증 없음" 확인 → PRD의 페어링 절차는 실제로 존재하지 않는 개념이라 생략, HTTP 직접 호출로 구현
* `memory_client.py`, `capture_memory()`, 설정 UI(옵트인 토글+단축키) 구현
* 모킹 테스트 3종 + 실서버 E2E(TXTAIMemory `/raw`에서 캡처 확인) + 실제 설치본에서 `Ctrl+Shift+M` 눌러 로그·원장 id 일치 확인
* master 커밋 `d21a9ff` 푸시, 재빌드·배포·재시작, 검증 후 `memory_enabled`를 기본값(false)으로 복원

## 04. 2026-07-10 TTS 자동 기동 작업 내역

* 사용자 문의(낭독이 "개선된 MCP 루트"를 안 타는 것 같다)를 받고 svil-ai-work 백엔드/MCP 소스 조사
* 확인 결과: 음질 개선(문장분할·환청재시도·RVC 음색일치)은 `/api/tts/pipeline` 엔드포인트 자체에 통합되어 있어 TXTDrop도 이미 적용받는 중이었음
* 유일한 실제 차이는 **자동 기동** — MCP만 웹 백엔드(:3000)를 통해 TTS 서비스를 깨우고, TXTDrop 직접 호출은 서버가 꺼져 있으면 그냥 실패
* `tts_client.py`에 동일 자동 기동 로직 이식, 모킹 테스트 4종 + 실서버 `/api/local-server` 호출 검증 + 재빌드 후 실단축키 E2E 통과
* master 커밋 `9da160f` 푸시, 배포·재시작 확인

## 05. 2026-07-08~09 작업 내역

* TTS 낭독 단축키 구현·실서버 E2E 검증, master 병합·배포·재시작 확인
* 중복제거(trash 테이블 + 중복제거 창) 구현, 로직 테스트 통과, master 병합
* TXTBrain v1.7.0 내용 해시 중복 차단(연계) 구현, 전체 테스트 30개 통과, main 병합
* Outline 위키 v0.7 기준 갱신

## 06. 2026-06-28 점검 및 수정

* Python 컴파일 검증 통과
* 의존성 import 검증 통과
* SQLite 스모크 테스트 통과
* `ollama_autostart=false`일 때 시작 시 Ollama 자동 실행 미시도 확인
* PyInstaller onedir 빌드 성공, read-only 속성 해제 `build.bat` 보강
* Outline 프로젝트 위키 구축

## 07. 현재 운영 상태

| 항목 | 값 |
|------|-----|
| 소스 실행 | `py -3.12 main.py` |
| 빌드 | `build.bat` |
| 실행 파일 | `dist\TXTDrop\TXTDrop.exe` (onedir) |
| 설치 파일 | `Output\TXTDropSetup.exe` |
| 기준 명세 | `docs\기능명세.md` |

## 08. 남은 확인 포인트

* 실제 설치본에서 단축키 등록 권한과 트레이 메뉴 동작 확인
* Ollama 미설치/오프라인 상태별 UI 메시지 재확인
* 절전/복귀 후 단축키 지속성 (WNDPROC 핸들러 비활성화 상태)
* SQLite 다중 스레드 동시 쓰기 안정성 (`docs\전체검토-및-개선제안-2026-07-05.md` C1 참조)
* 유사(비동일) 문서까지 막으려면 임베딩 유사도 기반 정책 검토 (미구현)
* TTS 자동 기동은 웹 백엔드(:3000)까지 꺼진 상태(예: 워크스테이션 재부팅 직후)는 여전히 커버하지 못함
* AI 기억 캡처의 이중 저장(파일+메모리 병행) 옵션은 v0.8 PRD §10 열린 결정사항으로 보류 상태

## 09. 관련 문서

* `docs\기능명세.md` — 현재 구현 기준 기능 명세
* `docs\전체검토-및-개선제안-2026-07-05.md` — 코드 검토 및 개선 제안
* `docs\reports\` — 완료보고서 (TTS 낭독, 중복제거, AI 기억 캡처 등)
* `docs\outline-wiki\` — Outline 위키 원본
