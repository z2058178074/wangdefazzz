import json
import subprocess
import sys
from pathlib import Path

import pytest

from app.ocr.engine import OCREngine
from scripts.prepare_models import prepare_models


ROOT = Path(__file__).resolve().parents[1]


def test_model_manifest_covers_every_runtime_model() -> None:
    manifest = json.loads((ROOT / "models" / "manifest.json").read_text(encoding="utf-8"))
    by_name = {item["filename"]: item for item in manifest["models"]}
    assert set(by_name) == set(OCREngine.REQUIRED_FILES)
    for item in by_name.values():
        assert len(item["sha256"]) == 64
        assert item["source"].startswith("https://")


def test_prepare_models_copies_and_verifies_installed_rapidocr_models(tmp_path: Path) -> None:
    copied = prepare_models(tmp_path)
    assert {path.name for path in copied} == set(OCREngine.REQUIRED_FILES)
    assert all(path.stat().st_size > 100_000 for path in copied)


def test_pyinstaller_spec_describes_portable_windows_folder() -> None:
    spec = (ROOT / "pdf_to_word.spec").read_text(encoding="utf-8")
    assert "PDF转Word" in spec
    assert "collect_all('rapidocr')" in spec
    assert "collect_dynamic_libs('onnxruntime')" in spec
    assert "dependencies" in spec
    assert "models" in spec


def test_distribution_smoke_script_checks_exe_models_and_dependencies() -> None:
    script = (ROOT / "scripts" / "smoke_dist.py").read_text(encoding="utf-8")
    assert "PDF转Word.exe" in script
    assert "OCR 模型" in script
    assert "dependencies" in script


@pytest.mark.skipif(sys.platform == "win32", reason="Windows 上由 CI 的真实构建步骤验证")
def test_windows_build_script_rejects_non_windows_host() -> None:
    completed = subprocess.run(
        [sys.executable, "scripts/build_windows.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    output = completed.stdout + completed.stderr
    assert completed.returncode != 0
    assert "Windows 发行包必须" in output
    assert "ModuleNotFoundError" not in output


def test_frozen_smoke_probe_initializes_ocr_models() -> None:
    source = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
    assert "OCREngine().recognize" in source


def test_runtime_uses_qt_essentials_without_large_addons_bundle() -> None:
    requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()
    assert any(line.startswith("PySide6-Essentials") for line in requirements)
    assert not any(line.startswith("PySide6>") or line.startswith("PySide6=") for line in requirements)
