
import pygame, os, random
from settings import CELL_SIZE, ASSET_DIR, COLORS

# 形狀定義 (4x4陣列，使用整數代表顏色索引)
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
    def __init__(self, shape_key):
        self.shape_key = shape_key
        self.matrix = [row[:] for row in SHAPES[shape_key]]  # copy
        self.size = len(self.matrix[0])
        self.x = 0
        self.y = 0

    def rotate(self):
        # 逆時針旋轉
        self.matrix = [list(row) for row in zip(*self.matrix[::-1])]

    def get_cells(self):
        cells = []
        for row_idx, row in enumerate(self.matrix):
            for col_idx, val in enumerate(row):
                if val:
                    cells.append((self.x + col_idx, self.y + row_idx, val))
        return cells

def random_tetromino():
    return Tetromino(random.choice(list(SHAPES.keys())))
