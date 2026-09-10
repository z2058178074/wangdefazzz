from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from app.ui.main_window import MainWindow


def run() -> int:
    if "--smoke-test" in sys.argv:
        import cv2  # noqa: F401
        import onnxruntime  # noqa: F401
        import pdfplumber  # noqa: F401
        import pypdfium2  # noqa: F401

        from app.ocr.engine import OCREngine

        OCREngine()._validate_models()
        return 0
    application = QApplication.instance() or QApplication(sys.argv)
    application.setApplicationName("PDF 转 Word")
    window = MainWindow()
    window.show()
    return application.exec()
