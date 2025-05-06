from __future__ import annotations

import os
import random
from typing import List, Tuple, Dict

import pygame

from settings import CELL_SIZE, ASSET_DIR, COLORS

# -----------------------------------------------------------------------------
# Shape definitions (spawn/orientation 0)
# -----------------------------------------------------------------------------

SHAPES: Dict[str, List[List[int]]] = {
    "I": [
        [0, 0, 0, 0],
        [1, 1, 1, 1],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
    ],
    "J": [
        [2, 0, 0, 0],
        [2, 2, 2, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
    ],
    "L": [
        [0, 0, 3, 0],
        [3, 3, 3, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
    ],
    "O": [
        [0, 4, 4, 0],
        [0, 4, 4, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
    ],
    "S": [
        [0, 5, 5, 0],
        [5, 5, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
    ],
    "T": [
        [0, 6, 0, 0],
        [6, 6, 6, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
    ],
    "Z": [
        [7, 7, 0, 0],
        [0, 7, 7, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
    ],
}

PIVOT: Dict[str, Tuple[int, int]] = {
    "I": (1, 2),  # guideline pivot for I
    "O": (1, 1),  # O technically doesn't rotate, but keep for completeness
    "default": (1, 1),
}

SHAPE_KEYS = list(SHAPES.keys())

# -----------------------------------------------------------------------------
# Block sprite loading helper
# -----------------------------------------------------------------------------

def load_block_images() -> List[pygame.Surface]:
    surfaces: List[pygame.Surface] = [pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)]

    sprite_path = os.path.join(ASSET_DIR, "All_color_blocks.png")
    if not os.path.exists(sprite_path):
        sprite_path = os.path.join(ASSET_DIR, "All_color_blocks.jpg")

    if os.path.exists(sprite_path):
        sheet = pygame.image.load(sprite_path).convert_alpha()
        h = sheet.get_height()
        count = sheet.get_width() // h
        for i in range(count):
            sub = sheet.subsurface((i * h, 0, h, h))
            surfaces.append(pygame.transform.scale(sub, (CELL_SIZE, CELL_SIZE)))

    else:
        for c in COLORS[1:]:
            surf = pygame.Surface((CELL_SIZE, CELL_SIZE))
            surf.fill(c)
            surfaces.append(surf)
    return surfaces

BLOCK_IMAGES: List[pygame.Surface] | None = None

# -----------------------------------------------------------------------------
# Kick tables (Y↓)
# -----------------------------------------------------------------------------

JLSTZ_KICKS: Dict[Tuple[int, int], List[Tuple[int, int]]] = {
    (0, 1): [(0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)],
    (1, 0): [(0, 0), (1, 0), (1, 1), (0, -2), (1, -2)],
    (1, 2): [(0, 0), (1, 0), (1, 1), (0, -2), (1, -2)],
    (2, 1): [(0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)],
    (2, 3): [(0, 0), (1, 0), (1, -1), (0, 2), (1, 2)],
    (3, 2): [(0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)],
    (3, 0): [(0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)],
    (0, 3): [(0, 0), (1, 0), (1, 1), (0, -2), (1, -2)],  # ← 修正 Y 位號
}

I_KICKS: Dict[Tuple[int, int], List[Tuple[int, int]]] = {
    (0, 1): [(0, 0), (-2, 0), (1, 0), (-2, 1), (1, -2)],
    (1, 0): [(0, 0), (2, 0), (-1, 0), (2, -1), (-1, 2)],
    (1, 2): [(0, 0), (-1, 0), (2, 0), (-1, -2), (2, 1)],
    (2, 1): [(0, 0), (1, 0), (-2, 0), (1, 2), (-2, -1)],
    (2, 3): [(0, 0), (2, 0), (-1, 0), (2, -1), (-1, 2)],
    (3, 2): [(0, 0), (-2, 0), (1, 0), (-2, 1), (1, -2)],
    (3, 0): [(0, 0), (1, 0), (-2, 0), (1, 2), (-2, -1)],
    (0, 3): [(0, 0), (-1, 0), (2, 0), (-1, -2), (2, 1)],
}

# -----------------------------------------------------------------------------
# Rotation helpers – rotate about pivot so it stays fixed within the matrix
# -----------------------------------------------------------------------------

def _rotate_matrix(matrix: List[List[int]], pivot: Tuple[int, int], cw: bool) -> List[List[int]]:
    size = len(matrix)
    pr, pc = pivot
    new = [[0] * size for _ in range(size)]
    for r, row in enumerate(matrix):
        for c, val in enumerate(row):
            if not val:
                continue
            # translate to origin (pivot)
            dr, dc = r - pr, c - pc
            if cw:
                dr, dc = dc, -dr  # 90° CW
            else:  # CCW
                dr, dc = -dc, dr
            nr, nc = pr + dr, pc + dc
            new[nr][nc] = val
    return new

# -----------------------------------------------------------------------------
# Tetromino class
# -----------------------------------------------------------------------------

class Tetromino:
    """Single falling tetromino with SRS rotation."""

    ROT_DIR = {+1: 1, -1: -1}

    def __init__(self, shape: str):
        self.shape_key = shape
        self.matrix = [row[:] for row in SHAPES[shape]]
        self.x, self.y = 0, -4  # spawn slightly above board
        self.r = 0  # orientation 0 = spawn

    # ---------------- 旋轉 ----------------
    def _apply_rotation(self, cw: bool):
        piv = PIVOT.get(self.shape_key, PIVOT["default"])
        self.matrix = _rotate_matrix(self.matrix, piv, cw)

    def rotate(self, direction: int, board) -> bool:
        if self.shape_key == "O":
            return True
        else:
            if direction not in self.ROT_DIR:
                return False
            old_r = self.r
            new_r = (self.r + self.ROT_DIR[direction]) % 4
            # 先計算旋轉矩陣
            self._apply_rotation(cw=(direction == 1))
            kicks = I_KICKS if self.shape_key == "I" else JLSTZ_KICKS

            for dx, dy in kicks[(old_r, new_r)]:
                if board.valid_position(self, dx=dx, dy=dy):
                    self.x += dx
                    self.y += dy
                    self.r = new_r
                    return True
                
            # 若全部 Kick 失敗 → 恢復
            self._apply_rotation(cw=(direction == -1))  # 逆向轉回
            return False
    # ---------------- 座標輸出 ----------------
    def get_cells(self):
        for ry, row in enumerate(self.matrix):
            for cx, val in enumerate(row):
                if val:
                    yield self.x + cx, self.y + ry, val

    # ---------------- 其他 ----------------
    def __repr__(self):
        return f"<Tetromino {self.shape_key} r={self.r} pos=({self.x},{self.y})>"


# -----------------------------------------------------------------------------
# 工具函式
# -----------------------------------------------------------------------------

def random_tetromino() -> Tetromino:
    return Tetromino(random.choice(SHAPE_KEYS))

__all__ = [
    "SHAPES",
    "PIVOT",
    "load_block_images",
    "BLOCK_IMAGES",
    "Tetromino",
    "random_tetromino",
]                 