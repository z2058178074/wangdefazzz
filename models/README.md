# OCR 模型目录

运行 `python scripts/prepare_models.py` 会从已安装的 RapidOCR 3.9.2 包中复制三份 ONNX 模型到本目录，并按 `manifest.json` 校验 SHA-256。

模型文件不提交 Git；GitHub Actions 在构建 Windows 发行包之前自动准备模型。最终 zip 的 `models/` 目录包含全部模型，程序运行时不会下载任何文件。
