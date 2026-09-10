from __future__ import annotations

from collections import defaultdict
from typing import Iterable, List, Optional, Sequence, Tuple

from app.models import TableCell, TableData


Line = Tuple[float, float, float, float]


def _cluster(values: Iterable[float], tolerance: float) -> List[float]:
    ordered = sorted(float(value) for value in values)
    groups: List[List[float]] = []
    for value in ordered:
        if groups and abs(value - sum(groups[-1]) / len(groups[-1])) <= tolerance:
            groups[-1].append(value)
        else:
            groups.append([value])
    return [sum(group) / len(group) for group in groups]


class _DisjointSet:
    def __init__(self, size: int):
        self.parent = list(range(size))

    def find(self, item: int) -> int:
        while self.parent[item] != item:
            self.parent[item] = self.parent[self.parent[item]]
            item = self.parent[item]
        return item

    def union(self, left: int, right: int) -> None:
        left_root, right_root = self.find(left), self.find(right)
        if left_root != right_root:
            self.parent[right_root] = left_root


class GridDetector:
    @staticmethod
    def from_lines(
        lines: Sequence[Line],
        size: Tuple[float, float],
        tolerance: Optional[float] = None,
    ) -> Optional[TableData]:
        width, height = size
        tolerance = tolerance if tolerance is not None else max(2.0, min(width, height) * 0.005)
        horizontal: List[Line] = []
        vertical: List[Line] = []
        for x0, y0, x1, y1 in lines:
            if abs(y1 - y0) <= tolerance and abs(x1 - x0) >= tolerance * 3:
                horizontal.append((min(x0, x1), (y0 + y1) / 2, max(x0, x1), (y0 + y1) / 2))
            elif abs(x1 - x0) <= tolerance and abs(y1 - y0) >= tolerance * 3:
                vertical.append(((x0 + x1) / 2, min(y0, y1), (x0 + x1) / 2, max(y0, y1)))
        xs = _cluster((line[0] for line in vertical), tolerance)
        ys = _cluster((line[1] for line in horizontal), tolerance)
        if len(xs) < 2 or len(ys) < 2:
            return None

        rows, cols = len(ys) - 1, len(xs) - 1
        groups = _DisjointSet(rows * cols)

        def index(row: int, col: int) -> int:
            return row * cols + col

        def has_vertical(x: float, y: float) -> bool:
            return any(abs(line[0] - x) <= tolerance and line[1] - tolerance <= y <= line[3] + tolerance for line in vertical)

        def has_horizontal(y: float, x: float) -> bool:
            return any(abs(line[1] - y) <= tolerance and line[0] - tolerance <= x <= line[2] + tolerance for line in horizontal)

        for row in range(rows):
            y_center = (ys[row] + ys[row + 1]) / 2
            for col in range(cols):
                x_center = (xs[col] + xs[col + 1]) / 2
                if col < cols - 1 and not has_vertical(xs[col + 1], y_center):
                    groups.union(index(row, col), index(row, col + 1))
                if row < rows - 1 and not has_horizontal(ys[row + 1], x_center):
                    groups.union(index(row, col), index(row + 1, col))

        members = defaultdict(list)
        for row in range(rows):
            for col in range(cols):
                members[groups.find(index(row, col))].append((row, col))

        cells: List[TableCell] = []
        for positions in members.values():
            top = min(row for row, _ in positions)
            left = min(col for _, col in positions)
            bottom = max(row for row, _ in positions)
            right = max(col for _, col in positions)
            cells.append(
                TableCell(
                    row=top,
                    col=left,
                    bbox=(xs[left], ys[top], xs[right + 1], ys[bottom + 1]),
                    row_span=bottom - top + 1,
                    col_span=right - left + 1,
                )
            )
        cells.sort(key=lambda cell: (cell.row, cell.col))
        return TableData(rows, cols, (xs[0], ys[0], xs[-1], ys[-1]), cells)
