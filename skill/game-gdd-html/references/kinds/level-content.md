# 레벨·콘텐츠 기획서 kind

공간 구조는 `level-design`, 개별 런·스테이지는 전용 kind, 반복 가능한 플레이 규칙은 `content-design`, 학습 순서는 `tutorial-design`이 소유한다.

| 기획서 / kind ID / profile | 목적·주 독자 | 반드시 답할 결정 | 필수 산출물 | 기본 제외 | 인접 문서 핸드오프 | 완료 조건 |
|---|---|---|---|---|---|---|
| 레벨 디자인 기획서<br>`level-design`<span id="level-design"></span><br>`level` | 공간·동선·리듬의 공통 원칙 정의<br>레벨·환경·전투·테크 아트 | 경로·시야·게이트·전투·휴식 구간은 어떤 경험 곡선을 만드는가? | 블록아웃, 주요·대체 경로, 공간 메트릭, 구간별 페이싱, 랜드마크·가독성 원칙 | 개별 던전 규칙, 최종 아트, 적 수치·보상량 | 입력: `game-concept`<br>출력: `dungeon-design`, `stage-design`, `tutorial-design`, `monster-boss` | 기준 캐릭터로 모든 필수 경로가 통과 가능하고 길찾기·페이싱 가설을 플레이테스트할 수 있다 |
| 던전 기획서<br>`dungeon-design`<span id="dungeon-design"></span><br>`level` | 한 던전 런의 방·기믹·전투·보상 흐름 설계<br>레벨·전투·콘텐츠·QA | 입장부터 종료까지 방 순서, 기믹, 실패·재시도, 보상 주기는 어떻게 이어지는가? | 런 플로, 방·조우 표, 기믹 상태도, 몬스터·보스 배치, 체크포인트·리셋 규칙, 보상 훅 | 공통 공간 규격, 적 AI 상세, 보상 최종 값, 서사 대사 | 입력: `level-design`, `monster-boss`<br>출력: `reward-design`, `stage-design`, `scenario-design`, `logging-spec` | 정상·실패·이탈·재접속 경로마다 진행 상태와 종료 결과가 정의된다 |
| 스테이지 기획서<br>`stage-design`<span id="stage-design"></span><br>`level` | 스테이지 단위 목표·제약·난이도 정의<br>레벨·콘텐츠·전투·QA 기획 및 개발 협업 담당 | 목표, 제한 조건, 웨이브·스폰, 클리어·실패와 난이도 태그는 무엇인가? | 스테이지 시트, 목표·조건 표, 웨이브·스폰 타임라인, 배치도, 클리어·실패 QA 사례 | 월드 전체 동선, 전역 전투 규칙, 성장 곡선, 데이터 표현·구성 구현 방식 | 입력: `level-design`, `combat-balance`<br>출력: `reward-design`, `progression-balance`, `logging-spec` | 스테이지 시트의 목표·제약·진행·종료 규칙만으로 QA가 모든 결과를 판정할 수 있고 데이터 표현과 구성 방식은 개발 협의로 남는다 |
| 콘텐츠 기획서<br>`content-design`<span id="content-design"></span><br>`content` | 레이드·PvP·길드·미니게임 등 독립 콘텐츠의 플레이 계약 정의<br>콘텐츠·서버·전투·운영·UI | 누가 언제 입장해 무엇을 반복하며 어떤 상태로 종료·초기화되는가? | 콘텐츠 루프, 참여·매칭·진행·종료 규칙, 주기·리셋, 의존 시스템, 보상 인터페이스, 운영 슬롯 | 공유 시스템 상세, 정확한 보상량, 화면 배치, 시즌 달력 | 입력: `game-concept` 및 필요한 시스템 kind<br>출력: `ui-spec`, `reward-design`, `event-plan`, `logging-spec` | 입장부터 정산까지 상태가 닫혀 있고 공유 시스템과의 소유권 충돌이 없다 |
| 튜토리얼 기획서<br>`tutorial-design`<span id="tutorial-design"></span><br>`content` | 신규 유저의 학습 순서와 검증 설계<br>UX·레벨·콘텐츠·데이터·QA | 무엇을 언제 보여주고 직접 수행시키며 실패·스킵·재진입을 어떻게 처리하는가? | 학습 목표·순서, 단계 트리거, 안내 문구 자리표시자, 연습 구간, 스킵·재학습 규칙, 성공 지표 | 최종 UI 아트, 전체 난이도 곡선, 로컬라이즈 최종 문안 | 입력: `control-scheme`, `ux-flow`, 대상 시스템 kind<br>출력: `ui-spec`, `stage-design`, `logging-spec` | 각 단계가 관찰 가능한 행동으로 완료되며 막힘·스킵 후 복구 경로가 있다 |

