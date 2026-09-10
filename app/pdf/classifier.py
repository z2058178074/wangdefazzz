from __future__ import annotations

from dataclasses import dataclass

from app.models import ConversionMode


@dataclass(frozen=True)
class PageStats:
    char_count: int
    text_area_ratio: float
    image_area_ratio: float


def classify_page(stats: PageStats) -> ConversionMode:
    """Choose OCR only when the embedded text layer is not useful."""
    if stats.char_count < 12:
        return ConversionMode.OCR
    if stats.text_area_ratio < 0.0004:
        return ConversionMode.OCR
    return ConversionMode.TEXT
