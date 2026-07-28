# Live Operations (`live-ops`)

라이브 이벤트의 준비부터 종료·회고까지 운영 생명주기와 대응 절차를 정의한다.

## 표준 구조

| 순서 | ID | 섹션 | 최소 완료 조건 |
|---|---|---|---|
| 01 | `live-objectives` | 운영 목표와 원칙 | 대상 KPI, 플레이어 가치, 피로도·공정성 경계 |
| 02 | `calendar` | 운영 캘린더 | 준비·공지·오픈·종료·정산·회고 일정 |
| 03 | `event-design` | 이벤트 루프와 규칙 | 진입, 참여, 완료, 반복, 종료 흐름 |
| 04 | `live-rewards` | 보상과 경제 영향 | 보상 풀, 한도, 소급, 경제 검토 |
| 05 | `segmentation` | 대상과 노출 | 자격, 지역·플랫폼·코호트, 빈도 제한 |
| 06 | `operations` | 운영 절차와 책임 | 적용 요청, 승인 주체, 공개·중단 시점, CS 대응, 접근 책임, 점검·수용 조건 |
| 07 | `live-telemetry` | 지표와 알람 | 퍼널, 이벤트, 대시보드, 임계값, 담당 |
| 08 | `contingency` | 장애·오류·복구 | 중단, 연장, 보상, 사용자 상태 복구 기준, 커뮤니케이션 |

## 자동 범위 조합

`allowed_ids` 전체를 항상 작성하지 않는다. 아래 `core_ids`에 요청에서 감지된 facet의 섹션과 그 dependency만 더해 `core + triggered + dependency` 범위로 작성한다. 사용자가 이 프로필의 allowed section ID를 직접 지정하면 해당 섹션을 명시적으로 추가한다.

- `core_ids`: `live-objectives`, `calendar`, `event-design`, `operations`, `contingency`

| facet | 추가 section ID |
|---|---|
| `rewards` | `live-rewards` |
| `economy-loop` | `live-rewards` |
| `monetization` | `live-rewards` |
| `segmentation` | `segmentation` |
| `telemetry` | `live-telemetry` |
| `exceptions` | `contingency` |

dependency:

- `live-rewards` → `event-design`
- `segmentation` → `event-design`

core 섹션은 제외할 수 없다. 명시적으로 포함한 섹션 또는 dependency를 동시에 제외하면 범위 충돌로 처리한다. 다른 프로필의 상세 명세는 이 문서에 펼치지 않고 안정적인 참조 ID와 별도 문서 핸드오프로 남긴다.

## 경계와 시각화

- 코어 시스템 구현 상세, 콘셉트 피치, 이벤트와 무관한 전체 경제는 넣지 않는다.
- 운영 도구, 설정 적용, 배포, 접근 권한과 복구의 기술 구현은 `개발 협의`로 남긴다.
- 운영 생명주기 Mermaid 1개가 필수다.
- 캘린더·KPI 수치가 있으면 Chart.js를 권장한다.
