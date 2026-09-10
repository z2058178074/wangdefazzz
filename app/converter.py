from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Optional

from app.models import (
    ConversionMode,
    ConversionResult,
    PageContent,
    ProgressEvent,
    TableCell,
    TableData,
    TextBlock,
)
from app.ocr.engine import OCREngine
from app.pdf.analyzer import PDFAnalyzer
from app.pdf.classifier import classify_page
from app.pdf.renderer import PDFRenderer
from app.table.assign import assign_blocks
from app.table.raster import RasterGridDetector
from app.word.writer import WordWriter


@dataclass(frozen=True)
class ConversionOptions:
    enable_ocr: bool = True
    preserve_tables: bool = True


class PDFConverter:
    def __init__(
        self,
        writer: Optional[WordWriter] = None,
        ocr_engine: Optional[OCREngine] = None,
    ):
        self.writer = writer or WordWriter()
        self.ocr_engine = ocr_engine

    @staticmethod
    def _scale_table(table: TableData, scale_x: float, scale_y: float) -> TableData:
        def scale(bbox):
            return (
                bbox[0] * scale_x,
                bbox[1] * scale_y,
                bbox[2] * scale_x,
                bbox[3] * scale_y,
            )

        return TableData(
            table.rows,
            table.cols,
            scale(table.bbox),
            [
                TableCell(
                    cell.row,
                    cell.col,
                    scale(cell.bbox),
                    cell.text,
                    cell.row_span,
                    cell.col_span,
                )
                for cell in table.cells
            ],
        )

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
        if cancel is not None and cancel.is_cancelled():
            message = "转换已取消"
            return ConversionResult(source, None, False, [message], message, cancelled=True)
        try:
            with PDFAnalyzer(source) as analyzer, PDFRenderer(source) as renderer:
                total = analyzer.page_count
                logs.append(f"开始转换：{source.name}，共 {total} 页")
                for index in range(total):
                    if cancel is not None and cancel.is_cancelled():
                        message = "转换已取消"
                        logs.append(message)
                        return ConversionResult(
                            source,
                            None,
                            False,
                            logs,
                            message,
                            failed_pages,
                            cancelled=True,
                        )
                    try:
                        mode = (
                            classify_page(analyzer.page_stats(index))
                            if options.enable_ocr
                            else ConversionMode.TEXT
                        )
                        if mode is ConversionMode.OCR:
                            text_page = analyzer.analyze_page(
                                index,
                                use_ocr=False,
                                preserve_tables=False,
                            )
                            image = renderer.render_page(index, dpi=220)
                            engine = self.ocr_engine or OCREngine()
                            detected = engine.recognize(image)
                            scale_x = text_page.width / image.shape[1]
                            scale_y = text_page.height / image.shape[0]
                            tables = []
                            if options.preserve_tables:
                                raster_table = RasterGridDetector().detect(image)
                                if raster_table is not None:
                                    assigned = assign_blocks(raster_table, detected)
                                    tables.append(self._scale_table(assigned, scale_x, scale_y))
                                    detected = [
                                        block
                                        for block in detected
                                        if not (
                                            raster_table.bbox[0]
                                            <= (block.bbox[0] + block.bbox[2]) / 2
                                            <= raster_table.bbox[2]
                                            and raster_table.bbox[1]
                                            <= (block.bbox[1] + block.bbox[3]) / 2
                                            <= raster_table.bbox[3]
                                        )
                                    ]
                            detected = [
                                TextBlock(
                                    block.text,
                                    (
                                        block.bbox[0] * scale_x,
                                        block.bbox[1] * scale_y,
                                        block.bbox[2] * scale_x,
                                        block.bbox[3] * scale_y,
                                    ),
                                    block.confidence,
                                )
                                for block in detected
                            ]
                            page = PageContent(
                                index + 1,
                                text_page.width,
                                text_page.height,
                                mode=mode,
                                text_blocks=detected,
                                tables=tables,
                            )
                        else:
                            page = analyzer.analyze_page(
                                index,
                                use_ocr=False,
                                preserve_tables=options.preserve_tables,
                            )
                            page.mode = mode
                        pages.append(page)
                        logs.append(f"第 {index + 1}/{total} 页：{mode.value}")
                        if progress is not None:
                            progress(
                                ProgressEvent(
                                    file_path=source,
                                    file_index=1,
                                    file_count=1,
                                    page_number=index + 1,
                                    page_count=total,
                                    mode=mode,
                                    percent=round((index + 1) / max(total, 1) * 100),
                                )
                            )
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
