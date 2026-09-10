from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from importlib.util import find_spec
from pathlib import Path
from typing import List, Optional


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "models" / "manifest.json"


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def installed_model_dir() -> Path:
    spec = find_spec("rapidocr")
    if spec is None or spec.origin is None:
        raise RuntimeError("未安装 RapidOCR，无法准备离线 OCR 模型")
    return Path(spec.origin).parent / "models"


def prepare_models(destination: Path, source_dir: Optional[Path] = None) -> List[Path]:
    destination = Path(destination)
    source_dir = Path(source_dir) if source_dir else installed_model_dir()
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    destination.mkdir(parents=True, exist_ok=True)
    copied: List[Path] = []
    for item in manifest["models"]:
        source = source_dir / item["filename"]
        if not source.is_file():
            raise RuntimeError(f"RapidOCR 安装包缺少模型：{item['filename']}")
        if file_sha256(source) != item["sha256"]:
            raise RuntimeError(f"OCR 模型校验失败：{item['filename']}")
        target = destination / item["filename"]
        if source.resolve() != target.resolve():
            shutil.copy2(source, target)
        if file_sha256(target) != item["sha256"]:
            raise RuntimeError(f"复制后的 OCR 模型校验失败：{item['filename']}")
        copied.append(target)
    return copied


def main() -> int:
    parser = argparse.ArgumentParser(description="准备并校验 RapidOCR 离线模型")
    parser.add_argument("destination", nargs="?", type=Path, default=ROOT / "models")
    args = parser.parse_args()
    paths = prepare_models(args.destination)
    print(f"已准备 {len(paths)} 个 OCR 模型：{args.destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
