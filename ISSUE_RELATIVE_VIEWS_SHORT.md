# Feat: Relative view 지원

## 문제

현재는 absolute view만 지원:
```python
views = {"AAPL": 0.10}  # "AAPL이 10% 수익"
```

Relative view 불가능:
```python
# "NVDA가 AAPL보다 20% 더 나을 것" ← 지금은 안됨!
```

## 해결책

Dict-based P 매트릭스 지원으로 통합:

```python
# 1. Absolute (기존)
views = {"AAPL": 0.10, "MSFT": 0.05}

# 2. Relative (새로운!)
views = {
    "P": [{"NVDA": 1, "AAPL": -1}],  # NVDA - AAPL
    "Q": [0.20]                       # 20% 차이
}
confidence = [0.9]

# 3. NumPy (고급)
views = {
    "P": [[1, -1, 0]],
    "Q": [0.20]
}
```

## 장점

✅ **LLM 친화적**: Ticker 이름으로 바로 생성 가능
✅ **사람이 읽기 쉬움**: `{"NVDA": 1, "AAPL": -1}` 명확
✅ **Backward compatible**: 기존 코드 100% 작동
✅ **순서 무관**: Index 몰라도 됨

## 구현 계획

1. `_parse_views()`: Dict/NumPy → P, Q 변환
2. `_normalize_confidence()`: 모든 타입 → list 통일
3. Validation: Ticker 존재, 길이 검증
4. 테스트: 10+ 케이스

## Acceptance Criteria

- [ ] Dict-based P 지원
- [ ] Backward compatible
- [ ] Confidence list 통일
- [ ] 완전한 validation
- [ ] 10+ 테스트
- [ ] 문서 업데이트

상세 내용: `ISSUE_RELATIVE_VIEWS.md` 참고
