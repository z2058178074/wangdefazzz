from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

try:
    from scripts.prepare_models import prepare_models
except ModuleNotFoundError:
    from prepare_models import prepare_models


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    if sys.platform != "win32":
        raise RuntimeError("Windows 发行包必须在 Windows 或 GitHub Actions 的 windows-latest 上构建")
    models = ROOT / "models"
    prepare_models(models)
    subprocess.run(
        [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "pdf_to_word.spec"],
        cwd=ROOT,
        check=True,
    )
    distribution = ROOT / "dist" / "PDF转Word-Windows"
    target_models = distribution / "models"
    if target_models.exists():
        shutil.rmtree(target_models)
    shutil.copytree(models, target_models, ignore=shutil.ignore_patterns("README.md"))
    print(f"Windows 便携版已生成：{distribution}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
