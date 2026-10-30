"""감성 분류 모델 부품 (강사 제공 — 수강생은 수정하지 않습니다).

`daekeun-ml/koelectra-small-v3-nsmc` (MIT 라이선스, 라벨 Neg=0 / Pos=1) 를
ONNX + int8 동적 양자화로 내보낸 파일을 사용한다.

- 모델 위치: 강사가 올려 둔 공개 Hugging Face 저장소
  (`thisispaperdoll/review-thermo-onnx`, 파일 위쪽의 `INSTRUCTOR_MODEL_REPO`).
  수강생은 아무것도 설정하지 않는다.
  (강사 테스트용으로 환경변수 `MODEL_REPO` 가 있으면 그 값이 우선한다)
- 내려받는 파일: `model_quantized.onnx`, `tokenizer.json`
  (`huggingface_hub.hf_hub_download` 사용)
- 첫 `predict()` 호출 때 한 번만 로드한다 (지연 로딩, 스레드 안전, 캐시)
- onnxruntime / tokenizers / huggingface_hub 는 로드 함수 안에서 import 하므로
  이 모듈을 import 하는 것만으로는 라이브러리도 네트워크도 필요하지 않다

공개 API:
    predict(texts) -> 각 텍스트의 긍정 확률 (0.0~1.0) 리스트
    MODEL_NAME     -> 원본 모델 이름

어떤 실패든 `RuntimeError` 로 감싸 올린다 (라우터가 503 으로 바꾼다).
"""

import os
import threading
from typing import Any

INSTRUCTOR_MODEL_REPO = "thisispaperdoll/review-thermo-onnx"  # 강사가 올려 둔 공개 모델 저장소

MODEL_NAME = "daekeun-ml/koelectra-small-v3-nsmc"
MODEL_FILE = "model_quantized.onnx"
TOKENIZER_FILE = "tokenizer.json"
MAX_LENGTH = 128

_lock = threading.Lock()
_cache: dict[str, Any] = {}


def _load() -> tuple[Any, Any, list[str]]:
    """모델과 토크나이저를 (필요하면) 내려받아 로드한다. 결과는 모듈 캐시에 보관."""
    if "session" in _cache:
        return _cache["session"], _cache["tokenizer"], _cache["input_names"]
    with _lock:
        if "session" in _cache:
            return _cache["session"], _cache["tokenizer"], _cache["input_names"]
        repo = os.getenv("MODEL_REPO") or INSTRUCTOR_MODEL_REPO
        try:
            import onnxruntime as ort
            from huggingface_hub import hf_hub_download
            from tokenizers import Tokenizer

            model_path = hf_hub_download(repo_id=repo, filename=MODEL_FILE)
            tokenizer_path = hf_hub_download(repo_id=repo, filename=TOKENIZER_FILE)

            tokenizer = Tokenizer.from_file(tokenizer_path)
            tokenizer.enable_truncation(max_length=MAX_LENGTH)
            tokenizer.enable_padding()

            session = ort.InferenceSession(model_path, providers=["CPUExecutionProvider"])
            input_names = [i.name for i in session.get_inputs()]
        except Exception as exc:
            raise RuntimeError(
                f"감성 분류 모델을 불러오지 못했습니다 (모델 저장소={repo!r}): {exc}"
            ) from exc
        _cache["tokenizer"] = tokenizer
        _cache["input_names"] = input_names
        _cache["session"] = session  # 마지막에 넣어 두어야 부분 로드 상태가 보이지 않는다
        return session, tokenizer, input_names


def predict(texts: list[str]) -> list[float]:
    """텍스트 목록을 받아 각 텍스트의 긍정 확률(0.0~1.0)을 같은 순서로 돌려준다."""
    if not texts:
        return []
    session, tokenizer, input_names = _load()
    try:
        import numpy as np

        encodings = tokenizer.encode_batch(list(texts))
        candidates = {
            "input_ids": np.array([e.ids for e in encodings], dtype=np.int64),
            "attention_mask": np.array([e.attention_mask for e in encodings], dtype=np.int64),
            "token_type_ids": np.array([e.type_ids for e in encodings], dtype=np.int64),
        }
        feeds = {name: candidates[name] for name in input_names if name in candidates}
        logits = session.run(None, feeds)[0]
        logits = logits - logits.max(axis=-1, keepdims=True)
        exp = np.exp(logits)
        probs = exp / exp.sum(axis=-1, keepdims=True)
        return [float(p) for p in probs[:, 1]]
    except Exception as exc:
        raise RuntimeError(f"감성 분류 추론에 실패했습니다: {exc}") from exc

# © 2026 김연지. All rights reserved. 수강생 개인 학습용 · 무단 강의·복제·배포·수정 금지 (LICENSE.md)
