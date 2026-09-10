import json
from pathlib import Path

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
