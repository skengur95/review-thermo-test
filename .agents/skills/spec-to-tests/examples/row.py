# 예시표 한 줄 = pytest.param 한 줄
# | score | 결과 |      ->  pytest.param(입력, 기대값, id="입력값")
# | 0.5   | positive |
import pytest

LABEL_CASES = [
    pytest.param(0.5, "positive", id="0.5_boundary"),
]

# © 2026 김연지. All rights reserved. 수강생 개인 학습용 · 무단 강의·복제·배포·수정 금지 (LICENSE.md)
