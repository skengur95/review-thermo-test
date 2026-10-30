"""쿠폰 API 계약 테스트 (SPEC_COUPON.md 4장 예시표 검증).

엔드포인트: POST /v1/coupons/issue
"""

import pytest


COUPON_API_CASES = [
    # Row 1: R1 사과 쿠폰 기준 상한 임계값 (20.0℃)
    pytest.param(
        "RV-01",
        "완전 최악 깨져서 왔어요",
        0.2000,
        {"issued": True, "coupon_type": "APOLOGY", "amount": 3000, "reason": None},
        id="Row_1_RV-01_apology_boundary_20.0C",
    ),
    # Row 2: R4 사과 쿠폰 기준 초과 (미발급 구간)
    pytest.param(
        "RV-02",
        "배송이 너무 느려서 실망",
        0.2001,
        {"issued": False, "coupon_type": None, "amount": None, "reason": "not_eligible"},
        id="Row_2_RV-02_not_eligible_boundary_20.1C",
    ),
    # Row 3: R4 중간 점수대 미발급
    pytest.param(
        "RV-03",
        "보통이에요 무난합니다",
        0.5000,
        {"issued": False, "coupon_type": None, "amount": None, "reason": "not_eligible"},
        id="Row_3_RV-03_not_eligible_50.0C",
    ),
    # Row 4: R4 30자 충족했으나 온도 80℃ 미만 (79.9℃)
    pytest.param(
        "RV-04",
        "가성비 만족하고 배송도 빠르고 정말 괜찮은 제품이에요.",
        0.7999,
        {"issued": False, "coupon_type": None, "amount": None, "reason": "not_eligible"},
        id="Row_4_RV-04_not_eligible_boundary_79.9C",
    ),
    # Row 5: R4 온도는 80℃ 이상이나 30자 미만 (21자)
    pytest.param(
        "RV-05",
        "완전 만족스럽고 최고예요 진짜 추천해요",
        0.9000,
        {"issued": False, "coupon_type": None, "amount": None, "reason": "not_eligible"},
        id="Row_5_RV-05_not_eligible_length_21chars",
    ),
    # Row 6: R2 감사 쿠폰 최소 온도(80.0℃) 및 최소 길이(30자) 일치
    pytest.param(
        "RV-06",
        "완전 만족스럽고 최고예요 진짜 추천해요 꼭사세요!",
        0.8000,
        {"issued": True, "coupon_type": "THANKS", "amount": 3000, "reason": None},
        id="Row_6_RV-06_thanks_boundary_80.0C_30chars",
    ),
    # Row 7: R2 일반적인 감사 쿠폰 발급
    pytest.param(
        "RV-07",
        "품질도 너무 좋고 마감도 깔끔해서 가족들에게도 추천했습니다.",
        0.9200,
        {"issued": True, "coupon_type": "THANKS", "amount": 3000, "reason": None},
        id="Row_7_RV-07_thanks_92.0C_33chars",
    ),
]


@pytest.mark.parametrize(("review_id", "text", "score", "expected"), COUPON_API_CASES)
def test_coupon_issue_matches_spec_examples(make_client, review_id, text, score, expected):
    """Rows 1~7: 정상 요청에 대한 쿠폰 발급/미발급 판정 확인."""
    r = make_client(score).post("/v1/coupons/issue", json={"review_id": review_id, "text": text})
    assert r.status_code == 200
    data = r.json()
    assert data["issued"] == expected["issued"]
    assert data.get("coupon_type") == expected["coupon_type"]
    assert data.get("amount") == expected["amount"]
    assert data.get("reason") == expected["reason"]
    if data["issued"]:
        assert data.get("code") is not None
        assert data["code"].startswith(f"{expected['coupon_type']}-")


def test_coupon_issue_duplicate_matches_spec_row_8(make_client):
    """Row 8: R3 동일 review_id 재발급 시도시 already_issued 거절 확인."""
    client = make_client(0.2000)
    # 최초 발급 성공
    first = client.post("/v1/coupons/issue", json={"review_id": "RV-01", "text": "완전 최악 깨져서 왔어요"})
    assert first.status_code == 200
    assert first.json()["issued"] is True

    # 재요청 시 중복 발급 방지 거절
    second = client.post("/v1/coupons/issue", json={"review_id": "RV-01", "text": "완전 최악 깨져서 왔어요 재요청"})
    assert second.status_code == 200
    assert second.json()["issued"] is False
    assert second.json().get("reason") == "already_issued"


def test_coupon_issue_blank_text_matches_spec_row_9(make_client):
    """Row 9: R5 공백뿐인 본문은 422 거절."""
    r = make_client(0.5000).post("/v1/coupons/issue", json={"review_id": "RV-08", "text": "   "})
    assert r.status_code == 422


def test_coupon_issue_empty_review_id_matches_spec_row_10(make_client):
    """Row 10: R5 빈 review_id는 422 거절."""
    r = make_client(0.5000).post("/v1/coupons/issue", json={"review_id": "", "text": "정말 마음에 들어요"})
    assert r.status_code == 422


def test_coupon_issue_too_long_text_matches_spec_row_11(make_client):
    """Row 11: R5 500자 초과 본문은 422 거절."""
    r = make_client(0.5000).post("/v1/coupons/issue", json={"review_id": "RV-09", "text": "A" * 501})
    assert r.status_code == 422


def test_coupon_issue_ai_down_matches_spec_row_12(broken_client):
    """Row 12: R6 AI 컴포넌트 장애 시 503 거절."""
    r = broken_client.post("/v1/coupons/issue", json={"review_id": "RV-10", "text": "좋은 상품입니다"})
    assert r.status_code == 503
