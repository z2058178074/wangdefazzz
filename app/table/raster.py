from __future__ import annotations

from typing import List, Optional

import cv2
import numpy as np

from app.models import TableData
from app.table.grid import GridDetector, Line


class RasterGridDetector:
    def detect(self, image: np.ndarray) -> Optional[TableData]:
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY) if image.ndim == 3 else image
        binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
        height, width = gray.shape[:2]
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (max(12, width // 25), 1))
        vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, max(12, height // 25)))
        horizontal_mask = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horizontal_kernel)
        vertical_mask = cv2.morphologyEx(binary, cv2.MORPH_OPEN, vertical_kernel)
        lines: List[Line] = []
        for mask, orientation in ((horizontal_mask, "h"), (vertical_mask, "v")):
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                if orientation == "h" and w >= width * 0.2:
                    lines.append((float(x), y + h / 2, float(x + w), y + h / 2))
                if orientation == "v" and h >= height * 0.2:
                    lines.append((x + w / 2, float(y), x + w / 2, float(y + h)))
        return GridDetector.from_lines(lines, (float(width), float(height)), tolerance=max(3.0, min(width, height) * 0.01))
