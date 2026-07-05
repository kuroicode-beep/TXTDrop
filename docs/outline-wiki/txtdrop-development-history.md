# TXTDrop 개발진행 히스토리

## 01. 요약

TXTDrop은 v0.6.1 기준으로 Windows 트레이 상주, 전역 단축키 클립보드 저장, Ollama 제목 생성, 설정/로그/히스토리 UI, PyInstaller onedir/Inno Setup 배포 흐름을 갖춘 상태다.

## 02. 주요 마일스톤

### v0.6.1 (2026-07-06) — 실행 안정화

- **첫 실행 데드락 수정**: `_first_run()`에서 `call_on_main` + `event.wait()` 제거 → `mainloop()` 전 메인 스레드에서 직접 `messagebox`/`filedialog` 호출
- **단축키 등록 예외 처리**: `keyboard.add_hotkey()` 실패 시 기본값 `ctrl+shift+z`로 재시도, 설정 변경 시에도 try/except
- **절전 핸들러 비활성화**: PyInstaller frozen 런타임 `STATUS_STACK_BUFFER_OVERRUN` 크래시 방지를 위해 WNDPROC 패치를 no-op으로 전환

### v0.6 (2026-07-05) — 기능 확장

- 트레이 메뉴 **"Ollama 새로고침"** 추가 — 상태 확인, 미실행 시 시작, 미설치 시 안내 토스트
- Ollama 미연결 시 파일명 폴백: **클립보드 첫 줄** 기반 제목
- 시작 시 Ollama 자동 시작: `ollama_autostart=true`일 때만 무음 시도 (에러 토스트 없음)
- `os._exit(0)` 종료 — `keyboard` 논데몬 스레드 즉시 종료
- 설정 창 Ollama 상태: `is_running()` 실시간 확인 (stale 캐시 문제 수정)
- Inno Setup `CloseApplications=yes` — 설치 시 실행 중 프로세스 자동 종료

### v0.4 ~ v0.5 — 안정화 이터레이션

- Tkinter `mainloop()` 메인 스레드 이관 (`tray.run_detached()` + `mainloop()`)
- 토스트 work area 기준 위치, 스택, 5초 표시
- Ollama 상태 캐싱, 제목 생성 로깅, 20초 타임아웃
- 설정/로그 창 singleton 재생성 버그 수정
- 다크 트레이 메뉴, 다크 설치 마법사

### v0.2 ~ v0.3 — AI/설정/로그

- Ollama AI 제목 생성, SQLite 마이그레이션
- 설정 창, 로그/저장 이력 창, 토스트 알림
- DB 백업/복원, 단축키 캡처, i18n (한국어/English)

### v0.1 — 초기 완성

- 클립보드 텍스트/이미지 저장, 트레이, 전역 단축키
- PyInstaller + Inno Setup 빌드 파이프라인

## 03. 2026-06-28 점검 및 수정

- Python 컴파일 검증 통과
- 의존성 import 검증 통과
- SQLite 스모크 테스트 통과
- `ollama_autostart=false`일 때 시작 시 Ollama 자동 실행 미시도 확인
- PyInstaller onedir 빌드 성공, read-only 속성 해제 `build.bat` 보강
- Outline 프로젝트 위키 구축

## 04. 현재 운영 상태

| 항목 | 값 |
|------|-----|
| 소스 실행 | `py -3.12 main.py` |
| 빌드 | `build.bat` |
| 실행 파일 | `dist\TXTDrop\TXTDrop.exe` (onedir) |
| 설치 파일 | `Output\TXTDropSetup.exe` |
| 기준 명세 | `docs\기능명세.md` |

## 05. 남은 확인 포인트

- 실제 설치본에서 단축키 등록 권한과 트레이 메뉴 동작 확인
- Ollama 미설치/오프라인 상태별 UI 메시지 재확인
- 절전/복귀 후 단축키 지속성 (WNDPROC 핸들러 비활성화 상태)
- SQLite 다중 스레드 동시 쓰기 안정성 (`docs\전체검토-및-개선제안-2026-07-05.md` C1 참조)

## 06. 관련 문서

- `docs\기능명세.md` — 현재 구현 기준 기능 명세
- `docs\전체검토-및-개선제안-2026-07-05.md` — 코드 검토 및 개선 제안
- `docs\outline-wiki\` — Outline 위키 원본
