# TXTDrop 완료보고서 인덱스

## 01. 문서 위치

| 유형 | 위치 |
|------|------|
| 기준 명세 | `docs\기능명세.md` |
| 코드 검토/개선 제안 | `docs\전체검토-및-개선제안-2026-07-05.md` |
| Outline 위키 원본 | `docs\outline-wiki\*.md` |
| Codex 검증 보고서 | `docs\codex-verification-YYYY-MM-DD-*.md` |
| 빌드 산출물 | `dist\TXTDrop\TXTDrop.exe` |
| 설치 파일 | `Output\TXTDropSetup.exe` |

## 02. 핵심 규칙

- 기능 변경 후 `docs\기능명세.md`와 Outline 위키 원본을 함께 갱신한다.
- Outline 문서는 로컬 Markdown 원본을 기준으로 재생성 가능해야 한다.
- 빌드 검증은 PyInstaller onedir 산출물 생성 여부까지 확인한다.
- 토큰, API 키, 개인 경로의 비공개 내용은 보고서나 Outline 문서에 포함하지 않는다.

## 03. 주요 완료보고서

### 2026-07-06 v0.6.1 실행 안정화

요약:

- 첫 실행 `_first_run()` 데드락 수정 (mainloop 전 직접 Tk 호출)
- `keyboard.add_hotkey()` 예외 처리 및 기본값 폴백
- 절전 WNDPROC 핸들러 비활성화 (PyInstaller 크래시 방지)
- `docs\` 전체 문서 v0.6.1 기준 갱신

관련 파일:

- `main.py`
- `docs\기능명세.md`
- `docs\outline-wiki\*.md`

### 2026-07-05 v0.6 기능 확장

요약:

- 트레이 "Ollama 새로고침" 메뉴 추가
- Ollama 미연결 시 클립보드 첫 줄 파일명 폴백
- `os._exit(0)` 프로세스 즉시 종료
- 설정 창 Ollama 실시간 상태 확인
- Inno Setup `CloseApplications=yes`

관련 파일:

- `main.py`, `i18n.py`, `settings_window.py`, `installer.iss`

### 2026-07-05 전체 코드 검토

요약:

- Critical/Major/Minor/Enhancement 이슈 분류
- SQLite 다중 스레드 동시 쓰기, 설정값 불일치, 파일명 충돌 등 식별
- 상세: `docs\전체검토-및-개선제안-2026-07-05.md`

### 2026-06-28 프로젝트 점검 및 수정

요약:

- 전체 프로젝트 구조와 구현 상태 점검
- `ollama_autostart` 설정 미반영 문제 수정
- PyInstaller onedir 빌드 실패 원인 확인 및 `build.bat` 보강
- 컴파일, 스모크 테스트, PyInstaller 빌드 검증 통과

관련 파일:

- `main.py`, `build.bat`, `docs\기능명세.md`

### 2026-06-28 Outline 프로젝트 위키 구축

요약:

- TXTDrop 프로젝트 위키 허브와 하위 문서 원본 생성
- PRD, 구현 스펙, 아키텍처, 개발진행 히스토리, 완료보고서 인덱스 구성
- Outline 등록 후 문서 ID와 URL을 검증 보고서에 기록

## 04. 검색 키워드

- TXTDrop
- TXTDrop 프로젝트 위키
- TXTDrop PRD
- TXTDrop 구현 스펙
- TXTDrop 아키텍처
- TXTDrop 개발진행 히스토리
- TXTDrop 완료보고서 인덱스
- ollama_autostart
- ollama 새로고침
- PyInstaller onedir
- build.bat
- 첫 실행 데드락
- os._exit
