from pathlib import Path

from reportlab.pdfgen import canvas

from app.converter import PDFConverter
from app.utils.cancellation import CancellationToken


def test_cancellation_token_is_thread_safe() -> None:
    token = CancellationToken()
    assert token.is_cancelled() is False
    token.cancel()
    assert token.is_cancelled() is True


def test_cancelled_conversion_does_not_write_output(tmp_path: Path) -> None:
    source = tmp_path / "cancel-me.pdf"
    pdf = canvas.Canvas(str(source))
    pdf.drawString(50, 700, "page one")
    pdf.showPage()
    pdf.drawString(50, 700, "page two")
    pdf.save()
    token = CancellationToken()
    token.cancel()

    result = PDFConverter().convert_file(source, cancel=token)

    assert result.cancelled is True
    assert result.success is False
    assert not source.with_suffix(".docx").exists()
    assert any("已取消" in message for message in result.logs)
