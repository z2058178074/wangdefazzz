from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Optional, Tuple


BBox = Tuple[float, float, float, float]


class ConversionMode(str, Enum):
    TEXT = "文字提取"
    OCR = "OCR"


@dataclass
class TextBlock:
    text: str
    bbox: BBox
    confidence: float = 1.0


@dataclass
class TableCell:
    row: int
    col: int
    bbox: BBox
    text: str = ""
    row_span: int = 1
    col_span: int = 1


@dataclass
class TableData:
    rows: int
    cols: int
    bbox: BBox
    cells: List[TableCell] = field(default_factory=list)


@dataclass
class ImageBlock:
    data: bytes
    bbox: BBox
    extension: str = "png"


@dataclass
class PageContent:
    page_number: int
    width: float
    height: float
    mode: ConversionMode = ConversionMode.TEXT
    text_blocks: List[TextBlock] = field(default_factory=list)
    tables: List[TableData] = field(default_factory=list)
    images: List[ImageBlock] = field(default_factory=list)
    error: str = ""


@dataclass
class ProgressEvent:
    file_path: Path
    file_index: int
    file_count: int
    page_number: int
    page_count: int
    mode: ConversionMode
    percent: int
    message: str = ""


@dataclass
class ConversionResult:
    source_path: Path
    output_path: Optional[Path]
    success: bool
    logs: List[str] = field(default_factory=list)
    error: str = ""
    failed_pages: List[int] = field(default_factory=list)
    cancelled: bool = False
