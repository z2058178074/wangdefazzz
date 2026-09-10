from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Optional

from app.models import ConversionResult, PageContent, ProgressEvent
from app.pdf.analyzer import PDFAnalyzer
from app.word.writer import WordWriter


@dataclass(frozen=True)
class ConversionOptions:
    enable_ocr: bool = True
    preserve_tables: bool = True


class PDFConverter:
    def __init__(self, writer: Optional[WordWriter] = None):
        self.writer = writer or WordWriter()

    def convert_file(
        self,
        source_path: Path,
        options: Optional[ConversionOptions] = None,
        progress: Optional[Callable[[ProgressEvent], None]] = None,
        cancel=None,
    ) -> ConversionResult:
        source = Path(source_path)
        options = options or ConversionOptions()
        logs: List[str] = []
        if source.suffix.lower() != ".pdf":
            message = f"所选文件不是 PDF：{source.name}"
            return ConversionResult(source, None, False, [message], message)
        if not source.exists():
            message = f"找不到 PDF 文件：{source}"
            return ConversionResult(source, None, False, [message], message)

        output = source.with_suffix(".docx")
        pages: List[PageContent] = []
        failed_pages: List[int] = []
        try:
            with PDFAnalyzer(source) as analyzer:
                total = analyzer.page_count
                logs.append(f"开始转换：{source.name}，共 {total} 页")
                for index in range(total):
                    try:
                        page = analyzer.analyze_page(index, use_ocr=False)
                        pages.append(page)
                        logs.append(f"第 {index + 1}/{total} 页：文字提取")
                    except Exception as exc:  # page isolation is deliberate
                        failed_pages.append(index + 1)
                        message = str(exc) or exc.__class__.__name__
                        pages.append(PageContent(index + 1, 595, 842, error=message))
                        logs.append(f"第 {index + 1} 页转换失败，已继续：{message}")
                self.writer.write(pages, output)
        except Exception as exc:
            message = f"转换失败：{str(exc) or exc.__class__.__name__}"
            logs.append(message)
            return ConversionResult(source, None, False, logs, message, failed_pages)

        logs.append(f"转换完成：{output.name}")
        return ConversionResult(source, output, True, logs, failed_pages=failed_pages)
