# TXTDrop 완료보고서 인덱스

## 01. 문서 위치

| 유형 | 위치 |
|------|------|
| 기준 명세 | `docs\기능명세.md` |
| 완료보고서 | `docs\reports\*.md` |
| 코드 검토/개선 제안 | `docs\전체검토-및-개선제안-2026-07-05.md` |
| Outline 위키 원본 | `docs\outline-wiki\*.md` |
| Codex 검증 보고서 | `docs\codex-verification-YYYY-MM-DD-*.md` |
| 빌드 산출물 | `dist\TXTDrop\TXTDrop.exe` |
| 설치 파일 | `Output\TXTDropSetup.exe` |

## 02. 핵심 규칙

* 기능 변경 후 `docs\기능명세.md`와 Outline 위키 원본을 함께 갱신한다.
* Outline 문서는 로컬 Markdown 원본을 기준으로 재생성 가능해야 한다.
* 빌드 검증은 PyInstaller onedir 산출물 생성 여부까지 확인한다.
* 토큰, API 키, 개인 경로의 비공개 내용은 보고서나 Outline 문서에 포함하지 않는다.

## 03. 주요 완료보고서

### 2026-07-10 AI 기억 캡처 (Ctrl+Shift+M, TXTAIMemory 연계)

요약:

* Outline 위키의 v0.8 증분 PRD(유미 작성)를 확인·구현
* `memory_client.py`가 TXTAIMemory control API(:47530) `/write`를 직접 호출(`source=drop`), 자동 기동 없이 오프라인 시 로컬 파일(`ai_memory_inbox/*.jsonl`) 폴백
* PRD의 페어링 절차는 실제 TXTAIMemory API에 없는 개념(localhost 전용·무인증)이라 생략
* 기본 비활성(옵트인) — 기존 사용자 동작 무영향
* 모킹 테스트 + 실서버 E2E(원장 반영 확인) + 실단축키 통합 테스트 통과, master 병합(`d21a9ff`)

관련 파일:

* `memory_client.py`, `main.py`, `config.py`, `settings_window.py`, `i18n.py`
* `docs\reports\완료보고_20260710_AI기억캡처_TXTAIMemory연계_ClaudeCode.md`

### 2026-07-10 TTS 자동 기동 (MCP 경로 정합)

요약:

* TXTDrop 낭독이 MCP `svil_tts_speak`의 자동 기동 오케스트레이션을 타지 않던 문제 확인
* `tts_client.py`에 SVIL 웹 백엔드(:3000) `/api/local-server` 경유 자동 기동 + 최대 60초 헬스체크 폴링 추가
* 모킹 테스트 4종(이미 켜짐/자동기동 성공/타임아웃/기동요청 실패) + 실서버 검증, master 병합(`9da160f`)·배포·재시작 확인

관련 파일:

* `tts_client.py`, `main.py`, `i18n.py`, `docs\기능명세.md`

### 2026-07-08 TTS 낭독 단축키 (Ctrl+Shift+X)

요약:

* 선택/클립보드 텍스트를 SVIL TTS 프록시(:8765) `POST /api/tts/pipeline`로 낭독
* 선택 자동 복사 후 클립보드 원복, 2000자 상한, URL·마크다운 제거 전처리
* 실서버 E2E 검증(음성 생성·재생 큐 등록), master 병합·배포·재시작 확인

관련 파일:

* `tts_client.py`, `main.py`, `config.py`, `settings_window.py`, `i18n.py`
* `docs\reports\완료보고_20260708_TTS낭독단축키_ClaudeCode.md`

### 2026-07-08 중복 문서 제거 (trash)

요약:

* 저장 직후 백그라운드 중복 검사 (SHA-256 완전 동일 + difflib 유사도)
* 중복 시 `history` row를 `trash`로 이동(파일 유지), 트레이 "중복제거" 창에서 복구
* 로직 테스트 통과, master 병합

관련 파일:

* `dedup.py`, `dedup_window.py`, `config.py`, `main.py`, `settings_window.py`, `i18n.py`
* `docs\reports\완료보고_20260708_중복문서제거_ClaudeCode.md`

### 2026-07-09 TXTBrain 내용 해시 중복 차단 (연계)

요약:

* TXTBrain 수집 파이프라인에 내용 해시 기반 자동 중복 차단 추가 (TXTBrain v1.7.0)
* TXTDrop이 매번 다른 파일명으로 저장해도 동일 내용을 걸러냄
* 전체 테스트 30개 통과, TXTBrain main 병합 (완료보고서는 TXTBrain 저장소에 위치)

### 2026-07-06 v0.6.1 실행 안정화

요약:

* 첫 실행 `_first_run()` 데드락 수정 (mainloop 전 직접 Tk 호출)
* `keyboard.add_hotkey()` 예외 처리 및 기본값 폴백
* 절전 WNDPROC 핸들러 비활성화 (PyInstaller 크래시 방지)
* `docs\` 전체 문서 v0.6.1 기준 갱신

관련 파일:

* `main.py`, `docs\기능명세.md`, `docs\outline-wiki\*.md`

### 2026-07-05 v0.6 기능 확장

요약:

* 트레이 "Ollama 새로고침" 메뉴 추가
* Ollama 미연결 시 클립보드 첫 줄 파일명 폴백
* `os._exit(0)` 프로세스 즉시 종료
* 설정 창 Ollama 실시간 상태 확인
* Inno Setup `CloseApplications=yes`

관련 파일:

* `main.py`, `i18n.py`, `settings_window.py`, `installer.iss`

### 2026-07-05 전체 코드 검토

요약:

* Critical/Major/Minor/Enhancement 이슈 분류
* SQLite 다중 스레드 동시 쓰기, 설정값 불일치, 파일명 충돌 등 식별
* 상세: `docs\전체검토-및-개선제안-2026-07-05.md`

### 2026-06-28 프로젝트 점검 및 수정

요약:

* 전체 프로젝트 구조와 구현 상태 점검
* `ollama_autostart` 설정 미반영 문제 수정
* PyInstaller onedir 빌드 실패 원인 확인 및 `build.bat` 보강
* 컴파일, 스모크 테스트, PyInstaller 빌드 검증 통과

관련 파일:

* `main.py`, `build.bat`, `docs\기능명세.md`

### 2026-06-28 Outline 프로젝트 위키 구축

요약:

* TXTDrop 프로젝트 위키 허브와 하위 문서 원본 생성
* PRD, 구현 스펙, 아키텍처, 개발진행 히스토리, 완료보고서 인덱스 구성
* Outline 등록 후 문서 ID와 URL을 검증 보고서에 기록

## 04. 검색 키워드

* TXTDrop, TXTDrop 프로젝트 위키, TXTDrop PRD, TXTDrop 구현 스펙, TXTDrop 아키텍처, TXTDrop 개발진행 히스토리, TXTDrop 완료보고서 인덱스
* TTS 낭독, Ctrl+Shift+X, tts_client, SVIL TTS 프록시
* TTS 자동 기동, svil_tts_speak, local-server, 웹 백엔드 3000, 헬스체크
* AI 기억 캡처, Ctrl+Shift+M, memory_client, TXTAIMemory, control API 47530, ai_memory_inbox
* 중복제거, trash, dedup, difflib
* TXTBrain 연계, 내용 해시 중복 차단
* ollama_autostart, ollama 새로고침, PyInstaller onedir, build.bat, 첫 실행 데드락, os._exit
