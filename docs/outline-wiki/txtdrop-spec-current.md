# TXTDrop 구현 스펙

기준 문서: 기능명세.md / 작성자: Claude Code / 작성일: 2026-07-10 / 기준 버전: v0.7

## 01. 버전 관리

* 기준 앱 버전은 v0.7이다 (v0.6.1 실행 안정화 → v0.7 onedir/WNDPROC → TTS 낭독·중복제거 추가 → TTS 자동 기동 개선).
* 현재 구현 명세는 `docs\기능명세.md`를 기준으로 한다.
* 빌드 산출물은 PyInstaller **onedir** 구조인 `dist\TXTDrop\TXTDrop.exe`다.
* 설치 파일은 Inno Setup `Output\TXTDropSetup.exe`다.

## 02. 라우팅 / 진입점

* 진입점은 `main.py`의 `main()`이다.
* `config.init_db()`로 SQLite DB를 준비한다.
* `tk_root.init()`으로 숨겨진 Tk root를 만든다. 모든 UI 창은 `Toplevel`로 연다.
* pystray는 `tray.run_detached()`로 실행하고, Tk `mainloop()`는 **OS 메인 스레드**에서 실행한다.
* 첫 실행 폴더 선택은 `mainloop()` 시작 전 메인 스레드에서 `messagebox`/`filedialog`를 직접 호출한다.
* 앱 종료 시 `os._exit(0)`으로 프로세스를 즉시 종료한다.

## 03. 세션과 인증

이 앱은 사용자 계정 세션이나 원격 인증을 사용하지 않는다. 설정, 로그, 저장 이력은 로컬 SQLite DB에 저장한다.

## 04. 데이터 모델

SQLite DB `txtdrop.db`는 실행 파일 기준 경로에 위치한다.

| 테이블 | 역할 |
|--------|------|
| `config` | 설정 key-value |
| `history` | 저장 시각, 유형, 파일명, 전체 경로 |
| `trash` | 중복제거 시 `history`에서 이동된 기록 (사유·이동시각 포함, 복구 가능) |
| `log` | 실행 로그 |

기본 설정에는 저장 폴더, 파일명 접두사, 사운드, 저장 단축키(`hotkey`), 낭독 단축키(`tts_hotkey`), 언어, Ollama 모델·자동 시작, 중복제거 자동 검사(`dedup_auto`)·유사도 기준(`dedup_threshold`)이 포함된다.

## 05. 주요 훅 / 서비스

| 모듈 | 역할 |
|------|------|
| `main.py` | 단축키 등록, 클립보드 저장, TTS 낭독, 트레이 메뉴, Ollama 시작/새로고침 |
| `config.py` | SQLite 설정/로그/히스토리/휴지통/백업/복원, 메모리 캐시 |
| `ollama_client.py` | Ollama 상태 확인, 모델 목록, 제목 생성, 상태 캐시 |
| `tts_client.py` | SVIL TTS 프록시(:8765) 호출, 자동 기동(:3000 웹 백엔드), 음성 친화 전처리, 2000자 상한 |
| `dedup.py` | 저장 기록 중복 검사 (SHA-256 완전 동일 + difflib 유사도) |
| `dedup_window.py` | 중복제거 창 — 전체 스캔, 유사도 기준, 휴지통 복구 |
| `settings_window.py` | 설정 UI, Ollama 실시간 상태 표시 |
| `log_window.py` | 로그/저장 이력 UI, 5초 자동 새로고침 |
| `notify.py` | Tk 기반 토스트 (Windows work area 기준 위치) |
| `tk_root.py` | 공유 Tk root, `call_on_main()` |
| `sound.py` | 저장 성공 효과음 (`winsound.Beep` + 폴백) |
| `i18n.py` | 한국어/English 문자열 |

## 06. 클립보드 저장 / 파일명

* 이미지 우선, 텍스트 후순위로 저장한다.
* 텍스트 파일명: Ollama 실행 중이면 AI 제목, 아니면 **클립보드 첫 줄** 기반 제목, 최종 폴백은 타임스탬프.
* 이미지 파일명: `{prefix}_{YYYYMMDD_HHMMSS}.png`
* 텍스트 저장 직후 백그라운드에서 중복 검사를 수행한다 (09 참조).

## 07. Ollama 연동

* 기본 주소: `http://localhost:11434`
* 시작 시: 서버 상태 확인 → 미실행 + `ollama_autostart=true`이면 `ollama serve` **무음** 시도 (토스트 없음)
* 트레이 "Ollama 새로고침": 실시간 확인 → 미실행이면 시작 시도 → 미설치 시 설치 안내 토스트
* 설정 창: `is_running()` 실시간 확인 (캐시 미사용), 결과를 공유 캐시에 반영
* 제목 생성 타임아웃: 20초

## 08. TTS 낭독 (Ctrl+Shift+X)

* 낭독 단축키(기본 `Ctrl+Shift+X`)로 **선택 텍스트**(없으면 클립보드)를 SVIL TTS로 낭독한다.
* 선택 텍스트는 보조키를 뗀 뒤 Ctrl+C로 자동 복사하고, 낭독 후 클립보드를 원래대로 되돌린다.
* `POST http://127.0.0.1:8765/api/tts/pipeline` (`category: narration`, `play_async: true`), 2000자 상한, URL·코드블록·마크다운 기호 제거 전처리.
* **자동 기동 (2026-07-10)**: TTS 프록시가 꺼져 있으면 SVIL 웹 백엔드 `http://127.0.0.1:3000/api/local-server`(`action:start, id:tts`)로 기동을 요청하고, 최대 60초 헬스체크(`/health`) 폴링 후 낭독을 이어간다. MCP `svil_tts_speak`이 쓰는 것과 동일한 자동 기동 경로다. 대기 중에는 "TTS 서버 시작 중" 토스트를 표시한다.
* 자동 기동 요청 자체가 거부되거나 60초 내 응답이 없으면 오류 토스트를 띄우고 `tts` 카테고리 로그를 남긴다.

## 09. 중복제거 (trash)

* `dedup_auto=true`이면 텍스트 저장 직후 백그라운드에서 기존 저장 기록과 비교한다 (저장 자체는 지연 없음).
* 완전 동일(SHA-256 정규화 해시) 또는 유사도 기준(기본 90%, `difflib`) 이상이면 해당 `history` row를 `trash`로 이동한다. **파일 자체는 건드리지 않는다.**
* 트레이 "중복제거" 창: 전체 스캔 실행, 유사도 기준(70~100) 조정, 휴지통 목록·복구.
* 연계: TXTBrain은 저장 폴더의 `.txt` 수집 시 내용 해시로 중복을 자동 차단한다 (TXTBrain v1.7.0).

## 10. 알림 / 백그라운드 작업

* 저장 성공/실패, Ollama 상태, TTS 결과(생성 중/서버 시작 중), 중복 정리는 커스텀 토스트로 표시한다 (5초, work area 기준 위치).
* Ollama 상태 확인·제목 생성, TTS 호출·자동 기동, 중복 검사는 모두 백그라운드 스레드에서 수행한다.
* 저장 성공 시 `sound_enabled=true`이면 `winsound.Beep`를 사용한다.

## 11. 주요 화면 스펙

* 트레이 우클릭 메뉴: 환경설정, 로그 기록, 중복제거, Ollama 새로고침, 종료
* 설정 창: 저장 폴더, 파일명 접두사, 저장/낭독 단축키, Ollama, 중복제거, 사운드, 언어, DB 백업/복원
* 로그 창: 로그 탭(5초 자동 새로고침)과 저장 기록 탭
* 중복제거 창: 실행 버튼, 유사도 기준, 휴지통 목록·복구

## 12. 접근성 / 테마

* 앱 UI는 다크 테마를 기본으로 한다.
* 토스트는 작업 표시줄을 침범하지 않도록 Windows work area 기준으로 위치를 잡는다.
* 단축키 캡처는 보조키 없는 단일 키 입력을 허용하지 않는다.

## 13. 알려진 제약

* 절전/복귀 WNDPROC 핸들러는 PyInstaller frozen 런타임 크래시 방지를 위해 **비활성화(no-op)** 상태다.
* `keyboard` 전역 훅은 Windows 권한/보안 소프트웨어 상태에 영향을 받을 수 있다.
* 단축키 등록 실패 시 기본값(`ctrl+shift+z` / `ctrl+shift+x`)으로 재시도한다.
* TTS 낭독은 자동 기동을 시도하지만, SVIL 웹 백엔드(:3000)까지 함께 꺼져 있거나 60초 내 기동되지 않으면 여전히 실패한다.
* 중복제거는 완전 동일/유사(difflib)만 대상이며, 의미 유사도(임베딩)는 다루지 않는다.

## 14. 검증

* 2026-07-10: TTS 자동 기동 모킹 테스트 4종(이미 켜짐/자동기동 성공/타임아웃/기동요청 실패) + 실서버 `/api/local-server` 호출 형식 검증 + 재빌드 후 실제 단축키 E2E 통과
* 2026-07-08: TTS 낭독 실서버 E2E (음성 생성·재생 큐 등록 확인), 중복제거 로직 테스트 통과
* 2026-07-06: `compileall` 통과, PyInstaller onedir 빌드·Inno Setup 설치 파일 생성, 첫 실행 데드락 수정 확인
* 2026-07-06: Ollama 제목 생성 및 클립보드 첫 줄 폴백 동작 확인

세부 완료 내역은 완료보고서 인덱스와 `docs\reports\`를 참조한다.
