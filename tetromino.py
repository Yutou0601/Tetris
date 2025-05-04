
import pygame, os, random
from settings import CELL_SIZE, ASSET_DIR, COLORS

# 形狀定義 (4x4 陣列，使用整數代表顏色索引)
SHAPES = {
    "I": [
        [1,1,1,1]
    ],
    "J": [
        [2,0,0],
        [2,2,2]
    ],
    "L": [
        [0,0,3],
        [3,3,3]
    ],
    "O": [
        [4,4],
        [4,4]
    ],
    "S": [
        [0,5,5],
        [5,5,0]
    ],
    "T": [
        [0,6,0],
        [6,6,6]
    ],
    "Z": [
        [7,7,0],
        [0,7,7]
    ],
}

def load_block_images():
    """
    嘗試由 All_color_blocks.png 擷取各顏色方塊，若失敗則以純色方塊代替
    回傳 list，下標與 COLORS 配對
    """
    block_surfaces = [pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)]
    sprite_path = os.path.join(ASSET_DIR, "All_color_blocks.png")
    if not os.path.exists(sprite_path):
        sprite_path = os.path.join(ASSET_DIR, "All_color_blocks.jpg")
    if os.path.exists(sprite_path):
        sheet = pygame.image.load(sprite_path).convert_alpha()
        color_count = sheet.get_width() // sheet.get_height()  # 假設為水平排列
        w = sheet.get_height()
        for i in range(color_count):
            sub = sheet.subsurface((i*w, 0, w, w))
            block_surfaces.append(pygame.transform.scale(sub, (CELL_SIZE, CELL_SIZE)))
    else:
        # fallback 純色
        for c in COLORS[1:]:
            surf = pygame.Surface((CELL_SIZE, CELL_SIZE))
            surf.fill(c)
            block_surfaces.append(surf)
    return block_surfaces

BLOCK_IMAGES = None  # 遊戲啟動後由 Game 呼叫 load_block_images 產生


class Tetromino:
    # 面向與旋轉方向
    ROT_DIR = {+1: 1, -1: -1}   # +1=順時針, -1=逆時針

    # JLSTZ 共用 kick 表
    JLSTZ_KICKS = {
    (0, 1): [(0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)],
    (1, 0): [(0, 0), ( 1, 0), ( 1,  1), (0,-2), ( 1,-2)],
    (1, 2): [(0, 0), ( 1, 0), ( 1,  1), (0,-2), ( 1,-2)],
    (2, 1): [(0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)],
    (2, 3): [(0, 0), ( 1, 0), ( 1, -1), (0, 2), ( 1, 2)],
    (3, 2): [(0, 0), (-1, 0), (-1,  1), (0,-2), (-1,-2)],
    (3, 0): [(0, 0), (-1, 0), (-1,  1), (0,-2), (-1,-2)],
    (0, 3): [(0, 0), ( 1, 0), ( 1, -1), (0, 2), ( 1, 2)],
    }

    # I 方塊 kick 表
    I_KICKS = {
    (0, 1): [(0, 0), (-2, 0), ( 1, 0), (-2,  1), ( 1, -2)],
    (1, 0): [(0, 0), ( 2, 0), (-1, 0), ( 2, -1), (-1,  2)],
    (1, 2): [(0, 0), (-1, 0), ( 2, 0), (-1, -2), ( 2,  1)],
    (2, 1): [(0, 0), ( 1, 0), (-2, 0), ( 1,  2), (-2, -1)],
    (2, 3): [(0, 0), ( 2, 0), (-1, 0), ( 2, -1), (-1,  2)],
    (3, 2): [(0, 0), (-2, 0), ( 1, 0), (-2,  1), ( 1, -2)],
    (3, 0): [(0, 0), ( 1, 0), (-2, 0), ( 1,  2), (-2, -1)],
    (0, 3): [(0, 0), (-1, 0), ( 2, 0), (-1, -2), ( 2,  1)],
    }

    def __init__(self, shape_key):
        self.shape_key = shape_key
        self.matrix = [row[:] for row in SHAPES[shape_key]]
        self.x, self.y = 0, 0
        self.r = 0  # 0=Spawn,1=右,2=反,3=左

    # --- 內部旋轉 ---
    def _rot_cw(self):
        self.matrix = [list(row[::-1]) for row in zip(*self.matrix)]

    def _rot_ccw(self):
        self.matrix = [list(row) for row in zip(*self.matrix)][::-1]

    # --- SRS 旋轉 ---
    def rotate(self, direction, board):
        """
        direction : +1 順時針, -1 逆時針
        board     : Board 物件 (用於 valid_position)
        回傳 True = 成功, False = 失敗
        """
        if direction not in (1, -1):
            return False

        old_r = self.r
        new_r = (self.r + self.ROT_DIR[direction]) % 4

        # 先試著轉
        if direction == 1:
            self._rot_cw()
        else:
            self._rot_ccw()

        kicks = self.I_KICKS if self.shape_key == "I" else self.JLSTZ_KICKS
        for dx, dy in kicks[(old_r, new_r)]:
            if board.valid_position(self, dx=dx, dy=dy):
                self.x += dx
                self.y += dy
                self.r = new_r
                return True

        # 若全部 kick 失敗 → 還原
        if direction == 1:
            self._rot_ccw()
        else:
            self._rot_cw()
        return False

    # --- 取得所有方塊座標 ---
    def get_cells(self):
        for row_idx, row in enumerate(self.matrix):
            for col_idx, val in enumerate(row):
                if val:
                    yield self.x + col_idx, self.y + row_idx, val


def random_tetromino():
    return Tetromino(random.choice(list(SHAPES.keys())))
