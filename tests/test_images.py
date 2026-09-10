from pathlib import Path

from PIL import Image
from docx import Document
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from app.converter import PDFConverter


def test_embedded_figure_is_inserted_as_word_image(tmp_path: Path) -> None:
    source = tmp_path / "working-paper-with-chart.pdf"
    figure = Image.new("RGB", (160, 90), (41, 112, 171))
    pdf = canvas.Canvas(str(source), pagesize=(500, 400))
    pdf.drawString(40, 350, "Audit chart and supporting documentation for revenue testing")
    pdf.drawString(40, 330, "This page has a valid searchable text layer.")
    pdf.drawImage(ImageReader(figure), 40, 180, width=160, height=90)
    pdf.save()

    result = PDFConverter().convert_file(source)

    assert result.success
    doc = Document(result.output_path)
    assert len(doc.inline_shapes) == 1
    assert "Audit chart" in "\n".join(paragraph.text for paragraph in doc.paragraphs)
