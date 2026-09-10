from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLabel


class DropArea(QLabel):
    files_dropped = Signal(list)

    def __init__(self, parent=None):
        super().__init__("拖入 PDF 文件\n支持一次拖入多个文件", parent)
        self.setAcceptDrops(True)
        self.setObjectName("dropArea")
        self.setMinimumHeight(126)
        self.setAlignment(__import__("PySide6.QtCore", fromlist=["Qt"]).Qt.AlignmentFlag.AlignCenter)

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls() and any(
            url.toLocalFile().lower().endswith(".pdf") for url in event.mimeData().urls()
        ):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event) -> None:
        paths = [url.toLocalFile() for url in event.mimeData().urls() if url.isLocalFile()]
        self.files_dropped.emit(paths)
        event.acceptProposedAction()
