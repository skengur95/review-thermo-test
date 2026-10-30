"""쿠폰 발급 비즈니스 로직 단위 테스트.

SPEC_COUPON.md 4장 예시표의 규칙(R1~R4)을 검증합니다.
"""

import pytest

try:
    from app.coupon import issue_coupon
except ImportError:
    def issue_coupon(*args, **kwargs):  # type: ignore[no-redef]
        raise NotImplementedError("app.coupon.issue_coupon이 아직 구현되지 않았습니다.")


COUPON_CASES = [
    # Row 1: R1 사과 쿠폰 기준 상한 임계값 (20.0℃)
    pytest.param(
        "RV-01",
        "완전 최악 깨져서 왔어요",
        0.2000,
        {"issued": True, "coupon_type": "APOLOGY", "amount": 3000, "reason": None},
        id="RV-01_apology_boundary_20.0C",
    ),
    # Row 2: R4 사과 쿠폰 기준 초과 (미발급 구간)
    pytest.param(
        "RV-02",
        "배송이 너무 느려서 실망",
        0.2001,
        {"issued": False, "coupon_type": None, "amount": None, "reason": "not_eligible"},
        id="RV-02_not_eligible_boundary_20.1C",
    ),
    # Row 3: R4 중간 점수대 미발급
    pytest.param(
        "RV-03",
        "보통이에요 무난합니다",
        0.5000,
        {"issued": False, "coupon_type": None, "amount": None, "reason": "not_eligible"},
        id="RV-03_not_eligible_50.0C",
    ),
    # Row 4: R4 30자 충족했으나 온도 80℃ 미만 (79.9℃)
    pytest.param(
        "RV-04",
        "가성비 만족하고 배송도 빠르고 정말 괜찮은 제품이에요.",
        0.7999,
        {"issued": False, "coupon_type": None, "amount": None, "reason": "not_eligible"},
        id="RV-04_not_eligible_boundary_79.9C",
    ),
    # Row 5: R4 온도는 80℃ 이상이나 30자 미만 (21자)
    pytest.param(
        "RV-05",
        "완전 만족스럽고 최고예요 진짜 추천해요",
        0.9000,
        {"issued": False, "coupon_type": None, "amount": None, "reason": "not_eligible"},
        id="RV-05_not_eligible_length_21chars",
    ),
    # Row 6: R2 감사 쿠폰 최소 온도(80.0℃) 및 최소 길이(30자) 일치
    pytest.param(
        "RV-06",
        "완전 만족스럽고 최고예요 진짜 추천해요 꼭사세요!",
        0.8000,
        {"issued": True, "coupon_type": "THANKS", "amount": 3000, "reason": None},
        id="RV-06_thanks_boundary_80.0C_30chars",
    ),
    # Row 7: R2 일반적인 감사 쿠폰 발급
    pytest.param(
        "RV-07",
        "품질도 너무 좋고 마감도 깔끔해서 가족들에게도 추천했습니다.",
        0.9200,
        {"issued": True, "coupon_type": "THANKS", "amount": 3000, "reason": None},
        id="RV-07_thanks_92.0C_33chars",
    ),
]


@pytest.mark.parametrize(("review_id", "text", "score", "expected"), COUPON_CASES)
def test_issue_coupon_matches_spec_examples(review_id, text, score, expected):
    res = issue_coupon(review_id, text, score)
    assert res["issued"] == expected["issued"]
    assert res.get("coupon_type") == expected["coupon_type"]
    assert res.get("amount") == expected["amount"]
    assert res.get("reason") == expected["reason"]
    if res["issued"]:
        assert res.get("code") is not None
        assert res["code"].startswith(f"{expected['coupon_type']}-")


def test_issue_coupon_duplicate_matches_spec_row_8():
    """Row 8: R3 동일 review_id 재발급 시도시 already_issued 거절."""
    first = issue_coupon("RV-01", "완전 최악 깨져서 왔어요", 0.2000)
    assert first["issued"] is True

    second = issue_coupon("RV-01", "완전 최악 깨져서 왔어요 재요청", 0.1500)
    assert second["issued"] is False
    assert second["reason"] == "already_issued"
