from pathlib import Path
from zipfile import ZipFile

from docx import Document
from reportlab.pdfgen import canvas

from app.converter import ConversionOptions, PDFConverter


def make_two_page_pdf(path: Path) -> None:
    pdf = canvas.Canvas(str(path), pagesize=(595, 842))
    pdf.drawString(72, 770, "Audit working paper 2026")
    pdf.drawString(72, 740, "Revenue: 1,234,567.89")
    pdf.showPage()
    pdf.drawString(72, 770, "Accounts receivable details")
    pdf.save()


def test_converts_text_pdf_to_same_directory_docx(tmp_path: Path) -> None:
    source = tmp_path / "audit-sample.pdf"
    make_two_page_pdf(source)

    result = PDFConverter().convert_file(source, ConversionOptions(enable_ocr=False))

    assert result.success is True
    assert result.output_path == source.with_suffix(".docx")
    assert result.output_path.exists()
    doc = Document(result.output_path)
    text = "\n".join(p.text for p in doc.paragraphs)
    assert "Audit working paper 2026" in text
    assert "Revenue: 1,234,567.89" in text
    assert "Accounts receivable details" in text

    with ZipFile(result.output_path) as package:
        document_xml = package.read("word/document.xml").decode("utf-8")
    assert 'w:type="page"' in document_xml


def test_rejects_non_pdf_with_chinese_error(tmp_path: Path) -> None:
    source = tmp_path / "notes.txt"
    source.write_text("not a pdf", encoding="utf-8")

    result = PDFConverter().convert_file(source)

    assert result.success is False
    assert "PDF" in result.error
    assert any("不是 PDF" in message for message in result.logs)
