import pygame, sys, os
import settings as cfg
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, DEFAULT_KEYS, MUSIC_FILES

WHITE, YELLOW, BG = (255,255,255), (255,220,0), (25,25,25)

class Button:
    def __init__(self, txt, font, center):
        self.txt, self.font = txt, font
        self.rect = font.render(txt,True,WHITE).get_rect(center=center)
    def draw(self,surf,hover):
        surf.blit(self.font.render(self.txt,True,YELLOW if hover else WHITE),self.rect)

class MenuUI:
    def __init__(self,screen):
        self.s, self.clock = screen, pygame.time.Clock()
        f=pygame.font.SysFont(None,60)
        self.btn=[Button("Start",f,(SCREEN_WIDTH//2,SCREEN_HEIGHT//2-80)),
                  Button("Settings",f,(SCREEN_WIDTH//2,SCREEN_HEIGHT//2)),
                  Button("Quit",f,(SCREEN_WIDTH//2,SCREEN_HEIGHT//2+80))]
        bgp=os.path.join(os.path.dirname(__file__),"Material","main_background.jpg")
        self.bg=pygame.transform.scale(pygame.image.load(bgp),(SCREEN_WIDTH,SCREEN_HEIGHT)) if os.path.exists(bgp) else None
    def run(self):
        while True:
            self.clock.tick(FPS)
            for e in pygame.event.get():
                if e.type==pygame.QUIT: pygame.quit(); sys.exit()
                if e.type==pygame.MOUSEBUTTONDOWN and e.button==1:
                    for i,b in enumerate(self.btn):
                        if b.rect.collidepoint(e.pos): return i
            if self.bg: self.s.blit(self.bg,(0,0))
            else: self.s.fill((0,0,0))
            mp=pygame.mouse.get_pos()
            for b in self.btn: b.draw(self.s,b.rect.collidepoint(mp))
            pygame.display.flip()

class SettingUI():
    ACTIONS = ["LEFT", "RIGHT", "DOWN", "ROTATE", "HARD_DROP", "HOLD"]
    DIFFICULTY_LEVELS = ["Easy", "Normal", "Hard"] 

    def __init__(self, scr, keys_map):
        self.s, self.clock = scr, pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 32)
        self.keys = keys_map
        self.wait = None
        self.music_on, self.sfx_on = cfg.MUSIC_ON, cfg.SFX_ON
        self.difficulty_idx = cfg.DIFFICULTY_idx
        self.line_h, self.start_y = 48, 60
        self.back = Button("Back (Esc)", self.font, (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 20))

    def run(self):
        while True:
            self.clock.tick(FPS)
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    return
                if e.type == pygame.KEYDOWN and not self.wait and e.key == pygame.K_ESCAPE:
                    cfg.MUSIC_ON, cfg.SFX_ON = self.music_on, self.sfx_on
                    cfg.DIFFICULTY = self.DIFFICULTY_LEVELS[self.difficulty_idx]  # 記錄難度
                    return
                if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    mx, my = e.pos

                    # 拜託先判斷Back
                    if self.back.rect.collidepoint((mx, my)):
                        cfg.MUSIC_ON, cfg.SFX_ON = self.music_on, self.sfx_on
                        # 記錄難度
                        cfg.DIFFICULTY = self.DIFFICULTY_LEVELS[self.difficulty_idx]  
                        
                        return
                    
                    # 重綁按鍵
                    for i, a in enumerate(self.ACTIONS):
                        if pygame.Rect(60, self.start_y + i * self.line_h - 5, SCREEN_WIDTH - 120, self.line_h).collidepoint((mx, my)):
                            self.wait = a
                            break
                    # Music toggle
                    if pygame.Rect(60, self.start_y + len(self.ACTIONS) * self.line_h + 15, 300, self.line_h).collidepoint((mx, my)):
                        self.music_on = not self.music_on
                        if self.music_on:
                            if not pygame.mixer.music.get_busy() and MUSIC_FILES:
                                pygame.mixer.music.load(MUSIC_FILES[0])
                                pygame.mixer.music.play()
                            else:
                                pygame.mixer.music.unpause()
                        else:
                            pygame.mixer.music.pause()
                    # SFX toggle
                    if pygame.Rect(60, self.start_y + len(self.ACTIONS) * self.line_h + 65, 300, self.line_h).collidepoint((mx, my)):
                        self.sfx_on = not self.sfx_on
                    # 難度切換
                    if pygame.Rect(60, self.start_y + len(self.ACTIONS) * self.line_h + 115, 300, self.line_h).collidepoint((mx, my)):
                        self.difficulty_idx = (self.difficulty_idx + 1) % len(self.DIFFICULTY_LEVELS)

                if e.type == pygame.KEYDOWN and self.wait:
                    self.keys[self.wait] = e.key
                    self.wait = None

            # 畫面
            self.s.fill(BG)
            for i, a in enumerate(self.ACTIONS):
                
                label = f"{a:<10}: {pygame.key.name(self.keys[a])}" if self.wait != a else f"{a:<10}: Press new key..."
                col = YELLOW if self.wait == a else WHITE
                self.s.blit(self.font.render(label, True, col), (80, self.start_y + i * self.line_h))

            self.s.blit(self.font.render(f"Background Music: {'ON' if self.music_on else 'OFF'}", True, YELLOW if self.music_on else WHITE),
                         (80, self.start_y + len(self.ACTIONS) * self.line_h + 15))
            self.s.blit(self.font.render(f"Sound Effects: {'ON' if self.sfx_on else 'OFF'}", True, YELLOW if self.sfx_on else WHITE),
                         (80, self.start_y + len(self.ACTIONS) * self.line_h + 65))

            self.s.blit(self.font.render(f"Game Difficulty: {self.DIFFICULTY_LEVELS[self.difficulty_idx]}", True, WHITE),
            (80, self.start_y + len(self.ACTIONS) * self.line_h + 115))
            
            mp = pygame.mouse.get_pos()
            self.back.draw(self.s, self.back.rect.collidepoint(mp))
            pygame.display.flip()
