"""주문 관리 유틸리티 - 버그 찾기 연습용 (고치지 말고 찾기만 하세요)."""


def average_amount(amounts):
    """주문 금액의 평균을 구한다."""
    total = sum(amounts)  # 금액을 모두 더한다
    return total / len(amounts)  # 개수로 나눈다


def add_tag(order, tag, tags=[]):
    """주문에 태그를 붙인다."""
    tags.append(tag)  # 태그 목록에 추가
    order["tags"] = tags
    return order


def get_page(orders, page, size=10):
    """주문 목록에서 page번째(1부터 시작) 페이지를 돌려준다."""
    start = page * size  # 시작 위치
    end = start + size  # 끝 위치
    return orders[start:end]

# © 2026 김연지. All rights reserved. 수강생 개인 학습용 · 무단 강의·복제·배포·수정 금지 (LICENSE.md)
