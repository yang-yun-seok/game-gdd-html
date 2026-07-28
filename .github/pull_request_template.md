## 변경 요약

<!-- 무엇을 변경했는지 2~5개 항목으로 작성해 주세요. -->

-

## 변경 이유

<!-- 해결하려는 문제와 이 변경이 필요한 이유를 설명해 주세요. -->

## 영향 범위

- 관련 profile:
- 관련 document kind:
- GDDQL 호환성:
- 입력 JSON 호환성:
- HTML 메타데이터 호환성:

## 검증

실행한 명령과 결과를 작성해 주세요.

```text
python tools/validate_skill.py skill/game-gdd-html
python tests/test_interpreter.py
python tests/test_context_compiler.py
python tests/test_kinds.py
python tests/test_profiles.py
```

## 렌더 결과

<!-- 렌더러 또는 템플릿을 변경했다면 예제 HTML과 스크린샷을 첨부해 주세요. -->

## 체크리스트

- [ ] 변경 범위와 관련 없는 파일을 포함하지 않았습니다.
- [ ] 계약, 참고 문서와 테스트를 함께 갱신했습니다.
- [ ] 기존 자연어·GDDQL 요청의 하위 호환성을 확인했습니다.
- [ ] 기획 문서가 클래스·API·DB·알고리즘 등 구현 방식을 확정하지 않습니다.
- [ ] profile, kind, facet와 내부 파이프라인 정보가 최종 본문에 노출되지 않습니다.
- [ ] 근거 없는 수치와 외부 사실을 확정하지 않습니다.
- [ ] 새 kind라면 고유한 산출물·제외 범위·핸드오프를 정의했습니다.
- [ ] 모든 자동 테스트가 통과합니다.
- [ ] 사용자에게 영향을 주는 변경을 README 또는 CHANGELOG에 기록했습니다.

## 관련 Issue

<!-- 예: Closes #123 -->
