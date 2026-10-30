# 명세서 (SPEC_REVIEW.md)

> © 2026 김연지. All rights reserved. 수강생 개인 학습용 · 무단 강의·복제·배포·수정 금지 · [LICENSE.md](LICENSE.md)

> `REQUEST.md` 1차 요구사항을 바탕으로 AI와의 인터뷰(7문 7답)를 거쳐 작성한 리뷰 온도계 기능 명세서입니다.

---

## 1. 이 기능은 무엇을 하나요? (한 문장)

- 고객의 리뷰 텍스트와 별점을 입력받아 AI 긍정/부정 감성 분석, 0~100℃ 리뷰 온도, 별점 불일치(mismatch) 여부를 판별해 주는 기능입니다.

---

## 2. 입력 (무엇을 받나요?)

| 이름 | 종류(글자/숫자) | 허용 범위 | 예 |
|---|---|---|---|
| `text` | 글자 (`str`) | 앞뒤 공백 제외 1~500자 (`min_length=1, max_length=500`) | "배송도 빠르고 품질도 마음에 듭니다!" |
| `rating` | 숫자 (`int`) | 1 이상 5 이하의 정수 (`1 <= rating <= 5`) | 5 |

---

## 3. 출력 (무엇을 돌려주나요?)

| 이름 | 종류 | 뜻 | 예 |
|---|---|---|---|
| `label` | 글자 (`str`) | 감성 분류 결과 (`"positive"`, `"negative"`, `"neutral"`) | `"positive"` |
| `score` | 숫자 (`float`) | AI 모델이 판단한 긍정 확률 (0.0 ~ 1.0, 소수점 4자리) | `0.8732` |
| `temperature` | 숫자 (`float`) | 리뷰의 긍정 정도를 나타내는 온도 (0.0 ~ 100.0℃) | `87.3` |
| `mismatch` | 참/거짓 (`bool`) | 별점과 리뷰 내용 감성의 불일치 여부 | `false` |

---

## 4. 규칙 (어떻게 정하나요?)

### 긍정/부정 기준 (`to_label`)
- **긍정 (`positive`)**: AI 점수(`score`) >= 0.6
- **부정 (`negative`)**: AI 점수(`score`) <= 0.4
- **중립 (`neutral`)**: 0.4 < AI 점수(`score`) < 0.6

### 리뷰 온도 계산법 (`to_temperature`)
- `score * 100`을 계산한 뒤, 소수점 첫째 자리까지 반올림합니다 (`round(score * 100, 1)`).
- 0.0℃(가장 부정적)부터 100.0℃(가장 긍정적)까지의 범위를 갖습니다.

### 별점과 내용이 '반대'라는 기준 (`is_mismatch`)
- **불일치 (`True`) 인정 조건**:
  1. 높은 별점(4점, 5점)인데 내용이 부정(`label == "negative"`)인 경우
  2. 낮은 별점(1점, 2점)인데 내용이 긍정(`label == "positive"`)인 경우
- **불일치 아님 (`False`) 조건**:
  - 별점과 감성 라벨의 방향이 일치하는 경우
  - 별점이 3점인 경우 (중립적 별점으로 보아 불일치 판정에서 제외)
  - 감성 라벨이 중립(`label == "neutral"`)인 경우

---

## 5. 예시표 (이 표가 그대로 테스트가 됩니다)

| 번호 | 입력 (`text`, `rating`, `score`) | 기대하는 출력 (`label`, `temperature`, `mismatch`) | 비고 |
|---|---|---|---|
| 1 | `text="너무 좋아요 최고예요"`, `rating=5`, `score=0.8732` | `label="positive"`, `temperature=87.3`, `mismatch=False` | 일반적인 긍정 일치 |
| 2 | `text="배송 최악이고 파손돼서 옴"`, `rating=5`, `score=0.2000` | `label="negative"`, `temperature=20.0`, `mismatch=True` | 별점은 높으나 내용은 부정 (불일치) |
| 3 | `text="생각보다 별로예요 실망"`, `rating=1`, `score=0.1500` | `label="negative"`, `temperature=15.0`, `mismatch=False` | 일반적인 부정 일치 |
| 4 | `text="기대 안 했는데 대만족"`, `rating=1`, `score=0.9200` | `label="positive"`, `temperature=92.0`, `mismatch=True` | 별점은 낮으나 내용은 긍정 (불일치) |
| 5 | `text="그냥 무난합니다 보통이에요"`, `rating=3`, `score=0.5200` | `label="neutral"`, `temperature=52.0`, `mismatch=False` | 별점 3점 및 중립 구간 |
| 6 | `text="괜찮은 편이에요"`, `rating=4`, `score=0.5500` | `label="neutral"`, `temperature=55.0`, `mismatch=False` | 중립 감성은 불일치 제외 |

---

## 6. 이런 입력은 거절합니다

1. **텍스트 유효성 검증 실패 (HTTP 422 Unprocessable Entity)**
   - `text`가 빈 문자열이거나 공백으로만 이루어진 경우 (`"   "`)
   - 앞뒤 공백 제거 후 길이가 1자 미만이거나 500자를 초과하는 경우
2. **별점 유효성 검증 실패 (HTTP 422 Unprocessable Entity)**
   - `rating`이 1 미만이거나 5 초과인 정수인 경우 (예: `0`, `6`)
   - `rating`이 정수형이 아니거나 누락된 경우
3. **요청 형식 오류 (HTTP 422 Unprocessable Entity)**
   - 필수 필드가 누락되었거나 JSON 본문 문법이 올바르지 않은 경우
4. **AI 모델 컴포넌트 장애 (HTTP 503 Service Unavailable)**
   - `app/sentiment.py`의 감성 분류 모델 로딩 실패 또는 추론 장애 발생 시

---

## 7. AI와 대화하면서 새로 알게 된 것, 애매했던 것

- **중립(neutral) 감성의 도입과 시스템 호환성**:
  - 사용자 인터뷰를 통해 0.4~0.6 점수 구간을 `neutral`로 분류하여 실질적인 고객 반응을 더 정밀하게 표현하도록 정의하였습니다.
  - 다만 현재 제공된 기본 스키마(`app/schemas.py`) 및 프론트엔드 연동 규격은 `Literal["positive", "negative"]`의 2진 분류(0.5 임계값)를 전제로 하고 있으므로, 강사 제공 공식 명세(`SPEC.md`)와 비교할 때 이 부분의 반영 여부를 조율해야 합니다.
- **별점 불일치(mismatch)에서 중간 별점(3점)과 중립 감성의 처리**:
  - 3점은 긍정도 부정도 아닌 중간 점수이므로 어느 감성이 오더라도 '반대'로 보지 않는 것이 자연스럽습니다.
  - 마찬가지로 감성이 `neutral`인 경우에도 극단적인 불일치로 단정하기 어려우므로 `mismatch=False`로 처리하기로 합의하였습니다.
- **수치 정밀도 및 표기 규칙**:
  - AI 모델의 긍정 확률 점수(`score`)는 소수점 4자리까지 제공되며, 온도(`temperature`)는 사용자 친화적으로 100을 곱한 뒤 소수점 첫째 자리에서 반올림(`round(..., 1)`)하는 일관된 계산 규칙을 확립했습니다.
