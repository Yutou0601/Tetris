import pygame, sys, random, os, time
import settings as cfg                                       # 即時讀寫 MUSIC_ON / SFX_ON
from settings import *
import tetromino
from tetromino import random_tetromino
from board import Board
from ui import MenuUI, SettingUI

# 連續平移
DAS_DELAY = 200          # ms
ARR_SPEED = 40           # ms

class TetrisGame:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Tetris")
        self.clock = pygame.time.Clock()

        # 影像資源
        tetromino.BLOCK_IMAGES = tetromino.load_block_images()
        self.load_background()

        # 音樂
        self.music_list = MUSIC_FILES
        self.music_index = 0
        pygame.mixer.music.set_endevent(pygame.USEREVENT+1)
        self.play_music()

        # 音效
        sfx_dir = os.path.join(os.path.dirname(__file__), "Sound_effect")
        self.sfx_put   = pygame.mixer.Sound(os.path.join(sfx_dir, "put_on_top.mp3")) \
                         if os.path.exists(os.path.join(sfx_dir, "put_on_top.mp3")) else None
        self.sfx_clear = pygame.mixer.Sound(os.path.join(sfx_dir, "break.mp3")) \
                         if os.path.exists(os.path.join(sfx_dir, "break.mp3")) else None

        # 控制鍵 / DAS
        self.keys = DEFAULT_KEYS
        self.move_dir = 0
        self.das_timer = self.arr_timer = 0

        # 遊戲狀態
        self.board = Board()
        self.current_piece = random_tetromino()
        self.next_piece = random_tetromino()
        self.hold_piece = None
        self.hold_locked = False
        self.drop_timer = pygame.time.get_ticks()
        self.fall_speed = 500  # ms

        self.run_menu()

    # ---------- 資源 ----------
    def load_background(self):
        bg_path = os.path.join(ASSET_DIR, "background.png")
        self.board_bg = None
        if os.path.exists(bg_path):
            img = pygame.image.load(bg_path).convert_alpha()
            target_w = BOARD_WIDTH_PX + FRAME_BORDER*2
            target_h = BOARD_HEIGHT_PX + FRAME_BORDER*2
            self.board_bg = pygame.transform.scale(img, (target_w, target_h))

    def play_music(self):
        if not self.music_list or not cfg.MUSIC_ON:
            pygame.mixer.music.stop()
            return
        pygame.mixer.music.load(self.music_list[self.music_index])
        pygame.mixer.music.play()
        self.music_index = (self.music_index + 1) % len(self.music_list)

    # ---------- 主選單 ----------
    def run_menu(self):
        menu = MenuUI(self.screen)
        while True:
            choice = menu.run()
            if choice == 0:
                self.reset_game()
                self.game_loop()
            elif choice == 1:
                SettingUI(self.screen, self.keys).run()
            elif choice == 2:
                pygame.quit(); sys.exit()

    def reset_game(self):
        self.board = Board()
        self.current_piece = random_tetromino()
        self.next_piece = random_tetromino()
        self.hold_piece = None
        self.hold_locked = False
        self.drop_timer = pygame.time.get_ticks()

    # ---------- 方塊操作 ----------
    def spawn_piece(self):
        self.current_piece = self.next_piece
        self.next_piece = random_tetromino()
        self.current_piece.x = BOARD_COLS // 2 - len(self.current_piece.matrix[0]) // 2
        self.current_piece.y = -2
        self.hold_locked = False
        if not self.board.valid_position(self.current_piece):
            self.game_over()

    def hold_current(self):
        if self.hold_locked: return
        if self.hold_piece is None:
            self.hold_piece = self.current_piece
            self.spawn_piece()
        else:
            self.current_piece, self.hold_piece = self.hold_piece, self.current_piece
            self.current_piece.x = BOARD_COLS//2 - len(self.current_piece.matrix[0])//2
            self.current_piece.y = -2
        self.hold_locked = True

    def hard_drop(self):
        while self.board.valid_position(self.current_piece, dy=1):
            self.current_piece.y += 1
        self.lock_piece()

    def lock_piece(self):
        cleared = self.board.lock_piece(self.current_piece)
        if cleared == -1:
            self.game_over(); return
        if cfg.SFX_ON and self.sfx_put:   self.sfx_put.play()
        if cleared>0 and cfg.SFX_ON and self.sfx_clear: self.sfx_clear.play()
        self.spawn_piece()

    # ---------- 遊戲迴圈 ----------
    def game_loop(self):
        self.spawn_piece()
        while True:
            dt = self.clock.tick(FPS)
            for e in pygame.event.get():
                if e.type == pygame.QUIT: pygame.quit(); sys.exit()
                if e.type == pygame.USEREVENT+1: self.play_music()

                if e.type == pygame.KEYDOWN:
                    if e.key == self.keys["LEFT"]:
                        self.move_dir = -1; self.move(-1)
                        self.das_timer = self.arr_timer = pygame.time.get_ticks()
                    elif e.key == self.keys["RIGHT"]:
                        self.move_dir = 1;  self.move(1)
                        self.das_timer = self.arr_timer = pygame.time.get_ticks()
                    elif e.key == self.keys["DOWN"]:      self.soft_drop()
                    elif e.key == self.keys["ROTATE"]:    self.rotate()
                    elif e.key == self.keys["HARD_DROP"]: self.hard_drop()
                    elif e.key == self.keys["HOLD"]:      self.hold_current()
                    elif e.key == pygame.K_ESCAPE:        return
                if e.type == pygame.KEYUP and e.key in (self.keys["LEFT"], self.keys["RIGHT"]):
                    self.move_dir = 0

            # DAS / ARR
            if self.move_dir:
                now = pygame.time.get_ticks()
                if now - self.das_timer >= DAS_DELAY and now - self.arr_timer >= ARR_SPEED:
                    self.move(self.move_dir); self.arr_timer = now

            # Gravity
            if pygame.time.get_ticks() - self.drop_timer > self.fall_speed:
                self.soft_drop(); self.drop_timer = pygame.time.get_ticks()

            self.render()

    # ---------- 操作輔助 ----------
    def move(self, dx):
        if self.board.valid_position(self.current_piece, dx=dx): self.current_piece.x += dx
    def soft_drop(self):
        if self.board.valid_position(self.current_piece, dy=1): self.current_piece.y += 1
        else: self.lock_piece()
    def rotate(self):
        self.current_piece.rotate()
        if not self.board.valid_position(self.current_piece):
            if self.board.valid_position(self.current_piece, dx=-1): self.current_piece.x -= 1
            elif self.board.valid_position(self.current_piece, dx=1): self.current_piece.x += 1
            else: [self.current_piece.rotate() for _ in range(3)]

    # ---------- 繪圖 ----------
    def draw_side_panels(self):
        pygame.draw.rect(self.screen, (0,0,0), (0,0,SIDE_PANEL_PX,SCREEN_HEIGHT))
        pygame.draw.rect(self.screen, (0,0,0), (SCREEN_WIDTH-SIDE_PANEL_PX,0,SIDE_PANEL_PX,SCREEN_HEIGHT))
        # Hold
        h_box = pygame.Rect(10,10,SIDE_PANEL_PX-20,SIDE_PANEL_PX-20)
        n_box = pygame.Rect(SCREEN_WIDTH-SIDE_PANEL_PX+10,10,SIDE_PANEL_PX-20,SIDE_PANEL_PX-20)
        for box in (h_box, n_box): pygame.draw.rect(self.screen,(255,255,255),box,3)
        if self.hold_piece: self.draw_preview(self.hold_piece,h_box)
        self.draw_preview(self.next_piece,n_box)

    def draw_preview(self,piece,box):
        scale=(box.width-10)//4
        ox=box.x+(box.width-len(piece.matrix[0])*scale)//2
        oy=box.y+(box.height-len(piece.matrix)*scale)//2
        for r,row in enumerate(piece.matrix):
            for c,v in enumerate(row):
                if v: self.screen.blit(pygame.transform.scale(tetromino.BLOCK_IMAGES[v],(scale,scale)),(ox+c*scale,oy+r*scale))

    def draw_current(self):
        for x,y,v in self.current_piece.get_cells():
            if y>=0:
                self.screen.blit(tetromino.BLOCK_IMAGES[v],(BOARD_OFFSET_X+x*CELL_SIZE,BOARD_OFFSET_Y+y*CELL_SIZE))

    def render(self):
        self.screen.fill((0,0,0))
        self.board.draw(self.screen,BOARD_OFFSET_X,BOARD_OFFSET_Y)
        self.draw_current()
        self.draw_side_panels()
        pygame.draw.rect(self.screen,(255,255,255),pygame.Rect(SIDE_PANEL_PX,18.3,BOARD_WIDTH_PX,BOARD_HEIGHT_PX+10.5),3)
        pygame.display.flip()

    # ---------- 結束 ----------
    def game_over(self):
        f=pygame.font.SysFont(None,72)
        self.screen.blit(f.render("GAME OVER",True,(255,0,0)),
                         (SCREEN_WIDTH//2-150,SCREEN_HEIGHT//2-40))
        pygame.display.flip(); pygame.time.wait(2000)

def main(): TetrisGame()
if __name__=="__main__": main()
