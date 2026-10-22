# -*- coding: utf-8 -*-
"""库存管理概率求解器（schale-inventory-management 的 Python 移植）。

原版：terry-u16/schale-inventory-management（MIT）Rust/WASM 实现。
规则：9x5 棋盘；3 组备品（各组 W/H/数量可配，<=4x4）；部分格子已翻开
（空格=确定无备品）；已找到的备品固定占格；剩余备品在未翻开区域均匀
随机摆放。求：每个格子是某种备品的概率。

实现说明：原版用 DP 数全部摆放方案数，方案 <=10 万时全量恢复、否则按
比例随机采样估计概率。本移植利用"前缀 DP x 后缀 DP"恒等式
    含某摆放 P 的方案数 = pref[放置前状态] x suf[放置后状态]
直接得到每个格子的**精确**概率，无需恢复/采样；方案总数 all_count
仍由同一 DP 精确给出。w_bits(10bit) 维全部 numpy 向量化。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import numpy as np

WIDTH = 9
HEIGHT = 5
ITEM_GROUPS = 3
MAX_ITEM_SIZE = 4
W_BITS = 1 << (HEIGHT * 2)  # 1024


@dataclass
class ItemDef:
    height: int = 1
    width: int = 1
    count: int = 0


@dataclass
class PlacedItem:
    item_index: int
    rotated: bool
    row: int
    col: int


@dataclass
class BoardState:
    """cell: 0=未翻开 1=已翻开且为空。"""
    cells: List[int] = field(default_factory=lambda: [0] * (WIDTH * HEIGHT))
    items: List[ItemDef] = field(default_factory=lambda: [ItemDef() for _ in range(ITEM_GROUPS)])
    placed: List[PlacedItem] = field(default_factory=list)


@dataclass
class SolveResult:
    ok: bool
    message: str = ""
    all_count: int = 0
    # prob[item_index][row][col] ∈ [0,1]
    prob: Optional[List[List[List[float]]]] = None


def _occupied_vacant(state: BoardState):
    occ = [[0] * WIDTH for _ in range(HEIGHT)]
    for pl in state.placed:
        it = state.items[pl.item_index]
        h, w = (it.width, it.height) if pl.rotated else (it.height, it.width)
        for r in range(pl.row, min(pl.row + h, HEIGHT)):
            for c in range(pl.col, min(pl.col + w, WIDTH)):
                occ[r][c] += 1
    vac = [[1 if (state.cells[r * WIDTH + c] == 1 and occ[r][c] == 0) else 0
            for c in range(WIDTH)] for r in range(HEIGHT)]
    return occ, vac


def _rect_has(mat, r0, c0, r1, c1) -> bool:
    for r in range(r0, r1):
        row = mat[r]
        for c in range(c0, c1):
            if row[c]:
                return True
    return False


def _w_get(w: int, row: int) -> int:
    return (w >> (row * 2)) & 3


def solve(state: BoardState) -> SolveResult:
    items = state.items[:ITEM_GROUPS]
    if len(state.cells) != WIDTH * HEIGHT or len(items) != ITEM_GROUPS:
        return SolveResult(ok=False, message="input_error")
    for pl in state.placed:
        if pl.item_index < 0 or pl.item_index >= ITEM_GROUPS:
            return SolveResult(ok=False, message="input_error")
        it = items[pl.item_index]
        h, w = (it.width, it.height) if pl.rotated else (it.height, it.width)
        if pl.row < 0 or pl.col < 0 or pl.row + h > HEIGHT or pl.col + w > WIDTH:
            return SolveResult(ok=False, message="input_error")
    occ, vac = _occupied_vacant(state)
    if any(v > 1 for row in occ for v in row):
        return SolveResult(ok=False, message="overlap")

    placed_counts = [0] * ITEM_GROUPS
    for pl in state.placed:
        placed_counts[pl.item_index] += 1
    totals = [max(0, min(7, int(it.count))) for it in items]
    if any(placed_counts[i] > totals[i] for i in range(ITEM_GROUPS)):
        return SolveResult(ok=False, message="input_error")
    # 原版 lib.rs：输入 count 是总数，已放置备品从 remaining count 中扣除。
    counts = [totals[i] - placed_counts[i] for i in range(ITEM_GROUPS)]
    cn = [c + 1 for c in counts]
    strides = [cn[1] * cn[2], cn[2], 1]
    C_TOTAL = cn[0] * cn[1] * cn[2]
    FULL_C = C_TOTAL - 1  # c 全取最大值的扁平下标
    P_END = WIDTH * HEIGHT

    # 变体：每个组 0=原方向 1=旋转（正方形旋转=原样）
    variants = []  # (item_index, h, w, rot)
    for i, it in enumerate(items):
        if counts[i] <= 0:
            continue
        h, w = max(1, min(4, it.height)), max(1, min(4, it.width))
        variants.append((i, h, w, False))
        if h != w:
            variants.append((i, w, h, True))

    # 几何可行性：geom[p][variant_i] —— 以 p 的 (row,col) 为左上能否放
    def geom_ok(row, col, h, w) -> bool:
        if row + h > HEIGHT or col + w > WIDTH:
            return False
        if _rect_has(occ, row, col, row + h, col + w):
            return False
        if _rect_has(vac, row, col, row + h, col + w):
            return False
        return True

    geom = {}  # (p, variant_idx) -> bool
    for p in range(P_END):
        row, col = p % HEIGHT, p // HEIGHT
        for vi, (i, h, w, rot) in enumerate(variants):
            geom[(p, vi)] = geom_ok(row, col, h, w)

    # w 重映射表：place[row][variant_i] = (valid_mask(1024), new_idx(1024))
    place_tables = {}
    for p in range(P_END):
        row = p % HEIGHT
        for vi, (i, h, w, rot) in enumerate(variants):
            if not geom[(p, vi)]:
                continue
            valid = np.zeros(W_BITS, dtype=bool)
            new_idx = np.zeros(W_BITS, dtype=np.int64)
            fill = w - 1
            rows_covered = range(row, row + h)
            for wb in range(W_BITS):
                ok = True
                for r in rows_covered:
                    if _w_get(wb, r) != 0:
                        ok = False
                        break
                if not ok:
                    continue
                nw = wb
                for r in rows_covered:
                    nw |= (fill << (r * 2))
                valid[wb] = True
                new_idx[wb] = nw
            place_tables[(p, vi)] = (valid, new_idx)

    # 位置转移：skip 恒为 p+1；place 后位置取决于 row+h
    place_next = {}
    for p in range(P_END):
        row, col = p % HEIGHT, p // HEIGHT
        for vi, (i, h, w, rot) in enumerate(variants):
            if not geom[(p, vi)]:
                continue
            nrow = row + h
            ncol = col
            if nrow >= HEIGHT:
                nrow = 0
                ncol = col + 1
            place_next[(p, vi)] = ncol * HEIGHT + nrow

    C = C_TOTAL
    # C 行重映射：放组 i → c_i+1
    row_maps = {}
    for i in range(ITEM_GROUPS):
        if counts[i] <= 0:
            continue
        sel, up = [], []
        for cidx in range(C):
            c2 = cidx % cn[2]
            c1 = (cidx // cn[2]) % cn[1]
            c0 = cidx // (cn[2] * cn[1])
            cv = (c0, c1, c2)
            if cv[i] < counts[i]:
                nv = list(cv)
                nv[i] += 1
                sel.append(cidx)
                up.append(((nv[0] * cn[1]) + nv[1]) * cn[2] + nv[2])
        row_maps[i] = (np.array(sel, dtype=np.int64), np.array(up, dtype=np.int64))

    def skip_forward(next_arr, src, row):
        # next[..., field'] += src: 0->0,1->0,2->1,3->2（组内 reshape 向量化）
        A = 1 << (row * 2)
        B = 1 << (HEIGHT * 2 - row * 2 - 2)
        s = src.reshape(C, A, 4, B)
        n = next_arr.reshape(C, A, 4, B)
        n[:, :, 0, :] += s[:, :, 0, :] + s[:, :, 1, :]
        n[:, :, 1, :] += s[:, :, 2, :]
        n[:, :, 2, :] += s[:, :, 3, :]

    def skip_backward(src_next, row):
        # suf[p][w] = suf[p+1][dec(w)]（gather）
        A = 1 << (row * 2)
        B = 1 << (HEIGHT * 2 - row * 2 - 2)
        s = src_next.reshape(C, A, 4, B)
        out = np.empty((C, A, 4, B), dtype=np.uint64)
        out[:, :, 0, :] = s[:, :, 0, :]
        out[:, :, 1, :] = s[:, :, 0, :]
        out[:, :, 2, :] = s[:, :, 1, :]
        out[:, :, 3, :] = s[:, :, 2, :]
        return out.reshape(C, W_BITS)

    # ---- suf（后缀 DP）：p 从终点往回 ----
    suf = [None] * (P_END + 1)
    term = np.zeros((C, W_BITS), dtype=np.uint64)
    term[FULL_C, 0] = 1
    suf[P_END] = term
    for p in range(P_END - 1, -1, -1):
        row = p % HEIGHT
        cur = skip_backward(suf[p + 1], row)
        for vi, (i, h, w, rot) in enumerate(variants):
            if not geom[(p, vi)]:
                continue
            if i not in row_maps:
                continue
            valid, new_idx = place_tables[(p, vi)]
            vw = np.nonzero(valid)[0]
            if vw.size == 0:
                continue
            sel, up = row_maps[i]
            if sel.size == 0:
                continue
            nxt = suf[place_next[(p, vi)]]
            # suf[p][sel, w_valid] += suf[p'][up, new_w]（gather）
            cur[np.ix_(sel, vw)] += nxt[np.ix_(up, new_idx[vw])]
        suf[p] = cur

    start = suf[0]
    all_count = int(start[0, 0])
    if all_count == 0:
        return SolveResult(ok=False, message="无有效配置：请检查已翻开的空格与备品尺寸/数量是否矛盾。")

    # ---- pref（前缀 DP）：p 从起点往后；放置转移跳到 place_next（可 > p+1）----
    pref = [np.zeros((C, W_BITS), dtype=np.uint64) for _ in range(P_END + 1)]
    pref[0][0, 0] = 1
    for p in range(P_END):
        row = p % HEIGHT
        src = pref[p]
        if not src.any():
            continue
        # skip：恒到 p+1
        skip_forward(pref[p + 1], src, row)
        for vi, (i, h, w, rot) in enumerate(variants):
            if not geom[(p, vi)]:
                continue
            if i not in row_maps:
                continue
            valid, new_idx = place_tables[(p, vi)]
            vw = np.nonzero(valid)[0]
            if vw.size == 0:
                continue
            sel, up = row_maps[i]
            if sel.size == 0:
                continue
            # pref[p'][up, new_w] += pref[p][sel, w_valid]（new_w 对 valid w 单射）
            tgt = pref[place_next[(p, vi)]]
            tgt[np.ix_(up, new_idx[vw])] += src[np.ix_(sel, vw)]

    # ---- 每格精确概率：含摆放 P 的方案数 = pref[pre] x suf[post] ----
    counts_cell = [[[0] * WIDTH for _ in range(HEIGHT)] for _ in range(ITEM_GROUPS)]
    for vi, (i, h, w, rot) in enumerate(variants):
        for p in range(P_END):
            row, col = p % HEIGHT, p // HEIGHT
            if not geom[(p, vi)]:
                continue
            if i not in row_maps:
                continue
            valid, new_idx = place_tables[(p, vi)]
            vw = np.nonzero(valid)[0]
            if vw.size == 0:
                continue
            sel, up = row_maps[i]
            if sel.size == 0:
                continue
            post = suf[place_next[(p, vi)]]
            # float64 乘积：避免 uint64 乘法溢出；与 all_count 相除为精确比值
            contain = float(np.sum(
                pref[p][np.ix_(sel, vw)].astype(np.float64)
                * post[np.ix_(up, new_idx[vw])].astype(np.float64)
            ))
            if contain <= 0:
                continue
            for r in range(row, row + h):
                for c in range(col, col + w):
                    counts_cell[i][r][c] += contain

    prob = []
    for i in range(ITEM_GROUPS):
        grid = []
        for r in range(HEIGHT):
            line = []
            for c in range(WIDTH):
                v = counts_cell[i][r][c] / all_count if all_count else 0.0
                line.append(min(1.0, max(0.0, v)))
            grid.append(line)
        prob.append(grid)

    # 已放置的备品：存在于一切有效配置中，概率恒为 1
    for pl in state.placed:
        it = items[pl.item_index]
        h, w = (it.width, it.height) if pl.rotated else (it.height, it.width)
        for r in range(pl.row, min(pl.row + h, HEIGHT)):
            for c in range(pl.col, min(pl.col + w, WIDTH)):
                prob[pl.item_index][r][c] = 1.0

    return SolveResult(ok=True, all_count=all_count, prob=prob)
