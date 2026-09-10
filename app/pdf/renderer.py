from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np
import pypdfium2 as pdfium


class PDFRenderer:
    def __init__(self, path: Path):
        self.path = Path(path)
        self._document: Optional[pdfium.PdfDocument] = None

    def __enter__(self) -> "PDFRenderer":
        self._document = pdfium.PdfDocument(str(self.path))
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        if self._document is not None:
            self._document.close()
            self._document = None

    @property
    def page_count(self) -> int:
        if self._document is None:
            raise RuntimeError("PDF 尚未打开")
        return len(self._document)

    def render_page(self, index: int, dpi: int = 220) -> np.ndarray:
        if self._document is None:
            raise RuntimeError("PDF 尚未打开")
        page = self._document[index]
        bitmap = page.render(scale=float(dpi) / 72.0, rev_byteorder=True)
        array = bitmap.to_numpy()
        if array.ndim == 2:
            array = np.repeat(array[:, :, None], 3, axis=2)
        if array.shape[2] == 4:
            array = array[:, :, :3]
        return np.ascontiguousarray(array, dtype=np.uint8)
