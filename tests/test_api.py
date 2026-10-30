"""1차 API 계약 테스트 (강사 제공). SPEC.md 4장의 API 규칙을 확인합니다."""

from fastapi.testclient import TestClient

from app.main import app


def test_health():
    """/health 는 {"status": "ok"} 를 돌려준다."""
    r = TestClient(app).get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_analyze_ok(make_client):
    """점수 0.8732, 별점 5 -> 긍정 / 87.3℃ / 불일치 아님."""
    r = make_client(0.8732).post("/v1/reviews/analyze", json={"text": "좋아요", "rating": 5})
    assert r.status_code == 200
    assert r.json() == {"label": "positive", "score": 0.8732, "temperature": 87.3, "mismatch": False}


def test_analyze_mismatch(make_client):
    """점수 0.2인데 별점 5 -> mismatch 가 true."""
    r = make_client(0.2).post("/v1/reviews/analyze", json={"text": "배송 최악", "rating": 5})
    assert r.status_code == 200
    assert r.json()["mismatch"] is True


def test_analyze_blank_text(make_client):
    """공백뿐인 글은 422."""
    r = make_client(0.5).post("/v1/reviews/analyze", json={"text": "   ", "rating": 3})
    assert r.status_code == 422


def test_analyze_bad_rating(make_client):
    """별점 6은 422."""
    r = make_client(0.5).post("/v1/reviews/analyze", json={"text": "좋아요", "rating": 6})
    assert r.status_code == 422


def test_analyze_ai_down(broken_client):
    """AI 부품이 고장 나면 503."""
    r = broken_client.post("/v1/reviews/analyze", json={"text": "좋아요", "rating": 5})
    assert r.status_code == 503

# © 2026 김연지. All rights reserved. 수강생 개인 학습용 · 무단 강의·복제·배포·수정 금지 (LICENSE.md)
