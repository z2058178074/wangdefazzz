from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_windows_workflow_builds_tests_zips_and_uploads_portable_artifact() -> None:
    workflow = (ROOT / ".github" / "workflows" / "build-windows.yml").read_text(
        encoding="utf-8"
    )
    required = [
        "windows-latest",
        "actions/setup-python",
        "python-version: '3.11'",
        "PYTHONUTF8: '1'",
        "pip install -r requirements-dev.txt",
        "pytest",
        "scripts/prepare_models.py",
        "scripts/build_windows.py",
        "scripts/smoke_dist.py",
        "Compress-Archive",
        "PDF转Word-Windows.zip",
        "actions/upload-artifact",
    ]
    for marker in required:
        assert marker in workflow


def test_readme_explains_offline_windows_use_and_limitations() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for marker in (
        "无需安装 Python",
        "拖拽",
        "RapidOCR",
        "GitHub Actions",
        "PDF转Word-Windows.zip",
        "已知限制",
    ):
        assert marker in readme
