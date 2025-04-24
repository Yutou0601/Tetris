
import pygame
from settings import BOARD_COLS, BOARD_ROWS, CELL_SIZE
import tetromino  # 直接載入模組，隨時取得最新 BLOCK_IMAGES

class Board:
    def __init__(self):
        self.grid = [[0] * BOARD_COLS for _ in range(BOARD_ROWS)]
        self.score = 0

    # ---------------- 檢查合法位置 ----------------
    def valid_position(self, piece, dx=0, dy=0):
        for x, y, _ in piece.get_cells():
            x += dx
            y += dy

            # X 軸邊界
            if not (0 <= x < BOARD_COLS):
                return False

            # Y 超出下邊界
            if y >= BOARD_ROWS:
                return False

            # 只有 y >= 0 時才檢查碰撞（生成階段 y 可能 < 0）
            if y >= 0 and self.grid[y][x]:
                return False
        return True

    # ---------------- 固定方塊＋消行 ----------------
    
    def lock_piece(self, piece):
        cleared = -1  # sentinel if game over

        for x, y, val in piece.get_cells():
            if y < 0:
                return -1          # game over
            self.grid[y][x] = val

        cleared = self.clear_lines()
        self.score += cleared * 100
        return cleared            # 0~4 lines cleared

        self.grid[y][x] = val

        cleared = self.clear_lines()
        self.score += cleared * 100
        return True

    def clear_lines(self):
        new_grid = [row for row in self.grid if any(v == 0 for v in row)]
        cleared = BOARD_ROWS - len(new_grid)
        while len(new_grid) < BOARD_ROWS:
            new_grid.insert(0, [0] * BOARD_COLS)
        self.grid = new_grid
        return cleared

    # ---------------- 繪製 ----------------
    def draw(self, surface, offset_x, offset_y):
        for row_idx, row in enumerate(self.grid):
            for col_idx, val in enumerate(row):
                if val:
                    img = tetromino.BLOCK_IMAGES[val]
                    surface.blit(
                        img,
                        (offset_x + col_idx * CELL_SIZE,
                         offset_y + row_idx * CELL_SIZE)
                    )
