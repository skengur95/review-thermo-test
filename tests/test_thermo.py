import pytest

from app.thermo import is_mismatch, to_label, to_temperature


@pytest.mark.parametrize(
    ("score", "expected"),
    [
        (0.8732, "positive"),
        (0.2000, "negative"),
        (0.1500, "negative"),
        (0.9200, "positive"),
        (0.5200, "neutral"),
        (0.5500, "neutral"),
    ],
)
def test_to_label_matches_review_spec_examples(score, expected):
    assert to_label(score) == expected


@pytest.mark.parametrize(
    ("score", "expected"),
    [
        (0.8732, 87.3),
        (0.2000, 20.0),
        (0.1500, 15.0),
        (0.9200, 92.0),
        (0.5200, 52.0),
        (0.5500, 55.0),
    ],
)
def test_to_temperature_matches_review_spec_examples(score, expected):
    assert to_temperature(score) == expected


@pytest.mark.parametrize(
    ("rating", "label", "expected"),
    [
        (5, "positive", False),
        (5, "negative", True),
        (1, "negative", False),
        (1, "positive", True),
        (3, "neutral", False),
        (4, "neutral", False),
    ],
)
def test_is_mismatch_matches_review_spec_examples(rating, label, expected):
    assert is_mismatch(rating, label) is expected
