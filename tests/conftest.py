"""강사 제공 테스트 도구: 가짜 AI 부품을 끼운 TestClient (모델·네트워크 필요 없음)."""

from collections.abc import Callable, Iterator

import pytest
from fastapi.testclient import TestClient

from app.deps import get_predict
from app.main import app


@pytest.fixture
def make_client() -> Iterator[Callable[[float], TestClient]]:
    """`make_client(0.8)` -> 어떤 리뷰든 점수 0.8을 돌려주는 가짜 AI가 연결된 클라이언트."""

    def _make(score: float) -> TestClient:
        def fake_predict(texts: list[str]) -> list[float]:
            return [score] * len(texts)

        app.dependency_overrides[get_predict] = lambda: fake_predict
        return TestClient(app)

    yield _make
    app.dependency_overrides.clear()


@pytest.fixture
def broken_client() -> Iterator[TestClient]:
    """AI 부품이 고장 난 클라이언트 (predict가 항상 에러) — 503 확인용."""

    def broken_predict(texts: list[str]) -> list[float]:
        raise RuntimeError("model down")

    app.dependency_overrides[get_predict] = lambda: broken_predict
    yield TestClient(app)
    app.dependency_overrides.clear()

# © 2026 김연지. All rights reserved. 수강생 개인 학습용 · 무단 강의·복제·배포·수정 금지 (LICENSE.md)
