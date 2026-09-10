from __future__ import annotations

from pathlib import Path
from typing import Callable, List, Optional

import numpy as np

from app.models import TextBlock
from app.utils.resources import resource_path


class OCRModelError(RuntimeError):
    pass


class OCREngine:
    REQUIRED_FILES = (
        "PP-OCRv6_det_small.onnx",
        "PP-OCRv6_rec_small.onnx",
        "ch_ppocr_mobile_v2.0_cls_mobile.onnx",
    )

    def __init__(
        self,
        model_dir: Optional[Path] = None,
        engine_factory: Optional[Callable] = None,
    ):
        self.model_dir = Path(model_dir) if model_dir else resource_path("models")
        self.engine_factory = engine_factory
        self._engine = None

    def _validate_models(self) -> None:
        missing = [name for name in self.REQUIRED_FILES if not (self.model_dir / name).is_file()]
        if missing:
            raise OCRModelError(f"OCR 模型不完整，缺少：{'、'.join(missing)}")

    def _load(self):
        self._validate_models()
        if self._engine is not None:
            return self._engine
        params = {
            "Global.model_root_dir": str(self.model_dir),
            "Global.log_level": "error",
            "Det.model_path": str(self.model_dir / self.REQUIRED_FILES[0]),
            "Rec.model_path": str(self.model_dir / self.REQUIRED_FILES[1]),
            "Cls.model_path": str(self.model_dir / self.REQUIRED_FILES[2]),
        }
        if self.engine_factory is None:
            from rapidocr import RapidOCR

            self._engine = RapidOCR(params=params)
        else:
            self._engine = self.engine_factory(params=params)
        return self._engine

    def recognize(self, image: np.ndarray) -> List[TextBlock]:
        output = self._load()(image)
        if output is None or output.boxes is None or output.txts is None:
            return []
        scores = output.scores or [1.0] * len(output.txts)
        blocks: List[TextBlock] = []
        for box, text, score in zip(output.boxes, output.txts, scores):
            points = np.asarray(box, dtype=float)
            blocks.append(
                TextBlock(
                    text=str(text).strip(),
                    bbox=(
                        float(points[:, 0].min()),
                        float(points[:, 1].min()),
                        float(points[:, 0].max()),
                        float(points[:, 1].max()),
                    ),
                    confidence=float(score),
                )
            )
        return [block for block in blocks if block.text]
