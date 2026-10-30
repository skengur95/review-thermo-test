"""FastAPI 앱 (강사 제공). 세션 4에서 쿠폰 API를 이 파일에 추가합니다.

실행: uvicorn app.main:app --reload
흐름: 화면/요청 -> 입력 검사(schemas) -> AI 점수(predict) -> 규칙(thermo) -> 응답
"""

from collections.abc import Callable
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app import thermo
from app.deps import get_predict
from app.schemas import AnalyzeRequest, AnalyzeResponse

app = FastAPI(title="리뷰 온도계 API", version="1.0.0")

Predict = Callable[[list[str]], list[float]]


@app.exception_handler(NotImplementedError)
async def not_implemented(request: Request, exc: NotImplementedError) -> JSONResponse:
    """아직 AI와 함께 만들지 않은 함수를 부르면 501과 함수 이름을 알려 준다."""
    return JSONResponse(status_code=501, content={"detail": f"아직 구현되지 않았습니다: {exc}"})


def get_score(predict: Predict, text: str) -> float:
    """AI 부품에게 점수를 받는다. 실패하면 503."""
    try:
        return predict([text])[0]
    except Exception as exc:
        raise HTTPException(status_code=503, detail="AI 부품이 응답하지 않습니다") from exc


@app.get("/health")
def health() -> dict[str, str]:
    """서버가 살아 있는지 확인."""
    return {"status": "ok"}


@app.post("/v1/reviews/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest, predict: Predict = Depends(get_predict)) -> AnalyzeResponse:
    """1차: 리뷰 한 건 -> 긍정/부정, 온도, 별점 불일치."""
    score = round(get_score(predict, req.text), 4)
    label = thermo.to_label(score)  # 규칙은 app/thermo.py
    return AnalyzeResponse(
        label=label,
        score=score,
        temperature=thermo.to_temperature(score),
        mismatch=thermo.is_mismatch(req.rating, label),
    )


# 화면(static/)은 마지막에 "/" 로 연결해야 위의 API 경로가 먼저 잡힌다.
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
if STATIC_DIR.is_dir():
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")

# © 2026 김연지. All rights reserved. 수강생 개인 학습용 · 무단 강의·복제·배포·수정 금지 (LICENSE.md)
