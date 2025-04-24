
import os
import pygame

# === 基本設定 ===
CELL_SIZE = 24           # 單一方塊像素大小
BOARD_COLS = 10
BOARD_ROWS = 20
SIDE_PANEL_WIDTH_RATIO = 1/3   # 旁邊黑色區域相對遊戲區寬度

FPS = 60

# --- Movement auto-repeat (DAS & ARR) ---
DAS_DELAY = 200   # 延遲自動移動啟動 (ms)
ARR_SPEED = 40    # 自動移動間隔 (ms)

# === 畫面計算 ===
BOARD_WIDTH_PX = CELL_SIZE * BOARD_COLS
BOARD_HEIGHT_PX = CELL_SIZE * BOARD_ROWS
SIDE_PANEL_PX  = int(BOARD_WIDTH_PX * SIDE_PANEL_WIDTH_RATIO)
SCREEN_WIDTH   = BOARD_WIDTH_PX + SIDE_PANEL_PX * 2
SCREEN_HEIGHT  = BOARD_HEIGHT_PX

ASSET_DIR      = os.path.join(os.path.dirname(__file__), "Material")
MUSIC_DIR      = os.path.join(os.path.dirname(__file__), "Background_music")

# 循環音樂
MUSIC_FILES    = [os.path.join(MUSIC_DIR, f"music{i}.mp3") for i in range(1,6)]

# 鍵盤按鍵 (可在 Setting 介面變更)
DEFAULT_KEYS   = {
    "LEFT": pygame.K_LEFT,
    "RIGHT": pygame.K_RIGHT,
    "DOWN": pygame.K_DOWN,
    "ROTATE": pygame.K_UP,
    "HARD_DROP": pygame.K_SPACE,
    "HOLD": pygame.K_LSHIFT
}

# 顏色 (備用)
COLORS = [
    (0,0,0),
    (0,255,255),     # I
    (0,0,255),       # J
    (255,127,0),     # L
    (255,255,0),     # O
    (0,255,0),       # S
    (128,0,128),     # T
    (255,0,0),       # Z
]


# 音效／音樂開關 (可由 SettingUI 變更)
MUSIC_ON = True
SFX_ON   = True

# Background frame inner margin (pixels) — tune if needed
BG_MARGIN_X = 12
BG_MARGIN_Y = 18

# Recompute screen height (frame plus margin)
BOARD_OFFSET_X = SIDE_PANEL_PX + BG_MARGIN_X
BOARD_OFFSET_Y = BG_MARGIN_Y

SCREEN_HEIGHT = BOARD_HEIGHT_PX + BG_MARGIN_Y*2  # background frame top+bottom

# ----- Frame & Board alignment (new scheme) -----
# Thickness of frame border after scaling, use CELL_SIZE as reference
FRAME_BORDER = CELL_SIZE        # scale background so left/right/top/bottom border ~= 1 cell

# Derived positions
BOARD_OFFSET_X = SIDE_PANEL_PX            # board X inside frame
BOARD_OFFSET_Y = FRAME_BORDER             # board Y (leave border thickness at top)

# Update screen height according to new frame
SCREEN_HEIGHT = BOARD_HEIGHT_PX + FRAME_BORDER*2
