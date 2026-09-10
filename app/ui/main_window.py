from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QThread, Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.converter import ConversionOptions
from app.models import ProgressEvent
from app.ui.drop_area import DropArea
from app.ui.worker import ConversionWorker
from app.utils.cancellation import CancellationToken


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("PDF 转 Word")
        self.resize(780, 720)
        self._thread = None
        self._worker = None
        self._token = None
        self._paths: list[Path] = []
        self._build_ui()
        self._apply_style()

    def _build_ui(self) -> None:
        root = QWidget()
        root.setObjectName("root")
        layout = QVBoxLayout(root)
        layout.setContentsMargins(32, 26, 32, 28)
        layout.setSpacing(14)

        title = QLabel("PDF 转 Word")
        title.setObjectName("title")
        subtitle = QLabel("审计与财务表格离线转换工具")
        subtitle.setObjectName("subtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        self.drop_area = DropArea()
        self.drop_area.files_dropped.connect(self.add_files)
        layout.addWidget(self.drop_area)

        file_buttons = QHBoxLayout()
        choose_one = QPushButton("选择 PDF")
        choose_many = QPushButton("选择多个文件")
        choose_one.clicked.connect(self._choose_one)
        choose_many.clicked.connect(self._choose_many)
        file_buttons.addWidget(choose_one)
        file_buttons.addWidget(choose_many)
        file_buttons.addStretch()
        layout.addLayout(file_buttons)

        self.file_list = QListWidget()
        self.file_list.setMinimumHeight(92)
        layout.addWidget(self.file_list)

        options = QHBoxLayout()
        self.auto_ocr_checkbox = QCheckBox("自动识别扫描件")
        self.auto_ocr_checkbox.setChecked(True)
        self.preserve_tables_checkbox = QCheckBox("保留表格结构")
        self.preserve_tables_checkbox.setChecked(True)
        options.addWidget(self.auto_ocr_checkbox)
        options.addWidget(self.preserve_tables_checkbox)
        options.addStretch()
        layout.addLayout(options)
        layout.addWidget(QLabel("输出位置：原 PDF 文件目录"))

        actions = QHBoxLayout()
        self.start_button = QPushButton("开始转换")
        self.start_button.setObjectName("primaryButton")
        self.start_button.setEnabled(False)
        self.start_button.clicked.connect(self.start_conversion)
        self.cancel_button = QPushButton("取消转换")
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self.cancel_conversion)
        actions.addWidget(self.start_button)
        actions.addWidget(self.cancel_button)
        actions.addStretch()
        layout.addLayout(actions)

        status_frame = QFrame()
        status_frame.setObjectName("statusFrame")
        status_layout = QVBoxLayout(status_frame)
        self.current_file_label = QLabel("当前文件：—")
        self.page_label = QLabel("当前页：— / —")
        self.mode_label = QLabel("转换方式：—")
        self.status_label = QLabel("状态：等待文件")
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("进度：%p%")
        for widget in (
            self.current_file_label,
            self.page_label,
            self.mode_label,
            self.status_label,
            self.progress_bar,
        ):
            status_layout.addWidget(widget)
        layout.addWidget(status_frame)

        layout.addWidget(QLabel("转换日志"))
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMinimumHeight(130)
        layout.addWidget(self.log_view, 1)
        self.setCentralWidget(root)

    def _apply_style(self) -> None:
        self.setStyleSheet(
            """
            QWidget#root { background: #F2F4F7; color: #172033; font-family: "Microsoft YaHei UI", "PingFang SC"; font-size: 13px; }
            QLabel#title { font-size: 27px; font-weight: 700; color: #102A43; }
            QLabel#subtitle { color: #62748A; margin-bottom: 8px; }
            QLabel#dropArea { background: #FFFFFF; border: 2px dashed #7895B2; border-radius: 8px; color: #244A70; font-size: 16px; font-weight: 600; }
            QLabel#dropArea:hover { border-color: #1F5D91; background: #F8FBFE; }
            QListWidget, QPlainTextEdit { background: #FFFFFF; border: 1px solid #D8E0E8; border-radius: 6px; padding: 7px; }
            QFrame#statusFrame { background: #FFFFFF; border: 1px solid #D8E0E8; border-radius: 7px; }
            QPushButton { min-height: 34px; padding: 0 16px; border: 1px solid #AFC0D0; border-radius: 5px; background: #FFFFFF; }
            QPushButton:hover { background: #EAF1F7; }
            QPushButton:disabled { color: #9AA7B4; background: #EBEFF3; }
            QPushButton#primaryButton { background: #1F5D91; color: white; border-color: #1F5D91; font-weight: 600; }
            QPushButton#primaryButton:hover { background: #174A74; }
            QProgressBar { min-height: 18px; border: 1px solid #CAD5DF; border-radius: 4px; background: #E8EDF2; text-align: center; font-family: Consolas; }
            QProgressBar::chunk { background: #2E75B6; border-radius: 3px; }
            """
        )

    def add_files(self, paths) -> None:
        added = 0
        known = {str(path.resolve()).casefold() for path in self._paths}
        for raw in paths:
            path = Path(raw)
            key = str(path.resolve()).casefold()
            if path.suffix.lower() != ".pdf" or key in known:
                continue
            self._paths.append(path)
            known.add(key)
            self.file_list.addItem(str(path))
            added += 1
        if added:
            self.log_view.appendPlainText(f"已添加 {added} 个 PDF")
        self.start_button.setEnabled(bool(self._paths) and self._thread is None)

    def _choose_one(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "选择 PDF", "", "PDF 文件 (*.pdf)")
        if path:
            self.add_files([path])

    def _choose_many(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(self, "选择多个 PDF", "", "PDF 文件 (*.pdf)")
        self.add_files(paths)

    def start_conversion(self) -> None:
        if not self._paths or self._thread is not None:
            return
        self._token = CancellationToken()
        options = ConversionOptions(
            enable_ocr=self.auto_ocr_checkbox.isChecked(),
            preserve_tables=self.preserve_tables_checkbox.isChecked(),
        )
        self._thread = QThread(self)
        self._worker = ConversionWorker(self._paths, options, self._token)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self._on_progress)
        self._worker.log.connect(self.log_view.appendPlainText)
        self._worker.file_finished.connect(self._on_file_finished)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.finished.connect(self._thread.quit)
        self._thread.finished.connect(self._thread.deleteLater)
        self.start_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.status_label.setText("状态：正在转换")
        self.log_view.appendPlainText(f"开始批量转换，共 {len(self._paths)} 个文件")
        self._thread.start()

    def cancel_conversion(self) -> None:
        if self._token is not None:
            self._token.cancel()
            self.cancel_button.setEnabled(False)
            self.status_label.setText("状态：正在取消…")
            self.log_view.appendPlainText("已请求取消，将在当前页面处理结束后停止")

    def _on_progress(self, event: ProgressEvent) -> None:
        self.current_file_label.setText(
            f"当前文件：{event.file_path.name}（{event.file_index}/{event.file_count}）"
        )
        self.page_label.setText(f"当前页：{event.page_number} / {event.page_count}")
        self.mode_label.setText(f"转换方式：{event.mode.value}")
        self.progress_bar.setValue(event.percent)

    def _on_file_finished(self, result) -> None:
        if result.cancelled:
            self.status_label.setText("状态：已取消")
        elif result.success:
            self.status_label.setText(f"状态：成功 - {result.output_path.name}")
        else:
            self.status_label.setText(f"状态：失败 - {result.source_path.name}")

    def _on_worker_finished(self, cancelled: bool) -> None:
        if not cancelled:
            self.progress_bar.setValue(100)
            self.status_label.setText("状态：批量转换完成")
        self.cancel_button.setEnabled(False)
        self._worker = None
        self._thread = None
        self._token = None
        self.start_button.setEnabled(bool(self._paths))

    def closeEvent(self, event) -> None:
        if self._token is not None:
            self._token.cancel()
        if self._thread is not None and self._thread.isRunning():
            self._thread.quit()
            self._thread.wait()
        event.accept()
