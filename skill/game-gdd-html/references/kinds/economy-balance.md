# 경제·밸런스 기획서 kind

경제 흐름, 개별 보상, 성장 곡선, 확률, 판매 상품은 서로 다른 결정 소유권을 가진다. 값의 출처와 소비처를 ID로 연결하고 같은 수치를 여러 문서에서 소유하지 않는다.

| 기획서 / kind ID / profile | 목적·주 독자 | 반드시 답할 결정 | 필수 산출물 | 기본 제외 | 인접 문서 핸드오프 | 완료 조건 |
|---|---|---|---|---|---|---|
| 게임 경제 기획서<br>`game-economy`<span id="game-economy"></span><br>`economy` | 재화 전체 흐름과 건전성 설계<br>경제·라이브·서버·데이터 기획자 | 각 재화는 어디서 얼마나 생성·소비·교환되며 인플레이션과 축적을 어떻게 제어하는가? | 재화 정의, 소스·싱크 지도, 기간별 예산, 교환·한도 규칙, 유저군별 시나리오, 경제 지표 | 개별 보상 지급 조건, 상품 문안·노출, 확률 풀 | 입력: `master-gdd`<br>출력: `reward-design`, `store-product`, `progression-balance`, `logging-spec` | 기준 유저군별 기간 수지가 계산되고 무한 생성·무의미한 재화가 없다 |
| 보상 기획서<br>`reward-design`<span id="reward-design"></span><br>`economy` | 행동별 보상 권리·수량·전달 정의<br>경제·콘텐츠·서버·운영 기획자 | 누가 어떤 조건에서 무엇을 몇 번 받고 중복·만료·공간 부족 시 어떻게 되는가? | 보상 매트릭스, 산정식·구간, 최초·반복 규칙, 권리·수령 상태, 중복·오버플로 처리 | 상점 가격, 콘텐츠 진행 규칙, 확률 풀 내부 가중치 | 입력: `game-economy`, 각 콘텐츠 kind<br>출력: `data-table-spec`, `ui-spec`, `logging-spec`, `exception-spec` | 모든 보상 행에 출처·자격·수량·상한·전달·중복 판정이 있다 |
| 성장 밸런스 기획서<br>`progression-balance`<span id="progression-balance"></span><br>`balance` | 레벨·경험치·전투력 성장 속도 설계<br>밸런스·콘텐츠·경제·데이터 기획자 | 각 성장 축의 목표 도달 시간, 요구량, 증가량, 게이트와 따라잡기는 어떻게 설정하는가? | 성장 축 지도, XP·요구량·능력치 곡선, 구간별 페이싱 목표, 기준 플레이 시나리오, 민감도·시뮬레이션 | 성장 시스템 상태 규칙, 상점 가격, 개별 전투 계수 | 입력: `character-system`, `game-economy`<br>출력: `stage-design`, `reward-design`, `data-table-spec`, `logging-spec` | 기준·고관여·저관여 시나리오가 목표 기간과 파워 구간을 허용 오차 내 통과한다 |
| 확률형 시스템 기획서<br>`random-probability-system`<span id="random-probability-system"></span><br>`balance` | 추첨·드롭·천장·중복 확률의 검증 가능성 확보<br>밸런스·서버·법무·데이터·QA | 풀·가중치·보정·천장·중복·리셋·표시는 어떤 규칙이며 기대값은 얼마인가? | 확률·풀 표, 추첨·천장 상태도, 기대값·분산, 중복 변환, 공개 기준, RNG 감사·통계 검증안 | 상품 가격·패키지 구성, 획득 후 아이템 사용, UI 레이아웃 | 입력: `item-system`, `game-economy`<br>출력: `store-product`, `reward-design`, `data-table-spec`, `logging-spec` | 이론 확률·누적 보장·시뮬레이션 결과가 일치하고 모든 리셋 조건을 감사할 수 있다 |
| 상점·상품 기획서<br>`store-product`<span id="store-product"></span><br>`economy` | 판매 SKU·가격·구매·지급 계약 정의<br>사업·경제·서버·운영·UI 기획자 | 무엇을 누구에게 얼마에 몇 번 판매하며 결제·지급·환불 실패를 어떻게 처리하는가? | SKU 명세, 구성품·가격 매트릭스, 구매 자격·한도·기간, 지급 권리 상태, 환불·복구 규칙 | 경제 전체 수지, 프로모션 캠페인 메시지, 결제 화면 시각 디자인 | 입력: `game-economy`, `item-system`<br>출력: `product-promotion`, `ui-spec`, `logging-spec`, `exception-spec` | SKU마다 가격·구성·자격·한도·지급·환불·버전이 단일하게 식별된다 |

