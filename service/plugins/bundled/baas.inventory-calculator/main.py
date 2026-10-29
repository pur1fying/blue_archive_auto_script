"""Exact Schale inventory-management probabilities, without Qt or NumPy.

Rules follow PR #583's solver and terry-u16/schale-inventory-management:
9 x 5 cells, three groups of interchangeable rectangles, both orientations.
An empty observed cell is forbidden; found rectangles are fixed. A column
frontier DP counts each remaining arrangement once with Python integers.
"""
from functools import lru_cache
from math import comb
import time

WIDTH, HEIGHT = 9, 5
MAX_STATES = 350000
MAX_SECONDS = 8


class CalculationLimit(Exception):
    pass


def _integer(value, minimum, maximum):
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError("Invalid board integer.")
    return value


def _read(inputs):
    items = inputs.get("items", [{"width": 1, "height": 1, "count": 1}] * 3)
    if not isinstance(items, list) or len(items) != 3:
        raise ValueError("Exactly three item groups are required.")
    shapes, totals = [], []
    for item in items:
        shapes.append((_integer(item["height"], 1, 4), _integer(item["width"], 1, 4)))
        totals.append(_integer(item["count"], 0, 7))
    empty = inputs.get("empty_cells", [])
    if not isinstance(empty, list) or len(empty) != len(set(empty)):
        raise ValueError("Empty cells must be unique.")
    empty = {_integer(cell, 0, 44) for cell in empty}
    fixed = {}
    placed_counts = [0, 0, 0]
    for placed in inputs.get("placed", []):
        index = _integer(placed["item_index"], 0, 2)
        row, col = _integer(placed["row"], 0, 4), _integer(placed["col"], 0, 8)
        if type(placed["rotated"]) is not bool:
            raise ValueError("Rotation must be a boolean.")
        h, w = shapes[index]
        if placed["rotated"]:
            h, w = w, h
        if row + h > HEIGHT or col + w > WIDTH:
            raise ValueError("A found item is outside the board.")
        for r in range(row, row + h):
            for c in range(col, col + w):
                cell = r * WIDTH + c
                if cell in fixed or cell in empty:
                    raise ValueError("Found items overlap another observation.")
                fixed[cell] = index
        placed_counts[index] += 1
    remaining = tuple(total - count for total, count in zip(totals, placed_counts))
    if min(remaining) < 0:
        raise ValueError("Found item count exceeds the group's total count.")
    return shapes, remaining, empty, fixed


def _result(status, total=0, counts=None, empty=(), fixed=None):
    fixed = fixed or {}
    cells, best, best_probability = [], [], 0
    if status == "solved":
        for cell in range(WIDTH * HEIGHT):
            values = [counts[i][cell] / total for i in range(3)]
            if cell in fixed:
                values = [float(i == fixed[cell]) for i in range(3)]
            probability = min(1.0, sum(values))
            revealed = cell in empty or cell in fixed
            cells.append({"row": cell // WIDTH, "col": cell % WIDTH,
                          "group_a": values[0], "group_b": values[1], "group_c": values[2],
                          "any_item": probability, "revealed": revealed})
            # Compare exact numerators so symmetric cells remain tied.
            numerator = sum(counts[i][cell] for i in range(3))
            if not revealed and numerator > 0:
                if numerator > best_probability:
                    best, best_probability = [cell], numerator
                elif numerator == best_probability:
                    best.append(cell)
    messages = {
        "solved": "Exact probabilities. Each valid arrangement is equally likely.",
        "impossible": "No arrangement matches the empty cells, found items and item totals.",
        "limit": "Exact calculation exceeded its resource budget. Reveal more cells or reduce item counts.",
    }
    return {"status": status, "total_arrangements": str(total), "cells": cells,
            "best_cells": best, "message": messages[status]}


def solve(context, inputs):
    shapes, remaining, empty, fixed = _read(inputs)
    area = sum(h * w * count for (h, w), count in zip(shapes, remaining))
    free_cells = [cell for cell in range(45) if cell not in empty and cell not in fixed]
    if area > len(free_cells):
        return _result("impossible")
    # Closed form for single-cell items: also covers counts whose exact total
    # exceeds uint64 and avoids needless DP work for the initial board.
    if all(count == 0 or shape == (1, 1) for shape, count in zip(shapes, remaining)):
        total, available = 1, len(free_cells)
        for count in remaining:
            total *= comb(available, count)
            available -= count
        counts = [[0] * 45 for _ in range(3)]
        for index, count in enumerate(remaining):
            for cell in free_cells:
                counts[index][cell] = total * count // len(free_cells)
        return _result("solved", total, counts, empty, fixed)

    # Compile geometry once. Frontier contains remaining horizontal coverage
    # (0..3) for each of the five rows in the next visited column.
    variants = [[] for _ in range(45)]
    forbidden = empty | set(fixed)
    for p in range(45):
        row, col = p % HEIGHT, p // HEIGHT
        for index, (height, width) in enumerate(shapes):
            if not remaining[index]:
                continue
            for h, w in {(height, width), (width, height)}:
                if row + h > HEIGHT or col + w > WIDTH:
                    continue
                cells = tuple(r * WIDTH + c for r in range(row, row + h) for c in range(col, col + w))
                if any(cell in forbidden for cell in cells):
                    continue
                mask = sum(3 << (r * 2) for r in range(row, row + h))
                fill = sum((w - 1) << (r * 2) for r in range(row, row + h))
                variants[p].append((index, mask, fill, p + h, cells))

    started = time.monotonic()
    visited = 0

    def transitions(p, frontier, counts):
        row = p % HEIGHT
        cover = (frontier >> (row * 2)) & 3
        next_frontier = frontier - (1 << (row * 2)) if cover else frontier
        yield (p + 1, next_frontier, counts), None, ()
        if cover:
            return
        for index, mask, fill, target, cells in variants[p]:
            if counts[index] and not frontier & mask:
                next_counts = list(counts)
                next_counts[index] -= 1
                yield (target, frontier | fill, tuple(next_counts)), index, cells

    @lru_cache(maxsize=None)
    def suffix(p, frontier, counts):
        nonlocal visited
        visited += 1
        if visited > MAX_STATES or (visited % 1024 == 0 and time.monotonic() - started > MAX_SECONDS):
            raise CalculationLimit
        if p == 45:
            return int(frontier == 0 and not any(counts))
        # The area bound is conservative in the presence of known observations.
        if sum(h * w * count for (h, w), count in zip(shapes, counts)) > 45 - p:
            return 0
        return sum(suffix(*target) for target, _, _ in transitions(p, frontier, counts))

    try:
        total = suffix(0, 0, remaining)
        if not total:
            return _result("impossible")
        counts = [[0] * 45 for _ in range(3)]
        layers = [{} for _ in range(46)]
        layers[0][(0, remaining)] = 1
        for p in range(45):
            if time.monotonic() - started > MAX_SECONDS:
                raise CalculationLimit
            for (frontier, left), prefix in layers[p].items():
                for target, index, covered in transitions(p, frontier, left):
                    continuation = suffix(*target)
                    if not continuation:
                        continue
                    target_p, target_frontier, target_counts = target
                    key = (target_frontier, target_counts)
                    layers[target_p][key] = layers[target_p].get(key, 0) + prefix
                    if index is not None:
                        ways = prefix * continuation
                        for cell in covered:
                            counts[index][cell] += ways
            layers[p].clear()
        return _result("solved", total, counts, empty, fixed)
    except CalculationLimit:
        return _result("limit")
    finally:
        suffix.cache_clear()
