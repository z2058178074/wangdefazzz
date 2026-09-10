from pathlib import Path

import numpy as np
import pytest
from PIL import Image
from docx import Document
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from app.converter import ConversionOptions, PDFConverter
from app.models import ConversionMode
from app.models import TextBlock
from app.ocr.engine import OCREngine, OCRModelError
from app.pdf.classifier import PageStats, classify_page
from app.pdf.renderer import PDFRenderer


def test_page_classifier_uses_text_when_character_layer_is_useful() -> None:
    stats = PageStats(char_count=86, text_area_ratio=0.035, image_area_ratio=0.0)
    assert classify_page(stats) is ConversionMode.TEXT


def test_page_classifier_uses_ocr_for_scan_or_empty_text_layer() -> None:
    scan = PageStats(char_count=0, text_area_ratio=0.0, image_area_ratio=0.96)
    broken_layer = PageStats(char_count=5, text_area_ratio=0.0001, image_area_ratio=0.8)
    assert classify_page(scan) is ConversionMode.OCR
    assert classify_page(broken_layer) is ConversionMode.OCR


def test_pdfium_renderer_returns_rgb_array(tmp_path: Path) -> None:
    source = tmp_path / "render.pdf"
    pdf = canvas.Canvas(str(source), pagesize=(200, 100))
    pdf.drawString(20, 50, "render me")
    pdf.save()

    with PDFRenderer(source) as renderer:
        image = renderer.render_page(0, dpi=144)

    assert image.dtype == np.uint8
    assert image.ndim == 3
    assert image.shape[2] == 3
    assert 190 <= image.shape[0] <= 210
    assert 390 <= image.shape[1] <= 410


def test_ocr_refuses_to_download_missing_models(tmp_path: Path) -> None:
    with pytest.raises(OCRModelError, match="OCR 模型不完整"):
        OCREngine(model_dir=tmp_path).recognize(np.zeros((50, 100, 3), dtype=np.uint8))


def test_ocr_output_is_adapted_to_text_blocks(tmp_path: Path) -> None:
    for name in OCREngine.REQUIRED_FILES:
        (tmp_path / name).write_bytes(b"model")

    class FakeOutput:
        boxes = np.array([[[10, 10], [80, 10], [80, 30], [10, 30]]])
        txts = ("营业收入 123.45",)
        scores = (0.98,)

    engine = OCREngine(model_dir=tmp_path, engine_factory=lambda **_: lambda image: FakeOutput())
    blocks = engine.recognize(np.zeros((50, 100, 3), dtype=np.uint8))

    assert blocks[0].text == "营业收入 123.45"
    assert blocks[0].bbox == (10.0, 10.0, 80.0, 30.0)
    assert blocks[0].confidence == pytest.approx(0.98)


def test_converter_automatically_uses_ocr_for_scanned_page(tmp_path: Path) -> None:
    source = tmp_path / "scanned-statement.pdf"
    image = Image.new("RGB", (500, 300), "white")
    pdf = canvas.Canvas(str(source), pagesize=(500, 300))
    pdf.drawImage(ImageReader(image), 0, 0, width=500, height=300)
    pdf.save()

    class FakeOCR:
        called = 0

        def recognize(self, rendered):
            self.called += 1
            assert rendered.shape[0] > 300
            return [TextBlock("扫描财务表 2026", (20, 20, 220, 50), 0.99)]

    ocr = FakeOCR()
    events = []
    result = PDFConverter(ocr_engine=ocr).convert_file(
        source,
        ConversionOptions(enable_ocr=True),
        progress=events.append,
    )

    assert result.success
    assert ocr.called == 1
    assert events[-1].mode is ConversionMode.OCR
    assert "扫描财务表 2026" in "\n".join(p.text for p in Document(result.output_path).paragraphs)
