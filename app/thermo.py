"""리뷰 점수, 온도, 별점 불일치 규칙."""


def to_label(score: float) -> str:
    """긍정 점수에 따라 positive, neutral, negative 라벨을 반환한다."""
    if score >= 0.6:
        return "positive"
    if score <= 0.4:
        return "negative"
    return "neutral"


def to_temperature(score: float) -> float:
    """긍정 점수를 0~100 사이의 온도로 변환한다."""
    return round(score * 100, 1)


def is_mismatch(rating: int, label: str) -> bool:
    """별점과 감성이 반대인지 반환하며 neutral 라벨은 불일치에서 제외한다."""
    return (rating in (4, 5) and label == "negative") or (
        rating in (1, 2) and label == "positive"
    )

# © 2026 김연지. All rights reserved. 수강생 개인 학습용 · 무단 강의·복제·배포·수정 금지 (LICENSE.md)
