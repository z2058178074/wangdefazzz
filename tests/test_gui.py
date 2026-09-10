from pathlib import Path

from app.ui.main_window import MainWindow


def test_main_window_has_chinese_controls_and_defaults(qtbot) -> None:
    window = MainWindow()
    qtbot.addWidget(window)

    assert window.windowTitle() == "PDF 转 Word"
    assert window.auto_ocr_checkbox.isChecked()
    assert window.preserve_tables_checkbox.isChecked()
    assert window.start_button.text() == "开始转换"
    assert window.cancel_button.text() == "取消转换"
    assert window.start_button.isEnabled() is False


def test_add_files_filters_non_pdf_and_deduplicates(tmp_path: Path, qtbot) -> None:
    first = tmp_path / "审计底稿.pdf"
    second = tmp_path / "应收账款明细表.PDF"
    ignored = tmp_path / "说明.txt"
    for path in (first, second, ignored):
        path.write_bytes(b"fixture")
    window = MainWindow()
    qtbot.addWidget(window)

    window.add_files([str(first), str(first), str(ignored), str(second)])

    assert window.file_list.count() == 2
    assert window.start_button.isEnabled() is True
    assert "已添加 2 个 PDF" in window.log_view.toPlainText()


def test_drop_area_exposes_instruction(qtbot) -> None:
    window = MainWindow()
    qtbot.addWidget(window)
    assert "拖入 PDF 文件" in window.drop_area.text()
