from __future__ import annotations

from pathlib import Path
from typing import Iterable

from docx import Document
from docx.enum.section import WD_SECTION_START
from docx.shared import Pt

from app.models import PageContent


class WordWriter:
    """Write normalized page content to an editable DOCX."""

    def write(self, pages: Iterable[PageContent], output_path: Path) -> Path:
        page_list = list(pages)
        document = Document()
        normal = document.styles["Normal"]
        normal.font.name = "Microsoft YaHei"
        normal.font.size = Pt(10.5)

        for page_index, page in enumerate(page_list):
            for block in sorted(page.text_blocks, key=lambda item: (item.bbox[1], item.bbox[0])):
                paragraph = document.add_paragraph(block.text)
                paragraph.paragraph_format.space_after = Pt(2)
            if page.error:
                document.add_paragraph(f"[第 {page.page_number} 页转换失败：{page.error}]")
            if page_index < len(page_list) - 1:
                document.add_page_break()

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        document.save(output_path)
        return output_path
