from pathlib import Path

from docx import Document
from reportlab.pdfgen import canvas

from app.converter import ConversionOptions, PDFConverter
from app.pdf.analyzer import PDFAnalyzer


def test_one_failed_page_does_not_stop_remaining_pages(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "partly-readable.pdf"
    pdf = canvas.Canvas(str(source))
    pdf.drawString(50, 700, "first page")
    pdf.showPage()
    pdf.drawString(50, 700, "second page survives")
    pdf.save()
    original = PDFAnalyzer.analyze_page

    def fail_first_page(self, index, use_ocr=False, preserve_tables=True):
        if index == 0:
            raise ValueError("模拟页面损坏")
        return original(self, index, use_ocr, preserve_tables)

    monkeypatch.setattr(PDFAnalyzer, "analyze_page", fail_first_page)

    result = PDFConverter().convert_file(source, ConversionOptions(enable_ocr=False))

    assert result.success is True
    assert result.failed_pages == [1]
    assert "second page survives" in "\n".join(
        paragraph.text for paragraph in Document(result.output_path).paragraphs
    )
    assert any("第 1 页转换失败，已继续" in message for message in result.logs)
