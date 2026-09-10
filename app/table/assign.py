from __future__ import annotations

from copy import deepcopy
from typing import Iterable

from app.models import TableData, TextBlock


def assign_blocks(table: TableData, blocks: Iterable[TextBlock]) -> TableData:
    result = deepcopy(table)
    by_cell = {id(cell): [] for cell in result.cells}
    for block in blocks:
        center_x = (block.bbox[0] + block.bbox[2]) / 2
        center_y = (block.bbox[1] + block.bbox[3]) / 2
        candidates = [
            cell
            for cell in result.cells
            if cell.bbox[0] <= center_x <= cell.bbox[2]
            and cell.bbox[1] <= center_y <= cell.bbox[3]
        ]
        if candidates:
            cell = min(candidates, key=lambda item: (item.bbox[2] - item.bbox[0]) * (item.bbox[3] - item.bbox[1]))
            by_cell[id(cell)].append(block)
    for cell in result.cells:
        ordered = sorted(by_cell[id(cell)], key=lambda item: (item.bbox[1], item.bbox[0]))
        cell.text = "\n".join(block.text for block in ordered).strip()
    return result
