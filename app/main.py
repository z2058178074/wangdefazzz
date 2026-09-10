from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from app.ui.main_window import MainWindow


def run() -> int:
    application = QApplication.instance() or QApplication(sys.argv)
    application.setApplicationName("PDF 转 Word")
    window = MainWindow()
    window.show()
    return application.exec()
