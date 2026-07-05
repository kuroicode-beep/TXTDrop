# TXTDrop 프로젝트 위키

TXTDrop은 Windows 시스템 트레이에서 동작하는 클립보드 저장 유틸리티다. 전역 단축키로 텍스트와 이미지를 파일로 저장하며, 텍스트 저장 시 Ollama를 이용해 파일명용 짧은 제목을 생성할 수 있다.

## 01. 빠른 링크

- [TXTDrop PRD](https://outline-production-20a7.up.railway.app/doc/txtdrop-prd-pwtU6kwoyS)
- [TXTDrop 구현 스펙](https://outline-production-20a7.up.railway.app/doc/txtdrop-20UwLKqRLO)
- [TXTDrop 아키텍처](https://outline-production-20a7.up.railway.app/doc/txtdrop-5Aw1vfH9ac)
- [TXTDrop 개발진행 히스토리](https://outline-production-20a7.up.railway.app/doc/txtdrop-CmhqoXv0Hy)
- [TXTDrop 완료보고서 인덱스](https://outline-production-20a7.up.railway.app/doc/txtdrop-KTmAjyPxs1)

## 02. 현재 기준

| 항목 | 내용 |
|------|------|
| 현재 버전 | v0.6.1 |
| 대상 플랫폼 | Windows |
| 실행 형태 | 시스템 트레이 상주 앱 |
| 저장소 문서 위치 | `C:\Projects\TXTDrop\docs` |
| 기준 명세 | `docs\기능명세.md` |
| 빌드 산출물 | `dist\TXTDrop\TXTDrop.exe` (onedir) |
| 설치 파일 | `Output\TXTDropSetup.exe` |
| 보고서 기록 원칙 | 작업 검증 결과는 `docs\codex-verification-*.md`에 기록 |

## 03. 문서 구조

### PRD

제품 목적, 사용자, 주요 기능 범위, 비범위, 성공 기준, 리스크를 정리한다.

### 구현 스펙

엔트리포인트, 설정/DB, 클립보드 저장, Ollama 연동, 트레이/UI, 빌드/배포 규칙을 구현 기준으로 정리한다.

### 아키텍처

Tkinter 공유 루트, pystray 트레이, keyboard 전역 단축키, Pillow/pyperclip 클립보드 처리, SQLite 영속화, Ollama HTTP API 연동 구조를 설명한다.

### 개발진행 히스토리

v0.6.1 기준 기능과 버전별 마일스톤, 2026-06-28 점검/수정 내용을 추적한다.

### 완료보고서 인덱스

빌드 검증, 자동 시작 설정 수정, Outline 위키 구축 같은 완료 보고서의 위치와 검색 키워드를 관리한다.

## 04. 로컬 원본

- `docs\outline-wiki\txtdrop-project-wiki.md`
- `docs\outline-wiki\txtdrop-prd-current.md`
- `docs\outline-wiki\txtdrop-spec-current.md`
- `docs\outline-wiki\txtdrop-architecture.md`
- `docs\outline-wiki\txtdrop-development-history.md`
- `docs\outline-wiki\txtdrop-completion-report-index.md`
- `docs\기능명세.md`
- `docs\전체검토-및-개선제안-2026-07-05.md`
