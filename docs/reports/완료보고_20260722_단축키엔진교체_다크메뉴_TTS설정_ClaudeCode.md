# 완료보고 — 단축키 엔진 교체 · 트레이 다크 메뉴 · TTS 낭독 설정 (v0.8.1 → v0.10.0)

- 작성: Claude Code / 2026-07-22
- 브랜치: `claude/tray-menu-dark-mode-shortcut-0be279` (base: master 56828e2)
- 커밋: 444892a(v0.8.1) → 3f195ce(v0.9.0) → 6b7ada7 → 826cd21(v0.10.0)
- 배포: v0.10.0 설치 완료 (`%LOCALAPPDATA%\Programs\TXTDrop`), 실행·로그 확인됨

## 1. v0.8.1 — 단축키 RegisterHotKey 전환 + 트레이 다크 메뉴 수정

### 단축키 안 먹던 원인과 해결
- 원인: `keyboard` 라이브러리의 저수준 훅(WH_KEYBOARD_LL)은 절전 복귀·시스템
  부하 시 Windows가 조용히 제거한다. 로그상 등록은 매번 성공하나 실행 중 죽음.
- 해결: 신규 `hotkeys.py` — Win32 `RegisterHotKey` + 스레드 메시지 루프
  (GetMessageW)만 사용. WNDPROC 콜백 없음(과거 PyInstaller 프로즌 런타임
  STATUS_STACK_BUFFER_OVERRUN 크래시 원인이라 의도적으로 배제).
- 조합 선점(1409) 시에만 keyboard 라이브러리로 폴백. 설정 저장 시 전체 재등록.
- 부수 효과: 단축키 입력이 대상 앱으로 전달되지 않음(Ctrl+Shift+Z가 브라우저
  '다시 실행'으로 새던 부작용 제거).

### 트레이 다크 메뉴 미적용 원인과 해결
- 원인: pystray는 `__init__`에서 `_message_handlers` 딕셔너리에 원본
  `_on_notify` 바운드 메서드를 저장하고 디스패처가 그 딕셔너리만 참조 —
  기존 `tray._on_notify` 몽키패치는 무효였음.
- 해결: 딕셔너리 항목(`_message_handlers[WM_NOTIFY]`)까지 교체 + 적용 로그.
  `tk_popup` 후 `grab_release()` 보강.

## 2. v0.9.0 — TTS 낭독 설정 (svil-tts-settings 표준)

- 설정 창 "낭독 (SVIL TTS)" 섹션: 엔진(자동/gptsovits/qwen3, 오프라인 표기),
  보이스(학습/샘플 표기), RVC(사용 안 함/자동/모델), 말 속도(0.7~1.5), ▶ 미리듣기.
- `tts_client`: `capabilities()`(status+voices+rvc/models 통합), `preview()`,
  `speak()`에 저장 설정 반영. 설정 키: `tts_engine/tts_voice/tts_speed/tts_use_rvc/tts_rvc_model`.
- keepSelected: 저장값이 목록에 없으면 `(사용 불가)`로 유지.
- **서버 계약 주의(스킬 문서와 다름, 소스 확인 완료)**:
  - `speed_pct`는 -50~+50 **오프셋**(0=보통). 100 기준으로 보내면 +50 클램프되어 1.5배속.
  - pipeline `use_rvc` 기본 **True** → "사용 안 함"은 명시적으로 false 전송 필요.
  - `/api/tts/status`는 엔진 3종 헬스체크 순회로 오프라인이 많으면 5초+ 소요 → 클라이언트 타임아웃 12s.
- 후속 수정(6b7ada7): RVC 힌트 라벨 늦은 pack으로 창 하단 잘림 → 생성 시 pack,
  캐퍼빌리티 로드 중 사용자가 바꾼 선택 보존.

## 3. v0.10.0 — Ollama 자동 시작(페일오버) 제거

- 시작 시 서버가 죽어 있어도 `ollama serve`를 자동 기동하지 않음(상태 로그만).
- 설정 체크박스·`ollama_autostart` 키 제거. 트레이 "Ollama 새로고침" 수동 기동은 유지.
- 배경: GPU를 TTS·영상 파이프라인과 공유하는 환경에서 앱 실행마다 ollama가
  VRAM 선점. 실제로 고아 `llama-server.exe`가 3.9GB VRAM을 물고 있던 사례 확인·정리함.

## 4. 검증 내역 (실측)

- hotkeys 단위: 등록→발동(SendInput)→재등록→해제 통과.
- 앱 E2E: 테스트 단축키로 클립보드 텍스트 실제 파일 저장, 다크 메뉴 패치 로그 확인.
- TTS 실서버: pipeline에 `voice_name`/`speed_pct`/`use_rvc` 전송 → 합성 성공,
  RVC 오프라인 시 원본 폴백(`rvc_applied:false`) 확인.
- 설정 UI 자동 테스트: 콤보 채움·오프라인 표기·저장 라운드트립(온라인/오프라인 분기) 통과.
- v0.10.0: Ollama 꺼진 상태에서 자동 기동 없음 + 프로세스 미생성 확인.
- 설치본: v0.10.0 사일런트 설치 후 실행 로그로 신엔진·다크메뉴 적용 확인.

## 5. 남은 과제

- `ollama_client.resolve_model`의 모델 폴백이 임베딩 전용 모델(nomic-embed-text)을
  선택해 제목 생성이 Bad Request로 실패하는 버그 — 별도 작업 칩 등록됨(미해결).
  파일명은 클립보드 첫 줄 폴백으로 동작 중이라 저장 자체는 정상.
- 사일런트 재설치 시 트레이 앱이 창이 없어 CloseApplications로 안 닫힘 —
  재설치 전 프로세스 수동 종료 필요(이번에 확인된 운영 메모).
