from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Iterable

from PySide6.QtCore import QObject, Signal, Slot

from app.converter import ConversionOptions, PDFConverter
from app.utils.cancellation import CancellationToken


class ConversionWorker(QObject):
    progress = Signal(object)
    log = Signal(str)
    file_finished = Signal(object)
    finished = Signal(bool)

    def __init__(
        self,
        paths: Iterable[Path],
        options: ConversionOptions,
        token: CancellationToken,
        converter: PDFConverter | None = None,
    ):
        super().__init__()
        self.paths = [Path(path) for path in paths]
        self.options = options
        self.token = token
        self.converter = converter or PDFConverter()

    @Slot()
    def run(self) -> None:
        cancelled = False
        file_count = len(self.paths)
        for file_index, path in enumerate(self.paths, start=1):
            if self.token.is_cancelled():
                cancelled = True
                break

            def emit_progress(event, current=file_index):
                overall = round(
                    ((current - 1) + event.page_number / max(event.page_count, 1))
                    / max(file_count, 1)
                    * 100
                )
                self.progress.emit(
                    replace(
                        event,
                        file_index=current,
                        file_count=file_count,
                        percent=overall,
                    )
                )

            result = self.converter.convert_file(
                path,
                self.options,
                progress=emit_progress,
                cancel=self.token,
            )
            for message in result.logs:
                self.log.emit(message)
            self.file_finished.emit(result)
            if result.cancelled:
                cancelled = True
                break
        self.finished.emit(cancelled)
