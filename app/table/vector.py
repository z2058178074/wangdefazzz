from __future__ import annotations

from typing import List

from app.models import TableCell, TableData


def extract_vector_tables(page) -> List[TableData]:
    settings = {
        "vertical_strategy": "lines",
        "horizontal_strategy": "lines",
        "snap_tolerance": 3,
        "join_tolerance": 3,
        "intersection_tolerance": 5,
    }
    result: List[TableData] = []
    for found in page.find_tables(table_settings=settings):
        matrix = found.extract()
        if not matrix or not matrix[0]:
            continue
        rows = len(matrix)
        cols = max(len(row) for row in matrix)
        x0, top, x1, bottom = (float(value) for value in found.bbox)
        row_height = (bottom - top) / max(rows, 1)
        col_width = (x1 - x0) / max(cols, 1)
        cells = []
        for row_index, row in enumerate(matrix):
            for col_index in range(cols):
                value = row[col_index] if col_index < len(row) else ""
                if value is None:
                    continue
                cells.append(
                    TableCell(
                        row_index,
                        col_index,
                        (
                            x0 + col_index * col_width,
                            top + row_index * row_height,
                            x0 + (col_index + 1) * col_width,
                            top + (row_index + 1) * row_height,
                        ),
                        str(value).strip(),
                    )
                )
        result.append(TableData(rows, cols, (x0, top, x1, bottom), cells))
    return result
