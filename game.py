import pygame, sys, random, os
import settings as cfg
from settings import *
import tetromino
from tetromino import random_tetromino
from board import Board
from ui import MenuUI, SettingUI

DAS_DELAY, ARR_SPEED = 200, 40

class TetrisGame:
    def __init__(self):
        pygame.init(); pygame.mixer.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Tetris")
        self.clock = pygame.time.Clock()

        tetromino.BLOCK_IMAGES = tetromino.load_block_images()
        self.music_list, self.music_idx = MUSIC_FILES, 0
        pygame.mixer.music.set_endevent(pygame.USEREVENT+1)
        self.play_music()

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
        self.music_idx = (self.music_idx+1) % len(self.music_list)

    # ---------- 主流程 ----------
    def run_menu(self):
        menu = MenuUI(self.screen)
        while True:                          # ← 這層迴圈永遠在等你回到選單
            opt = menu.run()
            if opt == 0: self.start_game()   # 如果 start_game() 正常結束，就會回到這裡
            elif opt == 1: SettingUI(self.screen, self.keys).run()
            else: pygame.quit(); sys.exit()

    def start_game(self):
        self.board = Board()
        self.current, self.next_piece = random_tetromino(), random_tetromino()
        self.hold_piece, self.hold_locked = None, False

        self.score = self.lines = self.level = 0
        self.fall_delay = 1000
        self.drop_timer = pygame.time.get_ticks()

        # ---- Lock delay ----
        self.lock_delay = 500  # ms
        self.lock_timer = None


        # 「遊戲進行中」旗標
        self.in_game = True  

        # ↓ 鍵狀態
        self.down_pressed = False
        self.down_start   = 0
        self.down_delay   = 120   # 首次加速值

        self.move_dir = self.das_timer = self.arr_timer = 0
        self.game_loop()        

    # ---------- 計分 & 升級 ----------
    def update_score(self, cleared):
        if not cleared: return
        self.score += {1:100,2:300,3:500,4:800}[cleared]*(self.level+1)
        self.lines += cleared
        if self.lines//10 > self.level:
            self.level += 1
            self.fall_delay = max(50, int(1000*(0.85**self.level)))  # 指數加速

    # ---------- 方塊操作 ----------
    def spawn_piece(self):
        self.current, self.next_piece = self.next_piece, random_tetromino()
        self.current.x = BOARD_COLS//2 - len(self.current.matrix[0])//2
        self.current.y = -2
        self.hold_locked=False
        if not self.board.valid_position(self.current): self.game_over()

    def hold(self):
        if self.hold_locked: return
        if self.hold_piece is None:
            self.hold_piece = self.current; self.spawn_piece()
        else:
            self.current, self.hold_piece = self.hold_piece, self.current
            self.current.x = BOARD_COLS//2 - len(self.current.matrix[0])//2
            self.current.y = -2
        self.hold_locked=True

    def hard_drop(self):
        while self.board.valid_position(self.current,dy=1): self.current.y+=1
        self.lock_piece()

    def lock_piece(self):
        cleared=self.board.lock_piece(self.current)
        if cleared==-1: self.game_over(); return
        if cfg.SFX_ON and self.sfx_put: self.sfx_put.play()
        if cleared and cfg.SFX_ON and self.sfx_clear: self.sfx_clear.play()
        self.update_score(cleared); self.spawn_piece()

    # ---------- 遊戲迴圈 ----------
    def game_loop(self):
        self.spawn_piece()
        while self.in_game:
            dt=self.clock.tick(FPS)
            for e in pygame.event.get():
                if e.type==pygame.QUIT: pygame.quit(); sys.exit()
                if e.type==pygame.USEREVENT+1: self.play_music()
                if e.type==pygame.KEYDOWN:
                    if e.key==self.keys["LEFT"]:  self.move_dir=-1; self.move(-1); self.das_timer=self.arr_timer=pygame.time.get_ticks()
                    elif e.key==self.keys["RIGHT"]: self.move_dir=1; self.move(1); self.das_timer=self.arr_timer=pygame.time.get_ticks()
                    elif e.key==self.keys["DOWN"]:
                        self.down_pressed=True
                        self.down_start=pygame.time.get_ticks()
                        self.down_delay=120
                    elif e.key==self.keys["ROTATE"]: self.rotate()
                    elif e.key==self.keys["HARD_DROP"]: self.hard_drop()
                    elif e.key==self.keys["HOLD"]: self.hold()
                    elif e.key==pygame.K_ESCAPE: 
                        self.in_game = False # ★ 按 ESC 也能安全跳回主選單
                        break
                if e.type==pygame.KEYUP:
                    if e.key in (self.keys["LEFT"], self.keys["RIGHT"]): self.move_dir=0
                    if e.key==self.keys["DOWN"]: self.down_pressed=False

            # DAS/ARR
            if self.move_dir:
                now=pygame.time.get_ticks()
                if now-self.das_timer>=DAS_DELAY and now-self.arr_timer>=ARR_SPEED:
                    self.move(self.move_dir); self.arr_timer=now

            # 自然下落
            now=pygame.time.get_ticks()
            if cfg.DIFFICULTY == "Easy":
                base_delay = 1500
            elif cfg.DIFFICULTY == "Normal":
                base_delay = 800
            elif cfg.DIFFICULTY == "Hard":
                base_delay = 200
            else:
                base_delay = 1500
            # 再根據等級做加速
            self.fall_delay = max(50, int(base_delay * (0.85**self.level)))
            delay = self.fall_delay
            if self.down_pressed:
                held = now - self.down_start
                self.down_delay = max(20, 120 - (held//200)*10)
                delay = self.down_delay
            if now - self.drop_timer > delay:
                self.soft_drop(); self.drop_timer = now

            self.render()

    # ---------- 操作輔助 ----------
    
    def move(self, dx):
        if self.board.valid_position(self.current, dx=dx):
            self.current.x += dx
            self.lock_timer = None

    
    def soft_drop(self):
        """重力 / 快速下落；含 lock delay 邏輯"""
        if self.board.valid_position(self.current, dy=1):
            # 還能往下 → 移動並取消 lock timer
            self.current.y += 1
            self.lock_timer = None
        else:
            now = pygame.time.get_ticks()
            if self.lock_timer is None:
                self.lock_timer = now
            elif now - self.lock_timer >= self.lock_delay:
                self.lock_piece()

    
    # ---------- 操作輔助 ----------
    def rotate(self, dir=1):
        if self.current.rotate(dir, self.board):
            self.lock_timer = None

    # ---------- 繪圖 ----------

    def draw_side_panels(self):
        pygame.draw.rect(self.screen,(0,0,0),(0,0,SIDE_PANEL_PX,SCREEN_HEIGHT))
        pygame.draw.rect(self.screen,(0,0,0),(SCREEN_WIDTH-SIDE_PANEL_PX,0,SIDE_PANEL_PX,SCREEN_HEIGHT))
        h_box=pygame.Rect(10,10,SIDE_PANEL_PX-20,SIDE_PANEL_PX-20)
        n_box=pygame.Rect(SCREEN_WIDTH-SIDE_PANEL_PX+10,10,SIDE_PANEL_PX-20,SIDE_PANEL_PX-20)
        for b in(h_box,n_box): pygame.draw.rect(self.screen,(255,255,255),b,3)
        if self.hold_piece: self.draw_preview(self.hold_piece,h_box)
        self.draw_preview(self.next_piece,n_box)
        font=pygame.font.SysFont(None,21)
        info_y=n_box.bottom+30
        for txt in (f"S : {self.score}", f"L : {self.level}"):
            self.screen.blit(font.render(txt,True,(255,255,255)),(SCREEN_WIDTH-SIDE_PANEL_PX+10,info_y)); info_y+=30

    def draw_preview(self,piece,box):
        s=(box.width-10)//4
        ox=box.x+(box.width-len(piece.matrix[0])*s)//2
        oy=box.y+(box.height-len(piece.matrix)*s)//2
        for r,row in enumerate(piece.matrix):
            for c,v in enumerate(row):
                if v: self.screen.blit(pygame.transform.scale(tetromino.BLOCK_IMAGES[v],(s,s)),(ox+c*s,oy+r*s))

    def render(self):
        self.screen.fill((0,0,0))
        self.board.draw(self.screen,BOARD_OFFSET_X,BOARD_OFFSET_Y)
        for x,y,v in self.current.get_cells():
            if y>=0:
                self.screen.blit(tetromino.BLOCK_IMAGES[v],
                                 (BOARD_OFFSET_X+x*CELL_SIZE,BOARD_OFFSET_Y+y*CELL_SIZE))
        self.draw_side_panels()
        pygame.draw.rect(self.screen,(255,255,255),pygame.Rect(SIDE_PANEL_PX,18.3,BOARD_WIDTH_PX,BOARD_HEIGHT_PX+10.5),3)
        pygame.display.flip()

    # ---------- 結束 ----------
    def game_over(self):
        f=pygame.font.SysFont(None,72)
        r=f.render("GAME OVER",True,(255,0,0))
        self.screen.blit(r,r.get_rect(center=(SCREEN_WIDTH//2,SCREEN_HEIGHT//2)))
        pygame.display.flip()
        pygame.time.wait(2000)  
        self.in_game = False
        
def main(): TetrisGame()
if __name__=="__main__": main()
