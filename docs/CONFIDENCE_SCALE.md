# Confidence Scale Guide

## 확신도 스케일 (Confidence Scale)

Black-Litterman 모델에서 확신도는 **투자자 견해가 포트폴리오에 얼마나 영향을 미칠지** 결정합니다.

### 📊 확신도 스케일 (0.5 = 중립 기준점)

```
100% ■■■■■■■■■■ 절대 확실 (Absolute Certainty)
 95% ■■■■■■■■■□ 매우 확신 (Very Confident) ← 거의 틀림없음
 85% ■■■■■■■■□□ 확신 (Confident) ← 높은 신뢰도
 75% ■■■■■■■□□□ 꽤 확신 (Quite Confident)
 60% ■■■■■■□□□□ 약간 확신 (Somewhat Confident)
────────────────────────────────────────────
 50% ■■■■■□□□□□ 보통/중립 (Neutral) ← 기준점
────────────────────────────────────────────
 40% ■■■■□□□□□□ 약간 불확실 (Somewhat Uncertain)
 30% ■■■□□□□□□□ 불확실 (Uncertain)
 10% ■□□□□□□□□□ 매우 불확실 (Very Uncertain) ← 거의 무의미
  0% □□□□□□□□□□ 완전 무의미 (No Information)
```

### 🎯 핵심 포인트

1. **50%는 중립 상태**
   - 견해가 있지만 확신이 없음
   - 포트폴리오에 최소한의 영향만 줌
   - 기본값

2. **60% 이상: 강한 견해**
   - 견해가 실제로 포트폴리오에 영향을 줌
   - 60%: 약간의 영향
   - 75%: 중간 정도 영향
   - 85%: 강한 영향
   - 95%+: 매우 강한 영향

3. **40% 이하: 약한 견해**
   - 견해가 거의 무시됨
   - 정보가 불확실하거나 신뢰할 수 없음
   - 30% 이하는 사실상 무의미

## 📋 자연어 → 숫자 변환 표

### 한국어

| 표현 | 확신도 | 설명 |
|------|--------|------|
| 틀림없어, 절대 확실해 | 100% (1.0) | 완전히 확실 |
| 매우 확신, 아주 확신 | 95% (0.95) | 거의 틀림없음 |
| 확신해, 그럴 것 같아 | 85% (0.85) | 높은 신뢰도 |
| 꽤 확신, 상당히 확신 | 75% (0.75) | 중상 수준 |
| 약간 확신, 조금 확신 | 60% (0.6) | 반반보다 나은 정도 |
| 보통, 잘 모름, 반반 | 50% (0.5) | **중립 (기준점)** |
| 약간 불확실 | 40% (0.4) | 반반보다 못한 정도 |
| 불확실, 별로 확신 없어 | 30% (0.3) | 낮은 신뢰도 |
| 매우 불확실, 전혀 확신 없어 | 10% (0.1) | 거의 무의미 |

### English

| Expression | Confidence | Description |
|------------|------------|-------------|
| Absolute certainty, Definitely | 100% (1.0) | Completely certain |
| Very confident, Certain | 95% (0.95) | Almost certain |
| Confident, Sure | 85% (0.85) | High confidence |
| Quite confident, Fairly sure | 75% (0.75) | Moderately high |
| Somewhat confident, Slightly sure | 60% (0.6) | Slightly above neutral |
| Neutral, Don't know, 50-50 | 50% (0.5) | **Neutral (Pivot)** |
| Somewhat uncertain, Not very sure | 40% (0.4) | Slightly below neutral |
| Uncertain, Not sure | 30% (0.3) | Low confidence |
| Very uncertain, No confidence | 10% (0.1) | Almost meaningless |

## 🔧 입력 형식 (모두 동등하게 지원!)

### 1. 퍼센트 (Percentage: 0-100)

```python
confidence=95   # 95%
confidence=85   # 85%
confidence=50   # 50% (중립)
```

### 2. 소수점 (Decimal: 0.0-1.0)

```python
confidence=0.95  # 95%
confidence=0.85  # 85%
confidence=0.5   # 50% (중립)
```

### 3. 퍼센트 문자열

```python
confidence="95%"
confidence="85%"
confidence="50%"
```

### 4. 소수점 문자열

```python
confidence="0.95"
confidence="0.85"
confidence="0.5"
```

**모든 형식이 동일하게 작동합니다!**
- `70` = `0.7` = `"70%"` = `"0.7"` → 모두 70%로 처리
- `95` = `0.95` = `"95%"` = `"0.95"` → 모두 95%로 처리

## 💡 사용 예시

### 예시 1: 강한 견해

```
사용자: "AAPL이 30% 수익 낼 것 같아. 매우 확신해!"

Agent 변환:
views={"AAPL": 0.30}
confidence=95  # "매우 확신" → 95%

결과: AAPL 비중이 크게 증가
```

### 예시 2: 중립 견해

```
사용자: "MSFT가 10% 수익 낼 것 같은데, 잘 모르겠어."

Agent 변환:
views={"MSFT": 0.10}
confidence=50  # "잘 모르겠어" → 50% (중립)

결과: 견해가 최소한만 반영됨
```

### 예시 3: 약한 견해

```
사용자: "GOOGL 15% 수익 예상. 별로 확신 없어."

Agent 변환:
views={"GOOGL": 0.15}
confidence=30  # "별로 확신 없어" → 30%

결과: 견해가 거의 무시됨
```

## ⚠️ 주의사항

### DO ✅

- 퍼센트로 입력: `70`, `80`, `95`
- 자연어 사용: "매우 확신", "보통", "불확실"
- 50%를 중립 상태로 이해
- 높은 확신일수록 견해가 강하게 반영됨을 인지

### DON'T ❌

- 1-5 사이 값 사용 (애매함): `confidence=2`
- 100% 초과: `confidence=150`
- 음수: `confidence=-10`
- 자연어 그대로 전달: `confidence="확신"` (숫자로 변환 필요)

## 🧪 테스트

```bash
# 확신도 타입 처리 테스트
make test-confidence
```

테스트 결과:
```
✅ Very confident (95%): 95 (int) → 0.95
✅ Confident (85%): 85 (int) → 0.85
✅ Neutral (50%): 50 (int) → 0.5
✅ Uncertain (30%): 30 (int) → 0.3
✅ Very uncertain (10%): 10 (int) → 0.1
```

## 🎓 Black-Litterman 이론

### Omega 행렬

확신도는 Black-Litterman 모델의 **Omega 행렬** (견해의 불확실성)을 계산하는 데 사용됩니다:

- **높은 확신도 (85-95%)**: Omega가 작음 → 견해가 강하게 반영
- **중립 확신도 (50%)**: Omega가 중간 → 견해가 약하게 반영
- **낮은 확신도 (10-30%)**: Omega가 큼 → 견해가 거의 무시됨

### Idzorek 방법

본 프로젝트는 Idzorek(2005) 방법을 사용하여 확신도를 Omega로 변환합니다:
- 직관적인 확신도 입력 (0-100%)
- 자동으로 최적의 Omega 계산
- Black-Litterman 사후 분포 생성

## 📚 참고 자료

- [Black-Litterman Model Overview](https://en.wikipedia.org/wiki/Black%E2%80%93Litterman_model)
- Idzorek, T. (2005). "A Step-by-Step Guide to the Black-Litterman Model"
- 프로젝트 문서: `memory-bank/productContext.md`

---

**Version**: 2.0 (Improved Scale with 0.5 Neutral Pivot)
**Last Updated**: 2025-11-22
