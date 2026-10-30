"""요청/응답의 모양(스키마). 강사 제공 파일.

여기에 적힌 규칙을 어기는 요청은 FastAPI가 자동으로 422로 거절합니다.
세션 4에서 쿠폰 요청/응답의 모양을 이 파일에 추가합니다.
"""

from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints

# 앞뒤 공백을 지운 뒤 길이를 검사하는 글자 타입
Text500 = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]


class AnalyzeRequest(BaseModel):
    """1차: 리뷰 분석 요청"""

    text: Text500  # 리뷰 글 (1~500자)
    rating: int = Field(ge=1, le=5)  # 별점 (1~5)


class AnalyzeResponse(BaseModel):
    """1차: 리뷰 분석 결과"""

    label: Literal["positive", "negative"]  # 긍정/부정
    score: float  # AI가 준 '긍정일 확률' (0~1)
    temperature: float  # 리뷰 온도 (0~100)
    mismatch: bool  # 별점과 내용이 반대인가

# © 2026 김연지. All rights reserved. 수강생 개인 학습용 · 무단 강의·복제·배포·수정 금지 (LICENSE.md)
