from __future__ import annotations

from pathlib import Path
from typing import List

import pdfplumber

from app.models import PageContent, TextBlock
from app.pdf.classifier import PageStats
from app.table.vector import extract_vector_tables


class PDFAnalyzer:
    """Extract positioned text from a PDF without OCR."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self._pdf = None

    def __enter__(self) -> "PDFAnalyzer":
        self._pdf = pdfplumber.open(self.path)
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        if self._pdf is not None:
            self._pdf.close()
            self._pdf = None

    @property
    def page_count(self) -> int:
        if self._pdf is None:
            raise RuntimeError("PDF 尚未打开")
        return len(self._pdf.pages)

    def analyze_page(
        self,
        index: int,
        use_ocr: bool = False,
        preserve_tables: bool = True,
    ) -> PageContent:
        if self._pdf is None:
            raise RuntimeError("PDF 尚未打开")
        if use_ocr:
            raise ValueError("文字分析器不执行 OCR")
        page = self._pdf.pages[index]
        words = page.extract_words(
            x_tolerance=2,
            y_tolerance=3,
            keep_blank_chars=False,
            use_text_flow=False,
        )
        blocks = self._words_to_lines(words)
        tables = extract_vector_tables(page) if preserve_tables else []
        if tables:
            blocks = [
                block
                for block in blocks
                if not any(
                    table.bbox[0] <= (block.bbox[0] + block.bbox[2]) / 2 <= table.bbox[2]
                    and table.bbox[1] <= (block.bbox[1] + block.bbox[3]) / 2 <= table.bbox[3]
                    for table in tables
                )
            ]
        return PageContent(
            page_number=index + 1,
            width=float(page.width),
            height=float(page.height),
            text_blocks=blocks,
            tables=tables,
        )

    def page_stats(self, index: int) -> PageStats:
        if self._pdf is None:
            raise RuntimeError("PDF 尚未打开")
        page = self._pdf.pages[index]
        area = max(float(page.width) * float(page.height), 1.0)
        chars = page.chars
        char_count = sum(1 for char in chars if str(char.get("text", "")).strip())
        text_area = sum(
            max(0.0, float(char["x1"]) - float(char["x0"]))
            * max(0.0, float(char["bottom"]) - float(char["top"]))
            for char in chars
        )
        image_area = sum(
            max(0.0, float(item["x1"]) - float(item["x0"]))
            * max(0.0, float(item["bottom"]) - float(item["top"]))
            for item in page.images
        )
        return PageStats(
            char_count=char_count,
            text_area_ratio=min(1.0, text_area / area),
            image_area_ratio=min(1.0, image_area / area),
        )

    @staticmethod
    def _words_to_lines(words: list, tolerance: float = 3.0) -> List[TextBlock]:
        if not words:
            return []
        ordered = sorted(words, key=lambda word: (float(word["top"]), float(word["x0"])))
        lines: List[List[dict]] = []
        for word in ordered:
            center = (float(word["top"]) + float(word["bottom"])) / 2
            if not lines:
                lines.append([word])
                continue
            previous = lines[-1]
            previous_center = sum(
                (float(item["top"]) + float(item["bottom"])) / 2 for item in previous
            ) / len(previous)
            if abs(center - previous_center) <= tolerance:
                previous.append(word)
            else:
                lines.append([word])

        result: List[TextBlock] = []
        for line in lines:
            line.sort(key=lambda word: float(word["x0"]))
            text = " ".join(str(word["text"]) for word in line).strip()
            if not text:
                continue
            result.append(
                TextBlock(
                    text=text,
                    bbox=(
                        min(float(word["x0"]) for word in line),
                        min(float(word["top"]) for word in line),
                        max(float(word["x1"]) for word in line),
                        max(float(word["bottom"]) for word in line),
                    ),
                )
            )
        return result
