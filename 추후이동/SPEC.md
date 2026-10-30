# 리뷰 온도계 — 공식 명세서 v1.0

> © 2026 김연지. All rights reserved. 수강생 개인 학습용 · 무단 강의·복제·배포·수정 금지 · [LICENSE.md](LICENSE.md)

> 세션 2에서 여러분이 쓴 명세와 비교한 뒤, 이후 개발은 이 문서를 따릅니다.
> 이 문서와 `tests/`는 사람의 허락 없이 수정하지 않습니다.

## 1. 한 문장 요약

리뷰 한 건과 별점을 받아서 긍정/부정, 리뷰 온도(0~100℃), 별점 불일치 여부를 돌려준다.

## 2. 규칙 (함수 3개, `app/thermo.py`)

| 함수 | 하는 일 |
|---|---|
| `to_label(score)` | score가 0.5 이상이면 `"positive"`, 아니면 `"negative"` |
| `to_temperature(score)` | score × 100 을 소수점 첫째 자리까지 반올림 |
| `is_mismatch(rating, label)` | 별점 4~5인데 negative, 또는 별점 1~2인데 positive이면 `True`. 별점 3은 항상 `False` |

score는 AI 부품 `predict()`가 돌려주는 '긍정일 확률'(0.0~1.0)입니다.

## 3. 예시표 (한 줄 = 테스트 한 줄)

### to_label

| score | 결과 |
|---|---|
| 0.9 | "positive" |
| 0.5 | "positive" (경계값) |
| 0.4999 | "negative" |
| 0.1 | "negative" |

### to_temperature

| score | 결과 |
|---|---|
| 0.8732 | 87.3 |
| 0.5 | 50.0 |
| 0.0 | 0.0 |
| 1.0 | 100.0 |

### is_mismatch

| rating | label | 결과 |
|---|---|---|
| 5 | "negative" | True |
| 4 | "negative" | True |
| 2 | "positive" | True |
| 1 | "positive" | True |
| 3 | "negative" | False |
| 5 | "positive" | False |
| 1 | "negative" | False |

## 4. API

### GET /health

응답: `{"status": "ok"}`

### POST /v1/reviews/analyze

요청:

```json
{"text": "배송도 빠르고 품질도 좋아요", "rating": 5}
```

- `text`: 1~500자 (앞뒤 공백 제거 후)
- `rating`: 정수 1~5

응답 (200):

```json
{"label": "positive", "score": 0.8732, "temperature": 87.3, "mismatch": false}
```

- `score`는 소수점 넷째 자리까지 반올림한 값

### 에러

| 상황 | 상태 코드 |
|---|---|
| 입력이 규칙에 맞지 않음 (빈 글, 500자 초과, 별점 0이나 6) | 422 |
| AI 부품이 응답하지 못함 | 503 |
