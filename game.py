import pygame, sys, os, random
import settings as cfg
from settings import *
import tetromino
from tetromino import random_tetromino
from board import Board
from ui import MenuUI, SettingUI

# --------- 參數 ---------
DAS_DELAY, ARR_SPEED = 200, 40        # 移動充電 / 重複輸入
LOCK_DELAY           = 500            # ms
INITIAL_FALL_DELAY   = 1000           # 等級 0 自然落下

class TetrisGame:
    def __init__(self):
        pygame.init(); pygame.mixer.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Tetris")
        self.clock = pygame.time.Clock()

        # 方塊圖
        tetromino.BLOCK_IMAGES = tetromino.load_block_images()

        # 音樂
        self.music_list, self.music_idx = MUSIC_FILES, 0
        pygame.mixer.music.set_endevent(pygame.USEREVENT + 1)
        self.play_music()

        # 音效
        sfx_dir = os.path.join(os.path.dirname(__file__), "Sound_effect")
        self.sfx_put   = pygame.mixer.Sound(os.path.join(sfx_dir, "put_on_top.mp3"))
        self.sfx_clear = pygame.mixer.Sound(os.path.join(sfx_dir, "break.mp3"))

        self.keys = DEFAULT_KEYS
        self.run_menu()

    # ---------- 音樂 ----------
    def play_music(self):
        if not self.music_list or not cfg.MUSIC_ON:
            pygame.mixer.music.stop(); return
        pygame.mixer.music.load(self.music_list[self.music_idx])
        pygame.mixer.music.play()
        self.music_idx = (self.music_idx + 1) % len(self.music_list)

    # ---------- 主流程 ----------
    def run_menu(self):
        menu = MenuUI(self.screen)
        while True:
            opt = menu.run()
            if opt == 0: self.start_game()
            elif opt == 1: SettingUI(self.screen, self.keys).run()
            else: pygame.quit(); sys.exit()

    # ---------- 開啟一局 ----------
    def start_game(self):
        self.board = Board()
        self.current, self.next_piece = random_tetromino(), random_tetromino()
        self.hold_piece, self.hold_locked = None, False

        # 計分參數
        self.score = 0
        self.lines = 0
        self.level = 0
        self.b2b   = False      # Back-to-Back 旗標

        # 時間控制
        self.fall_delay = INITIAL_FALL_DELAY
        self.drop_timer = pygame.time.get_ticks()
        self.lock_timer = None

        # 輸入狀態
        self.move_dir = self.das_timer = self.arr_timer = 0
        self.down_pressed = False
        self.down_start   = 0
        self.down_delay   = 120

        self.spawn_piece()
        self.in_game = True

        self.flash_points      = 0       # 這次清行得到多少分
        self.flash_start_time  = 0       # 開始顯示的時間戳
        self.flash_duration_ms = 1500    # 顯示 1.5 秒

        self.game_loop()

    # ---------- 產生新方塊 ----------
    def spawn_piece(self):
        self.current, self.next_piece = self.next_piece, random_tetromino()
        self.current.x = BOARD_COLS//2 - len(self.current.matrix[0])//2
        self.current.y = -2
        self.current.rotated = False
        self.hold_locked = False
        if not self.board.valid_position(self.current):
            self.game_over()

    # ---------- HOLD ----------
    def hold(self):
        if self.hold_locked: return
        if self.hold_piece is None:
            self.hold_piece = self.current; self.spawn_piece()
        else:
            self.current, self.hold_piece = self.hold_piece, self.current
            self.current.x = BOARD_COLS//2 - len(self.current.matrix[0])//2
            self.current.y = -2
            self.current.rotated = False
        self.hold_locked = True

    # ---------- DROP ----------
    def hard_drop(self):
        while self.board.valid_position(self.current, dy=1):
            self.current.y += 1
        self.lock_piece()

    # ---------- 鎖入 ----------
    def lock_piece(self):
        cleared = self.board.lock_piece(self.current)     # -1 = game over
        if cleared == -1:
            self.game_over(); return

        if cfg.SFX_ON and self.sfx_put:   self.sfx_put.play()
        if cleared and cfg.SFX_ON and self.sfx_clear: self.sfx_clear.play()

        # ----- T-Spin 判定（簡化） -----
        is_tspin = (
            getattr(self.current, "name", "") == "T"
            and self.current.rotated
            and cleared > 0
        )

        self.update_score(cleared, is_tspin)
        self.spawn_piece()

    # ---------- 計分 ----------
    def update_score(self, cleared, is_tspin):
        if cleared == 0:
            self.b2b = False
            return

        level_mul = self.level + 1
        difficult = False
        points    = 0

        if is_tspin and cleared == 2:            # T-Spin Double
            points = 12 * level_mul
            difficult = True
        elif is_tspin and cleared == 3:          # T-Spin Triple
            points = 36 * level_mul
            difficult = True
        elif cleared == 4:                       # Tetris
            points = 8 * level_mul
            difficult = True
        else:                                    # 一般單/雙/三消
            points = {1: 1, 2: 3, 3: 5}[cleared] * level_mul

        # Back-to-Back 加成
        if difficult and self.b2b:
            points = int(points * 1.5)           # +50 %
        self.score += points

        # 更新 B2B 狀態
        self.b2b = difficult

        # 升級
        self.lines += cleared
        if self.lines // 10 > self.level:
            self.level += 1

        # -------- Back-to-Back 與升級計算都做完後 ----------
        self.flash_points     = points         # 記下剛才拿到的分數
        self.flash_start_time = pygame.time.get_ticks()

    # ---------- ROTATE / MOVE ----------
    def rotate(self, dir=1):
        if self.current.rotate(dir, self.board):
            self.lock_timer = None
            self.current.rotated = True

    def move(self, dx):
        if self.board.valid_position(self.current, dx=dx):
            self.current.x += dx
            self.lock_timer = None

    # ---------- SOFT DROP ----------
    def soft_drop(self):
        if self.board.valid_position(self.current, dy=1):
            self.current.y += 1
            self.lock_timer = None
        else:
            now = pygame.time.get_ticks()
            if self.lock_timer is None:
                self.lock_timer = now
            elif now - self.lock_timer >= LOCK_DELAY:
                self.lock_piece()

    # ---------- 主迴圈 ----------
    def game_loop(self):
        while self.in_game:
            dt = self.clock.tick(FPS)
            for e in pygame.event.get():
                if e.type == pygame.QUIT: pygame.quit(); sys.exit()
                if e.type == pygame.USEREVENT + 1: self.play_music()

                # ---------- KEYDOWN ----------
                if e.type == pygame.KEYDOWN:
                    if e.key == self.keys["LEFT"]:
                        self.move_dir = -1; self.move(-1); self.das_timer = self.arr_timer = pygame.time.get_ticks()
                    elif e.key == self.keys["RIGHT"]:
                        self.move_dir = 1;  self.move(1);  self.das_timer = self.arr_timer = pygame.time.get_ticks()
                    elif e.key == self.keys["DOWN"]:
                        self.down_pressed = True
                        self.down_start = pygame.time.get_ticks()
                        self.down_delay = 120
                    elif e.key == self.keys["ROTATE"]:
                        self.rotate()
                    elif e.key == self.keys["HARD_DROP"]:
                        self.hard_drop()
                    elif e.key == self.keys["HOLD"]:
                        self.hold()
                    elif e.key == pygame.K_ESCAPE:
                        self.in_game = False  # 返回主選單
                        break

                # ---------- KEYUP ----------
                if e.type == pygame.KEYUP:
                    if e.key in (self.keys["LEFT"], self.keys["RIGHT"]):
                        self.move_dir = 0
                    if e.key == self.keys["DOWN"]:
                        self.down_pressed = False

            # ---------- DAS / ARR ----------
            if self.move_dir:
                now = pygame.time.get_ticks()
                if now - self.das_timer >= DAS_DELAY and now - self.arr_timer >= ARR_SPEED:
                    self.move(self.move_dir)
                    self.arr_timer = now

            # ---------- 自然下落 ----------
            now = pygame.time.get_ticks()
            base_delay = {"Easy": 1500, "Normal": 800, "Hard": 200}.get(cfg.DIFFICULTY, 1500)
            self.fall_delay = max(50, int(base_delay * (0.85 ** self.level)))
            delay = self.fall_delay
            if self.down_pressed:
                held = now - self.down_start
                self.down_delay = max(20, 120 - (held // 200) * 10)
                delay = self.down_delay
            if now - self.drop_timer > delay:
                self.soft_drop(); self.drop_timer = now

            self.render()

    # ---------- 繪圖 ----------
    def draw_side_panels(self):
        pygame.draw.rect(self.screen, (0, 0, 0), (0, 0, SIDE_PANEL_PX, SCREEN_HEIGHT))
        pygame.draw.rect(self.screen, (0, 0, 0), (SCREEN_WIDTH - SIDE_PANEL_PX, 0, SIDE_PANEL_PX, SCREEN_HEIGHT))

        h_box = pygame.Rect(10, 10, SIDE_PANEL_PX - 20, SIDE_PANEL_PX - 20)
        n_box = pygame.Rect(SCREEN_WIDTH - SIDE_PANEL_PX + 10, 10, SIDE_PANEL_PX - 20, SIDE_PANEL_PX - 20)
        for b in (h_box, n_box): pygame.draw.rect(self.screen, (255, 255, 255), b, 3)

        if self.hold_piece: self.draw_preview(self.hold_piece, h_box)
        self.draw_preview(self.next_piece, n_box)

        #顯示分數
        font = pygame.font.SysFont(None, 21)
        info_y = n_box.bottom + 30
        for txt in (f"Score : {self.score}", f"Level : {self.level}"):
            self.screen.blit(font.render(txt, True, (255, 255, 255)),
                             (SCREEN_WIDTH - SIDE_PANEL_PX + 10, info_y))
            info_y += 30

        # 說明文字
        font = pygame.font.SysFont(None, 18)
        guide_y = 100
        lines = [
            "Normal",
            "1Line : 1",
            "2Line : 3",
            "3Line : 5",
            "4Line : 8",
            "",
            "T-Spin",
            "Double : 12",
            "Triple : 36",
            "",
            "BTB : + 50%"
        ]
        for line in lines:
            self.screen.blit(font.render(line, True, (200, 200, 200)), (10, guide_y))
            guide_y += 25

        # --- 閃現分數 ---
        now = pygame.time.get_ticks()
        if self.flash_points and now - self.flash_start_time <= self.flash_duration_ms:
            flash_txt = f"+{self.flash_points}"
            flash_font = pygame.font.SysFont(None, 24, bold=True)

            # 放在 Score 下面再往右邊縮一點，避免文字重疊
            self.screen.blit(
                flash_font.render(flash_txt, True, (255, 220, 0)),
                (SCREEN_WIDTH - SIDE_PANEL_PX + 40, info_y)   # info_y 是上一段邏輯累加後的位置
            )
        else:
            self.flash_points = 0       # 時間到 → 清空

    def draw_preview(self, piece, box):
        s = (box.width - 10) // 4
        ox = box.x + (box.width - len(piece.matrix[0]) * s) // 2
        oy = box.y + (box.height - len(piece.matrix) * s) // 2 + s
        for r, row in enumerate(piece.matrix):
            for c, v in enumerate(row):
                if v:
                    img = pygame.transform.scale(tetromino.BLOCK_IMAGES[v], (s, s))
                    self.screen.blit(img, (ox + c * s, oy + r * s))

    def render(self):
        self.screen.fill((0, 0, 0))
        self.board.draw(self.screen, BOARD_OFFSET_X, BOARD_OFFSET_Y)
        for x, y, v in self.current.get_cells():
            if y >= 0:
                self.screen.blit(tetromino.BLOCK_IMAGES[v],
                                 (BOARD_OFFSET_X + x * CELL_SIZE, BOARD_OFFSET_Y + y * CELL_SIZE))
        self.draw_side_panels()
        pygame.draw.rect(self.screen, (255, 255, 255),
                         pygame.Rect(SIDE_PANEL_PX, 18.3, BOARD_WIDTH_PX, BOARD_HEIGHT_PX + 10.5), 3)
        pygame.display.flip()

    # ---------- GAME OVER ----------
    def game_over(self):
        f = pygame.font.SysFont(None, 72)
        r = f.render("GAME OVER", True, (255, 0, 0))
        self.screen.blit(r, r.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)))
        pygame.display.flip()
        pygame.time.wait(2000)
        self.in_game = False


def main():  # entry
    TetrisGame()


if __name__ == "__main__":
    main()
