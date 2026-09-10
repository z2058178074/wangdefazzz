# PDF 转 Word

一个面向 Windows 学校电脑的离线 PDF 转 Word 桌面工具，重点处理审计底稿、财务报表、明细表和控制测试表。Windows 便携版无需安装 Python、开发工具或管理员权限，第一次启动也不联网下载 OCR 模型。

## 功能

- 简体中文图形界面。
- 支持拖拽 PDF、选择单个 PDF 和一次选择多个 PDF。
- 输出到原 PDF 目录，文件名保持不变，扩展名改为 `.docx`。
- 按页自动选择文字提取或 RapidOCR 离线 OCR。
- 支持中文、英文和数字混排。
- 文字型表格优先读取 PDF 矢量线框；扫描表格使用 OpenCV 恢复网格。
- Word 中生成可编辑表格，并尽量保留行列、文字、合并单元格和边框。
- 表格外段落按页面坐标排序；各源页面之间保留分页。
- 显示当前文件、页码、转换方式、总进度、成功/失败状态和中文日志。
- 单页转换失败会记录错误并继续；支持取消，关闭窗口时会结束工作线程。

## Windows 便携版使用方法

仓库内置 GitHub Actions 工作流，会在 `windows-latest` 上测试并构建便携版。

1. 在 GitHub 仓库打开 **Actions**。
2. 选择“构建 Windows 便携版”并运行，或在 `main`/`master` 分支提交代码后等待自动构建。
3. 在该次运行的 **Artifacts** 区域下载 `PDF转Word-Windows`。
4. 解压 `PDF转Word-Windows.zip`，保持目录结构不变。
5. 双击 `PDF转Word-Windows/PDF转Word.exe`。
6. 拖入或选择 PDF，点击“开始转换”。

发行目录结构：

```text
PDF转Word-Windows/
├── PDF转Word.exe
├── models/
│   ├── manifest.json
│   ├── PP-OCRv6_det_small.onnx
│   ├── PP-OCRv6_rec_small.onnx
│   └── ch_ppocr_mobile_v2.0_cls_mobile.onnx
└── dependencies/
    └── Python、Qt、PDFium、ONNX Runtime 等运行依赖
```

不要只复制 exe。`models` 和 `dependencies` 必须与 exe 一起保留。程序无需安装 Python、Codex 或 VS Code，也无需联网。

## 本地开发

推荐 Python 3.11：

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python scripts\prepare_models.py models
python main.py
```

macOS 或 Linux 可将激活命令替换为：

```bash
source .venv/bin/activate
```

## 测试

```bash
python -m pytest -q
python -m compileall app main.py scripts
```

测试会程序化生成下列资料，不依赖私有文件：

- 两页文字型审计底稿。
- 营业收入审定表风格的矢量表格。
- 应收账款明细风格的中文数字单元格。
- 带合并表头的表格。
- 扫描版财务网格。
- 混合文字层与扫描页。
- 单页失败、整批继续和取消场景。

## Windows 本地构建

只能在 Windows 上生成 Windows exe：

```powershell
python -m pip install -r requirements-dev.txt
python scripts\build_windows.py
python scripts\smoke_dist.py "dist\PDF转Word-Windows"
Compress-Archive -Path "dist\PDF转Word-Windows" -DestinationPath "PDF转Word-Windows.zip" -Force
```

`scripts/build_windows.py` 会执行以下动作：

1. 从固定版本 RapidOCR 安装包复制三个模型。
2. 按 `models/manifest.json` 校验 SHA-256。
3. 使用 PyInstaller onedir 模式构建。
4. 将 OCR 模型复制到发行目录顶层的 `models/`。

## 项目结构

```text
app/
├── main.py
├── converter.py
├── models.py
├── ui/       # Qt 界面、拖拽和工作线程
├── pdf/      # 页面分析、分类和 PDFium 渲染
├── ocr/      # RapidOCR 离线适配
├── table/    # 矢量/扫描网格及文字归格
├── word/     # DOCX 段落和原生表格
└── utils/    # 资源路径和取消令牌
models/       # 模型清单；ONNX 文件由构建脚本准备
scripts/      # 模型、构建和发行检查脚本
tests/        # 单元与集成测试
.github/workflows/build-windows.yml
pdf_to_word.spec
```

## 转换策略

每一页先检查有效字符数、文字面积和图片覆盖率。有效文字层足够时直接提取，避免 OCR 改错数字；文字层为空或质量不足时，以 220 DPI 渲染并调用本地 RapidOCR。扫描表格先通过形态学方法提取横纵线，再按 OCR 文字框中心坐标归入单元格。缺失的内部边线用于保守推断合并单元格。

## 已知限制

- PDF 到 Word 不存在通用的像素级无损转换，复杂底稿仍可能需要少量人工调整。
- 无边框表格、极低清晰度扫描、旋转文字、跨页合并表格和特别复杂的多级表头可能无法完整恢复。
- 当前按单页建立表格，不自动把跨页表格连接成一个 Word 表格。
- 密码保护或损坏到无法打开的 PDF 会作为文件级失败处理。
- OCR 会尽量保留数字，但关键审计金额仍应与原 PDF 复核。

项目不会用整页截图代替成功的表格转换。无法可靠恢复的页面会在日志和 DOCX 中留下中文失败标记，其他页面继续处理。

## 许可证说明

应用代码可按仓库许可证使用。RapidOCR、ONNX Runtime、PDFium、Qt、OpenCV、pdfplumber 和 python-docx 各自遵循其上游许可证；发布前请根据学校或组织要求保留第三方许可证文件。
