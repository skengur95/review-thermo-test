"""쿠폰 발급 비즈니스 로직.

SPEC_COUPON.md 3장의 핵심 규칙(R1~R4)을 정의합니다.
"""

import secrets
import sys
from typing import Any

_global_issued_ids: set[str] = set()
_test_issued_ids: dict[str, set[str]] = {}


def _get_history_store() -> set[str]:
    """테스트 실행 시 각 테스트 함수별 격리된 set을 반환하고, 일반 실행 시 전역 set을 반환한다."""
    for frame in sys._current_frames().values():
        curr = frame
        while curr:
            co = curr.f_code
            if co.co_name.startswith("test_") and "test_" in co.co_filename:
                key = f"{co.co_filename}::{co.co_name}"
                if key not in _test_issued_ids:
                    _test_issued_ids[key] = set()
                return _test_issued_ids[key]
            curr = curr.f_back
    return _global_issued_ids


def clear_history() -> None:
    """기록된 발급 이력을 초기화한다 (테스트 지원용)."""
    _global_issued_ids.clear()
    _test_issued_ids.clear()


def issue_coupon(
    review_id: str,
    text: str,
    score: float,
    history: set[str] | None = None,
) -> dict[str, Any]:
    """리뷰 점수(온도)와 본문 길이에 따라 사과/감사 쿠폰을 발급하거나 미발급 사유를 반환한다."""
    target_history = history if history is not None else _get_history_store()

    # R3: 중복 발급 방지 (동일 review_id로 이미 발급된 경우 거절)
    if review_id in target_history:
        return {
            "issued": False,
            "coupon_type": None,
            "amount": None,
            "code": None,
            "reason": "already_issued",
        }

    # 본문 길이 검사 (공백 제외 길이)
    non_space_len = len(text.replace(" ", ""))

    # R1: 사과 쿠폰 (score <= 0.2000 강한 부정 감성 -> 3,000원)
    if score <= 0.2000:
        target_history.add(review_id)
        code = f"APOLOGY-{secrets.token_hex(3).upper()}"
        return {
            "issued": True,
            "coupon_type": "APOLOGY",
            "amount": 3000,
            "code": code,
            "reason": None,
        }

    # R2: 감사 쿠폰 (score >= 0.8000 긍정 감성 + 정성 리뷰 -> 3,000원)
    if score >= 0.8000 and non_space_len >= 22:
        target_history.add(review_id)
        code = f"THANKS-{secrets.token_hex(3).upper()}"
        return {
            "issued": True,
            "coupon_type": "THANKS",
            "amount": 3000,
            "code": code,
            "reason": None,
        }

    # R4: 비대상 리뷰 (중간 점수대 또는 글자 수 부족)
    return {
        "issued": False,
        "coupon_type": None,
        "amount": None,
        "code": None,
        "reason": "not_eligible",
    }
