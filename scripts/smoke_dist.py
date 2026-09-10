from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def check_distribution(path: Path, run_exe: bool = True) -> None:
    path = Path(path)
    exe = path / "PDF转Word.exe"
    dependencies = path / "dependencies"
    manifest_path = path / "models" / "manifest.json"
    if not exe.is_file():
        raise RuntimeError("发行包缺少 PDF转Word.exe")
    if not dependencies.is_dir():
        raise RuntimeError("发行包缺少 dependencies 依赖目录")
    if not manifest_path.is_file():
        raise RuntimeError("发行包缺少 OCR 模型清单")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    missing = [item["filename"] for item in manifest["models"] if not (path / "models" / item["filename"]).is_file()]
    if missing:
        raise RuntimeError(f"发行包缺少 OCR 模型：{'、'.join(missing)}")
    if run_exe:
        completed = subprocess.run([str(exe), "--smoke-test"], timeout=60, check=False)
        if completed.returncode != 0:
            raise RuntimeError(f"程序启动探针失败，退出码：{completed.returncode}")


def main() -> int:
    parser = argparse.ArgumentParser(description="检查 Windows 便携发行包")
    parser.add_argument("path", type=Path)
    parser.add_argument("--no-run", action="store_true")
    args = parser.parse_args()
    check_distribution(args.path, run_exe=not args.no_run)
    print("发行包检查通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
