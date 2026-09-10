# PDF 转 Word Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建可离线运行、可批量转换且重点恢复可编辑财务表格的 Windows PDF 转 Word 桌面工具。

**Architecture:** PDF、OCR、表格、Word 和 GUI 通过数据模型与回调接口解耦。转换器逐文件逐页编排并隔离错误，GUI 只通过 Qt 信号消费进度。

**Tech Stack:** Python 3.11、PySide6、pypdfium2、pdfplumber、RapidOCR、ONNX Runtime、OpenCV、python-docx、pytest、PyInstaller。

## Global Constraints

- 所有运行时提示使用简体中文。
- Windows 首次启动不得联网下载模型。
- 单页失败不得中止整批任务。
- 输出必须位于原 PDF 目录并使用同名 `.docx`。
- 表格使用 Word 原生表格；不得把整页截图作为转换结果。
- 关闭程序后不得残留线程或后台进程。

---

### Task 1: 最小文字 PDF 转换

**Files:** `app/models.py`, `app/pdf/analyzer.py`, `app/word/writer.py`, `app/converter.py`, `tests/test_text_conversion.py`

**Interfaces:** `PDFAnalyzer.analyze_page(index, use_ocr=False) -> PageContent`; `WordWriter.write(pages, output_path)`; `PDFConverter.convert_file(path, options, progress, cancel) -> ConversionResult`。

- [ ] 写入一个由 reportlab 生成的两页文字 PDF 测试，断言输出同名 DOCX、包含两页文字和分页符。
- [ ] 运行 `pytest tests/test_text_conversion.py -q`，确认因缺少实现而失败。
- [ ] 实现最小数据模型、文字提取、阅读顺序、DOCX 写出和同名输出规则。
- [ ] 再次运行测试并确认通过，提交 `feat: add text pdf conversion core`。

### Task 2: 自动分类与离线 OCR

**Files:** `app/pdf/classifier.py`, `app/pdf/renderer.py`, `app/ocr/engine.py`, `app/utils/resources.py`, `models/manifest.json`, `tests/test_ocr_pipeline.py`

**Interfaces:** `classify_page(stats) -> ConversionMode`; `PDFRenderer.render_page(index, dpi) -> ndarray`; `OCREngine.recognize(image) -> list[TextBlock]`。OCR 引擎允许依赖注入，以真实图像和确定性假引擎分别验证适配层与编排。

- [ ] 写入扫描页和混合页测试，断言低文字密度页选择 OCR、文字页不调用 OCR、模型缺失返回中文错误。
- [ ] 运行目标测试并确认预期失败。
- [ ] 实现 PDFium 渲染、阈值分类、RapidOCR 延迟初始化、本地模型路径和结果适配。
- [ ] 运行 OCR 与第一阶段测试并提交 `feat: add offline page ocr`。

### Task 3: 表格结构恢复

**Files:** `app/table/grid.py`, `app/table/vector.py`, `app/table/raster.py`, `app/table/assign.py`, `app/word/tables.py`, `tests/test_tables.py`, `tests/test_table_conversion.py`

**Interfaces:** `GridDetector.from_lines(lines, size) -> TableData`; `RasterGridDetector.detect(image) -> TableData`; `assign_blocks(table, blocks) -> TableData`; `add_table(document, table)`。

- [ ] 写入规则网格、缺失内部边线、中文数字混排和扫描表格测试，断言行列、文字分配、边框及横纵合并。
- [ ] 运行表格测试并确认因实现缺失而失败。
- [ ] 实现坐标聚类、网格单元格、合并推断、OpenCV 线条检测、文字归格和 OOXML 边框。
- [ ] 运行全部核心测试并提交 `feat: recover editable financial tables`。

### Task 4: 简体中文 GUI 与取消

**Files:** `app/ui/main_window.py`, `app/ui/drop_area.py`, `app/ui/worker.py`, `app/main.py`, `main.py`, `tests/test_gui.py`, `tests/test_cancellation.py`

**Interfaces:** `MainWindow.add_files(paths)`；`ConversionWorker.run()` 发出 `progress`, `log`, `file_finished`, `finished` 信号；`CancellationToken.cancel()`。

- [ ] 写入 offscreen GUI 测试，断言只接收 PDF、去重、多选、开始/取消按钮状态和中文状态。
- [ ] 运行 GUI 测试并确认预期失败。
- [ ] 实现审计工作台风格窗口、拖拽、多文件列表、后台工作对象、进度和关闭清理。
- [ ] 运行 GUI、取消和核心测试并提交 `feat: add chinese desktop interface`。

### Task 5: Windows 便携构建

**Files:** `pdf_to_word.spec`, `scripts/prepare_models.py`, `scripts/smoke_dist.py`, `requirements.txt`, `requirements-dev.txt`, `assets/app.ico`, `tests/test_packaging.py`

**Interfaces:** `prepare_models(destination) -> list[Path]`; `smoke_dist(path) -> int`；PyInstaller 产出 `dist/PDF转Word-Windows/PDF转Word.exe`。

- [ ] 写入模型清单、spec 数据收集和发行结构测试，确认初始失败。
- [ ] 实现模型复制及哈希校验、PyInstaller hooks/spec 和无 GUI 启动探针。
- [ ] 运行打包静态测试与 macOS spec 构建验证，提交 `build: add portable windows packaging`。

### Task 6: CI、文档与最终验证

**Files:** `.github/workflows/build-windows.yml`, `README.md`, `.gitignore`, `tests/fixtures/README.md`

**Interfaces:** workflow 在 `windows-latest` 安装 Python 3.11、依赖、准备模型、测试、构建、冒烟检查、压缩并上传 artifact。

- [ ] 写入 workflow 结构测试，断言 runner、测试、模型、PyInstaller、zip 和 artifact 步骤存在。
- [ ] 实现 GitHub Actions 和中文 README，记录离线运行、开发、测试、构建和限制。
- [ ] 运行 `pytest -q`、`python -m compileall app main.py scripts` 和依赖导入检查。
- [ ] 检查需求覆盖及工作树差异，提交 `ci: build portable windows artifact`。
