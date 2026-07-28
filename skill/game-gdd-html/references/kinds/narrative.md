# 세계관·스토리 기획서 kind

세계의 사실, 사건의 배열, 캐릭터의 정체성, 실제 발화문을 분리한다. 상위 문서가 정한 캐논을 하위 문서가 임의로 변경하지 않는다.

| 기획서 / kind ID / profile | 목적·주 독자 | 반드시 답할 결정 | 필수 산출물 | 기본 제외 | 인접 문서 핸드오프 | 완료 조건 |
|---|---|---|---|---|---|---|
| 세계관 기획서<br>`world-bible`<span id="world-bible"></span><br>`narrative` | 세계의 캐논·규칙·용어 기준 수립<br>내러티브·아트·레벨·콘텐츠 팀 | 역사·지역·종족·세력·자연·기술 규칙은 무엇이며 무엇이 불가능한가? | 시대·사건 연표, 지역·세력·종족, 세계 규칙, 용어집, 캐논 등급·금지선 | 메인 사건 순서, 개별 캐릭터 아크, 실제 대사, 게임 수치 | 입력: `game-concept`<br>출력: `scenario-design`, `character-bible`, `level-design` | 모든 고유명사와 세계 규칙이 단일 정의를 갖고 캐논 충돌이 없다 |
| 시나리오 기획서<br>`scenario-design`<span id="scenario-design"></span><br>`narrative` | 메인·서브 사건과 분기 구조 설계<br>내러티브·퀘스트·연출·레벨 기획자 | 사건의 원인·순서·갈등·전환·결말과 선택 결과는 무엇인가? | 막·에피소드 구조, 비트 시트, 장면 목록, 분기 그래프, 조건 플래그, 퀘스트·연출 연결 | 세계 백과 복제, 최종 대사, 퀘스트 판정·보상 수치 | 입력: `world-bible`, `character-bible`<br>출력: `dialogue-script`, `quest-system`, `dungeon-design` | 모든 장면에 목적·진입 조건·상태 변화·후속 장면이 있고 분기가 재합류 또는 종결된다 |
| 캐릭터 설정서<br>`character-bible`<span id="character-bible"></span><br>`narrative` | 캐릭터의 일관된 성격·관계·목표·목소리 정의<br>내러티브·아트·보이스·콘텐츠 팀 | 배경·욕망·결핍·관계·변화와 말투의 허용·금지 범위는 무엇인가? | 프로필, 동기·갈등, 관계도, 아크 비트, 외형 방향, 말투·어휘 가이드 | 전투 키트·능력치, 전체 장면 대사, 세계 공통 규칙 | 입력: `world-bible`, `game-concept`<br>출력: `scenario-design`, `dialogue-script`, `character-combat` | 주요 선택과 대사가 동기·관계·아크 단계로 설명되고 설정 모순이 없다 |
| 대사 스크립트<br>`dialogue-script`<span id="dialogue-script"></span><br>`narrative` | NPC·컷신·선택지·시스템 메시지의 실행 가능한 문안 제공<br>내러티브·연출·로컬라이즈·클라이언트 | 누가 어떤 조건에서 무엇을 말하며 선택·중단·재진입 뒤 어떤 줄로 이어지는가? | 대사 ID, 화자·조건·텍스트, 선택지·분기, 변수·성별·복수형 토큰, VO·연출 큐, 시스템 메시지 | 거시 스토리 변경, 세계 규칙 신설, 화면 레이아웃, 퀘스트 판정 | 입력: `scenario-design`, `character-bible`<br>출력: `quest-system`, `ui-spec`, `data-table-spec` | 모든 줄이 고유 ID·노출 조건·후속 상태를 가지며 변수와 분기가 로컬라이즈 가능하다 |

