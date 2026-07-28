# 변경 이력

이 프로젝트의 주요 변경 사항을 기록합니다.

형식은 [Keep a Changelog](https://keepachangelog.com/ko/1.1.0/)를 참고하며, 버전은 [Semantic Versioning](https://semver.org/)을 따릅니다.

## [Unreleased]

### Added

- MIT 라이선스
- 기여 가이드와 릴리스 정책
- 행동강령과 보안 정책
- Bug Report, Feature Request와 Document Kind Request 이슈 양식
- Pull Request 템플릿
- Python 3.10·3.12·3.14 자동 테스트 워크플로
- 저장소 내부에서 실행 가능한 SKILL.md 검증기
- 공통 줄바꿈·인코딩·에디터 규칙

### Changed

- 설치 가능한 스킬을 `skill/game-gdd-html/`로 분리
- 회귀 테스트, 유지보수 도구와 GitHub 커뮤니티 문서를 스킬 외부로 이동
- README 설치 절차를 단일 스킬 폴더 기준으로 변경
- 단독 복사한 스킬에도 MIT 조건이 보존되도록 라이선스 포함

## [0.1.0] - 2026-07-28

### Added

- 자연어와 GDDQL 기반 게임 기획 요청 해석
- 9개 카테고리의 41개 세부 document kind
- 12개 넓은 document profile
- kind 기본 facet, 요청 facet과 의존 section을 조합하는 범위 필터
- 복수 document kind의 독립 HTML 출력 계획
- 기획 권한과 구현 결정의 명시적 경계
- 실무 게임 기획서 문체와 내부 파이프라인 비노출 규칙
- 구조화 JSON 기반 단일 HTML 렌더러
- Mermaid와 Chart.js를 지원하는 반응형 HTML 템플릿
- profile, kind, scope와 canonical section 자동 검증
- 자연어 해석, kind 라우팅과 profile 렌더 회귀 테스트
- 설치·사용·GDDQL·CLI·저장소 구조를 포함한 상세 README

[Unreleased]: https://github.com/yang-yun-seok/game-gdd-html/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/yang-yun-seok/game-gdd-html/releases/tag/v0.1.0
