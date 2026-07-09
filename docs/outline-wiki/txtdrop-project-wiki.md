# TXTDrop 프로젝트 위키

TXTDrop은 Windows 시스템 트레이에서 동작하는 클립보드 저장 유틸리티다. 전역 단축키로 텍스트와 이미지를 파일로 저장하고, 텍스트 저장 시 Ollama로 파일명용 짧은 제목을 생성할 수 있다. v0.7부터 선택 또는 클립보드 텍스트를 SVIL TTS로 낭독하는 단축키(Ctrl+Shift+X)와, 저장 기록의 중복 문서를 걸러 휴지통으로 옮기는 중복제거 기능을 제공한다. TTS 낭독은 서버가 꺼져 있으면 MCP `svil_tts_speak`과 동일한 경로로 자동 기동을 시도한다 (2026-07-10).

## 01. 빠른 링크

* [TXTDrop PRD](https://outline-production-20a7.up.railway.app/doc/txtdrop-prd-pwtU6kwoyS)
* [TXTDrop 구현 스펙](https://outline-production-20a7.up.railway.app/doc/txtdrop-20UwLKqRLO)
* [TXTDrop 아키텍처](https://outline-production-20a7.up.railway.app/doc/txtdrop-5Aw1vfH9ac)
* [TXTDrop 개발진행 히스토리](https://outline-production-20a7.up.railway.app/doc/txtdrop-CmhqoXv0Hy)
* [TXTDrop 완료보고서 인덱스](https://outline-production-20a7.up.railway.app/doc/txtdrop-KTmAjyPxs1)

## 02. 현재 기준

| 항목 | 내용 |
|------|------|
| 현재 버전 | v0.7 (TTS 자동 기동 개선, 2026-07-10) |
| 대상 플랫폼 | Windows |
| 실행 형태 | 시스템 트레이 상주 앱 |
| 저장 단축키 | `Ctrl+Shift+Z` — 클립보드를 파일로 저장 |
| 낭독 단축키 | `Ctrl+Shift+X` — 선택/클립보드 텍스트를 SVIL TTS로 낭독, 서버 미기동 시 자동 기동(최대 60초) |
| TTS 연동 | SVIL TTS 프록시 `http://127.0.0.1:8765` (`/api/tts/pipeline`), 자동 기동은 웹 백엔드 `http://127.0.0.1:3000` 경유 |
| 연계 앱 | TXTBrain — 저장 폴더의 `.txt`를 수집, 내용 해시로 중복 차단 |
| 저장소 문서 위치 | `C:\Projects\TXTDrop\docs` |
| 기준 명세 | `docs\기능명세.md` |
| 빌드 산출물 | `dist\TXTDrop\TXTDrop.exe` (onedir) |
| 설치 파일 | `Output\TXTDropSetup.exe` |

## 03. 문서 구조

### PRD

제품 목적, 사용자, 주요 기능 범위, 비범위, 성공 기준, 리스크를 정리한다.

### 구현 스펙

엔트리포인트, 설정/DB, 클립보드 저장, Ollama 연동, TTS 낭독(자동 기동 포함), 중복제거, 트레이/UI, 빌드/배포 규칙을 구현 기준으로 정리한다.

### 아키텍처

Tkinter 공유 루트, pystray 트레이, keyboard 전역 단축키, Pillow/pyperclip 클립보드 처리, SQLite 영속화, Ollama·SVIL TTS HTTP 연동(웹 백엔드 경유 자동 기동 포함), 중복제거(difflib) 구조를 설명한다.

### 개발진행 히스토리

버전별 마일스톤과 2026-07-08 TTS 낭독·중복제거 추가, 2026-07-09 TXTBrain 연계, 2026-07-10 TTS 자동 기동 개선까지 추적한다.

### 완료보고서 인덱스

빌드 검증, 안정화, TTS 낭독·자동 기동, 중복제거, TXTBrain 연계 등 완료 보고서의 위치와 검색 키워드를 관리한다.

## 04. 로컬 원본

* `docs\outline-wiki\*.md` — Outline 위키 원본 6종
* `docs\기능명세.md` — 현재 구현 기준 기능 명세
* `docs\reports\완료보고_20260708_TTS낭독단축키_ClaudeCode.md`
* `docs\reports\완료보고_20260708_중복문서제거_ClaudeCode.md`
* `docs\전체검토-및-개선제안-2026-07-05.md`

문서를 갱신할 때는 로컬 원본과 Outline 위키를 함께 반영한다.
