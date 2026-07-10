# 검증보고 — 전체 검증 (TXTDrop + TXTBrain + 연계 서비스)

- 일자: 2026-07-10
- 작업자: Claude Code
- 범위: 이번 이터레이션에서 작업한 전 항목 (TTS 낭독·자동 기동, 중복제거, AI 기억 캡처, TXTBrain v1.7.0, 배포·문서)

## A. 저장소 상태 — 통과

| 저장소 | 브랜치 | 상태 |
|--------|--------|------|
| TXTDrop | master (`cfc8e28`) | clean, origin 동기화 |
| TXTBrain | main (`f63713e`) | clean, origin 동기화 |

## B. 소스 품질 — 통과

- TXTDrop 전 모듈(14개) `compileall` 통과
- TXTDrop 모킹 테스트 3종 재실행(master 소스 기준): dedup / TTS 자동기동 4시나리오 / memory_client — 전부 통과
- TXTBrain 전체 테스트 30개 통과, 인입 내용중복 E2E(임시 DB) 통과

## C. 배포 상태 — 통과

- 설치본(`AppData\Local\Programs\TXTDrop`) = dist 빌드 **1,005개 파일 완전 일치** (0 mismatch)
- 시작프로그램 Run 키 정상 (설치 경로 exe)
- 설정 기본 상태 확인: `memory_enabled=false`(옵트인 유지), 저장/낭독 단축키 기본값
- TXTBrain `dist\TXTBrain.exe`(07-09 19:43) + 바탕화면 바로가기 타깃 일치

## D. 런타임 E2E — 통과 (회귀 1건 발견·수정)

- **발견 1 — TXTDrop 프로세스 다운**: 새벽 4:09 시작 후 어느 시점에 종료됨. 정상 종료 로그 없음 + Windows WER 크래시 기록 없음 → 앱 결함이 아닌 외부 강제 종료로 판단. 재시작 후 정상 (저장/낭독 단축키 등록, AI 기억은 비활성이라 미등록 — 의도대로).
- **자동 중복제거 실동작 최초 검증**: 같은 클립보드로 `Ctrl+Shift+Z` 2회 → 1차는 history 유지, 2차는 저장 직후 "100% 유사" 판정으로 trash 이동. 테스트 파일·행은 검증 후 정리.
- **발견 2 — TTS RVC 폴백 회귀 (svil-ai-work)**: RVC 서버(:7865)가 꺼진 상태에서 낭독 시 502 실패. 원인은 `tts_core.py` 통합(bd22dc9) 때 "RVC 실패 시 원본 폴백" 정책(b25545a)이 유실된 것. TXTDrop 낭독과 MCP `svil_tts_speak` 공통 영향. **수정·커밋·푸시(`784c483`)**, TTS 서비스 재시작 후 재검증 → RVC 꺼진 상태에서도 원본 목소리로 낭독 성공 (7.19초 생성·재생).

## E. 연계 서비스·데이터 — 통과

- 서비스 헬스 4종 모두 200: TTS(:8765), 웹 백엔드(:3000), TXTAIMemory(:47530), Ollama(:11434)
- TXTBrain DB: documents 557 = FTS 557 (동기화 유지), 정리 전 백업 파일 존재
- TXTAIMemory 원장의 검증용 테스트 조각 2건 `/forget`으로 제거 (잔여 0)

## 남은 항목 (비차단)

- `main.py` 시작 로그가 "TXTDrop v0.6 시작됨"으로 하드코딩 — 앱 버전 규칙(APP_VERSION/VERSION_HISTORY 상수, 히스토리 메뉴) 미적용 상태. 다음 정비 때 적용 권장.
- RVC 서비스(:7865)는 현재 꺼져 있음 — 낭독은 폴백으로 동작하나, 청취 확정 음색(RVC 후처리)을 쓰려면 트레이에서 RVC를 켜야 함.
- TTS 자동 기동은 웹 백엔드(:3000)까지 꺼진 상태를 커버하지 못함 (기존 문서화된 제약).
