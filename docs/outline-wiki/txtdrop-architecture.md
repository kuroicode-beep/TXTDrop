# TXTDrop 아키텍처

작성일: 2026-07-06
기준 버전: v0.6.1

## 01. 개요

TXTDrop은 단일 Windows 데스크톱 프로세스 안에서 트레이, 전역 단축키, Tkinter UI, SQLite 저장소, Ollama HTTP API를 연결한다. 원격 백엔드는 없으며, Ollama는 로컬 서버 `http://localhost:11434`를 사용한다.

## 02. 구성도

```mermaid
flowchart TD
  User["사용자"] --> Hotkey["전역 단축키<br/>keyboard"]
  User --> Tray["시스템 트레이<br/>pystray run_detached"]
  Hotkey --> Drop["drop_clipboard()<br/>daemon thread"]
  Tray --> Settings["설정 창<br/>Tk Toplevel"]
  Tray --> LogWindow["로그/이력 창<br/>Tk Toplevel"]
  Tray --> OllamaRefresh["_do_ollama_refresh()"]
  Drop --> ImageGrab["ImageGrab.grabclipboard()"]
  Drop --> TextGrab["pyperclip.paste()"]
  Drop --> FileSystem["저장 폴더<br/>txt/png"]
  Drop --> Config["SQLite txtdrop.db"]
  Drop --> Ollama["Ollama API<br/>localhost:11434"]
  Drop --> Toast["커스텀 토스트<br/>Tk Toplevel"]
  Settings --> Config
  LogWindow --> Config
  OllamaRefresh --> Ollama
  MainThread["메인 스레드<br/>tk.mainloop()"] --> Toast
  MainThread --> Settings
  MainThread --> LogWindow
```

## 03. 스레드 모델

| 스레드 | 역할 |
|--------|------|
| OS 메인 스레드 | `tk.Tk().mainloop()` — 모든 Tk UI 이벤트 처리 |
| pystray 백그라운드 | `tray.run_detached()` — 트레이 아이콘/알림 |
| keyboard 내부 | 전역 단축키 훅 (논데몬 스레드 포함) |
| daemon threads | `drop_clipboard`, Ollama 확인/제목 생성, 사운드 |

**핵심 규칙:** Tkinter `mainloop()`는 반드시 OS 메인 스레드에서 실행한다. UI 작업은 `tk_root.call_on_main()`으로 스케줄링한다.

## 04. 프론트엔드

- UI 프레임워크는 Tkinter다.
- `tk_root.py`가 숨겨진 공유 root를 만든다.
- `settings_window.py`, `log_window.py`, `notify.py`는 모두 `Toplevel`을 사용한다.
- 트레이 메뉴는 pystray의 Windows 알림 핸들러를 패치해 다크 메뉴를 띄우고, 실패 시 기본 메뉴로 폴백한다.
- 토스트는 Windows `SPI_GETWORKAREA` API로 작업 표시줄 위에 위치한다.

## 05. 백엔드 / API

- 앱 자체 백엔드는 없다.
- Ollama 연동은 `urllib.request`로 `/api/tags`, `/api/generate`를 호출한다.
- 서버 상태 캐시는 10초 TTL로 관리한다. 설정 창에서는 `is_running()` 실시간 확인.

## 06. 데이터 저장소

- SQLite DB는 `txtdrop.db`다.
- PyInstaller 실행 시 실행 파일 폴더, 소스 실행 시 프로젝트 폴더에 위치한다.
- 설정값은 메모리 캐시(`_cache`)로 읽기 성능을 최적화한다.
- 로그는 시작 시 30일 초과 항목을 정리한다.

## 07. 인증 / 권한

- 앱 내부 인증은 없다.
- 전역 단축키 등록은 Windows 훅 권한과 환경에 영향을 받는다.
- 저장 폴더는 사용자가 선택한 로컬 경로를 사용한다.

## 08. 배포 / 운영

- PyInstaller spec은 **onedir** 구조를 사용한다 (`dist\TXTDrop\`).
- `build.bat`은 아이콘 생성, PyInstaller 빌드, Inno Setup 설치 파일 생성을 순서대로 실행한다.
- Inno Setup: `CloseApplications=yes`로 설치 시 실행 중 프로세스 자동 종료 시도.
- 앱 종료: `os._exit(0)` — `keyboard` 논데몬 스레드 포함 즉시 프로세스 종료.

## 09. 알려진 제약

- 절전/복귀 `WM_POWERBROADCAST` WNDPROC 패치는 PyInstaller frozen 런타임에서 `STATUS_STACK_BUFFER_OVERRUN` 크래시를 유발하여 **의도적으로 비활성화**했다.
- 첫 실행 폴더 선택은 `mainloop()` 전 메인 스레드에서 직접 Tk 다이얼로그를 호출한다 (`call_on_main` + `event.wait()` 데드락 방지).

## 10. 보안 / 접근성

- 파일명은 Windows 금지 문자를 제거한다.
- DB 백업/복원은 사용자 선택 파일/폴더에 대해서만 수행한다.
- 토스트와 UI는 다크 테마 고대비에 가까운 색상을 사용한다.
