#!/usr/bin/env python3
# Volleyball Mobile 1v1 (v27) — Buildozer-ready (SDL2/pygame)

import math, random, sys
from array import array
import pygame

pygame.init()
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
pygame.display.set_caption("Volleyball")
clock = pygame.time.Clock()

PHONE_W, PHONE_H = screen.get_size()
BASE_H = 1080.0
SCALE = PHONE_H / BASE_H
def S(v): return int(v * SCALE)

# Fonts
font = pygame.font.SysFont("arial", S(28), bold=True)
big_font = pygame.font.SysFont("arial", S(64), bold=True)
title_font = pygame.font.SysFont("arial", S(88), bold=True)
mono = pygame.font.SysFont("consolas", S(22))

# Colors
NET_COLOR = (40, 40, 40)
BG_COLOR = (242, 245, 250)
COURT_LEFT_COLOR = (228, 240, 255)
COURT_RIGHT_COLOR = (255, 235, 228)
LINE_COLOR = (210, 210, 210)
UI_BG = (18,22,28,170)
BTN_FACE = (245, 248, 255)
BTN_FACE_PRESSED = (228, 236, 255)
BTN_OUTLINE = (60, 100, 255)
BTN_ICON = (40, 60, 140)
BTN_TEXT = (25, 40, 120)

# Physics
FPS = 120
PLAYER_SPEED = 520.0
PLAYER_JUMP_VY = -1500.0
PLAYER_GRAV = 3000.0
GRAVITY = 1450.0
HIT_POWER_PERFECT = 1240.0
BASE_HORIZ_SPEED_PERFECT = 620.0
SET_TO_SPIKE_TIME = 0.62
SPIKE_DOWN_VY = 1500.0
MIN_SPIKE_VX = 600.0

PLAYER_RADIUS = S(40)
BALL_RADIUS = S(12)

NET_TOP_Y = S(350)
CEIL_Y = S(20)
WALL_DAMP = 0.9

MAX_TOUCHES = 3
WIN_SCORE = 25

def CONTACT_Y(py): return py - (PLAYER_RADIUS + BALL_RADIUS)
GOOD_Y_WINDOW = S(48)
X_ALIGN_WINDOW = int(PLAYER_RADIUS * 1.18)
SPIKE_REACH_BONUS = S(70)

AI_REACTION_TIME = 0.07
AI_NOISE_STD = 16.0
AI_PRESS_FAIL_CHANCE = 0.055
AI_SLOP_EXTRA = S(6)
AI_MOVE_SPEED_FACTOR = 1.16

SND_RATE = 22050
try:
    pygame.mixer.pre_init(SND_RATE, -16, 1, 256)
    pygame.mixer.init()
    MIXER_OK = True
except Exception:
    MIXER_OK = False

def synth_tone(freq=440.0, ms=120, vol=0.35):
    if not MIXER_OK:
        return None
    n = int(SND_RATE * (ms/1000.0))
    buf = array('h')
    amp = int(32767 * max(0.0, min(1.0, vol)))
    for i in range(n):
        t = i / SND_RATE
        env = max(0.0, 1.0 - (i / n))
        s = int(amp * env * math.sin(2*math.pi*freq*t))
        buf.append(s)
    try:
        return pygame.mixer.Sound(buffer=buf.tobytes())
    except Exception:
        return None

sfx_spike = synth_tone(220, 120, 0.45)
sfx_set = synth_tone(880, 70, 0.25)
sfx_bounce = synth_tone(320, 60, 0.30)
sfx_point = synth_tone(660, 160, 0.45)
sfx_ui = synth_tone(520, 80, 0.3)
def play(s): 
    if MIXER_OK and s is not None: s.play()

class Player:
    def __init__(self, x, min_x, max_x, ground_y, is_left=True, color=(30,144,255), human=False):
        self.x=x; self.y=ground_y; self.vy=0.0
        self.color=color; self.is_left=is_left
        self.min_x_val=min_x; self.max_x_val=max_x
        self.ground_y=ground_y; self.human=human
    @property
    def min_x(self): return self.min_x_val
    @property
    def max_x(self): return self.max_x_val
    @property
    def on_ground(self): return abs(self.y-self.ground_y)<0.5 and self.vy==0.0
    def jump(self):
        if self.on_ground: self.vy=PLAYER_JUMP_VY
    def update(self, dt, dir_x):
        self.x=max(self.min_x, min(self.max_x, self.x+dir_x*PLAYER_SPEED*dt))
        if not self.on_ground or self.vy!=0.0:
            self.vy+=PLAYER_GRAV*dt; self.y+=self.vy*dt
            if self.y>self.ground_y: self.y=self.ground_y; self.vy=0.0
    def draw(self, s):
        shadow_y=self.ground_y+PLAYER_RADIUS+S(6)
        h=max(0.0, min(1.0,(self.ground_y-self.y)/S(200)))
        sh_w=S(80)*(1-0.35*h)
        pygame.draw.ellipse(s,(0,0,0,40),pygame.Rect(self.x-sh_w/2,shadow_y-10,sh_w,20))
        pygame.draw.circle(s,self.color,(int(self.x),int(self.y)),PLAYER_RADIUS)
        if not self.on_ground:
            pygame.draw.circle(s,(255,255,255),(int(self.x),int(self.y)),PLAYER_RADIUS+2,2)

class Ball:
    def __init__(self,width,height,net_x,ground_y):
        self.width=width; self.height=height; self.net_x=net_x; self.ground_y=ground_y
        self.x=width/2; self.y=S(140); self.vx=0.0; self.vy=0.0
        self.prev_x=self.x; self.prev_y=self.y
        self.last_touch=None; self.last_action=None; self.touch_cooldown=0.0
        self.color=(50,50,50); self.trail=[]
    def reset_motion(self):
        self.vx=self.vy=0.0; self.prev_x=self.x; self.prev_y=self.y
        self.last_touch=None; self.last_action=None; self.touch_cooldown=0.0; self.trail.clear()
    def update(self, dt):
        self.prev_x=self.x; self.prev_y=self.y
        self.vy+=GRAVITY*dt; self.x+=self.vx*dt; self.y+=self.vy*dt
        if self.touch_cooldown>0: self.touch_cooldown-=dt
        spd=(self.vx*self.vx+self.vy*self.vy)**0.5
        k=max(0.2,min(0.9,spd/1500.0))
        self.trail.append((self.x,self.y,k))
        if len(self.trail)>14: self.trail.pop(0)
    def draw(self,s):
        for i,(tx,ty,a) in enumerate(self.trail):
            k=i/max(1,len(self.trail)-1); r=max(2,int(BALL_RADIUS*(0.4+0.6*k)))
            colv=int(40+150*(1-k)); col=(colv,colv,colv)
            pygame.draw.circle(s,col,(int(tx),int(ty)),r,1)
        shadow_y=self.ground_y+PLAYER_RADIUS+S(2)
        depth=max(0,min(1,(self.y-S(90))/(shadow_y-S(90)+1e-6)))
        sh_w=S(36)*(1-0.6*depth)
        pygame.draw.ellipse(s,(0,0,0,50),pygame.Rect(self.x-sh_w/2,shadow_y-6,sh_w,12))
        pygame.draw.circle(s,self.color,(int(self.x),int(self.y)),BALL_RADIUS,2)
        for i in (-S(5),0,S(5)):
            pygame.draw.line(s,self.color,(int(self.x-BALL_RADIUS+3),int(self.y+i)),
                             (int(self.x+BALL_RADIUS-3),int(self.y+i)),2)

def clamp(v,a,b): return max(a,min(b,v))

def draw_court(s,width,height,ground_y,net_x):
    pygame.draw.rect(s,COURT_LEFT_COLOR,pygame.Rect(0,ground_y-S(200),net_x,S(300)))
    pygame.draw.rect(s,COURT_RIGHT_COLOR,pygame.Rect(net_x,ground_y-S(200),width-net_x,S(300)))
    pygame.draw.line(s,LINE_COLOR,(0,ground_y+PLAYER_RADIUS),(width,ground_y+PLAYER_RADIUS),2)
    pygame.draw.line(s,NET_COLOR,(net_x,NET_TOP_Y),(net_x,ground_y+PLAYER_RADIUS),S(6))
    pygame.draw.line(s,(220,220,220),(net_x-S(22),NET_TOP_Y),(net_x+S(22),NET_TOP_Y),S(6))

flash_timer=0.0
def draw_flash(s):
    global flash_timer
    if flash_timer>0:
        a=int(180*(flash_timer/0.12))
        o=pygame.Surface((PHONE_W,PHONE_H),pygame.SRCALPHA); o.fill((255,255,255,a)); s.blit(o,(0,0))
        flash_timer-=1/FPS

def flash(): 
    global flash_timer; flash_timer=0.12

def run_menu():
    def rect(x,y,w,h): return pygame.Rect(x,y,w,h)
    buttons=[('play', rect(PHONE_W//2 - S(280), PHONE_H//2 - S(40), S(560), S(120))),
             ('quit', rect(PHONE_W//2 - S(280), PHONE_H//2 + S(110), S(560), S(120)))]
    while True:
        for e in pygame.event.get():
            if e.type==pygame.QUIT: return 'quit'
            if e.type==pygame.KEYDOWN:
                if e.key in (pygame.K_RETURN, pygame.K_SPACE): return 'play'
                if e.key==pygame.K_ESCAPE: return 'quit'
            if e.type==pygame.MOUSEBUTTONDOWN:
                mx,my=e.pos
                for name,r in buttons:
                    if r.collidepoint(mx,my):
                        return 'play' if name=='play' else 'quit'
        screen.fill((18,22,28))
        title=title_font.render("VOLLEYBALL", True, (240,245,255))
        screen.blit(title,(PHONE_W//2-title.get_width()//2, S(180)))
        sub=mono.render("1v1  •  Mobile controls", True, (210,215,225))
        screen.blit(sub,(PHONE_W//2-sub.get_width()//2, S(260)))
        for name,r in buttons:
            pygame.draw.rect(screen, (245,248,255), r, border_radius=S(28))
            pygame.draw.rect(screen, (60,100,255), r, S(4), border_radius=S(28))
            lab=big_font.render("Play" if name=='play' else "Quit", True, (25,40,120))
            screen.blit(lab,(r.centerx-lab.get_width()//2,r.centery-lab.get_height()//2))
        pygame.display.flip()

class Button:
    def __init__(self, rect): self.rect=rect; self.pressed=False
    def down(self,x,y): 
        if self.rect.collidepoint(x,y): self.pressed=True; return True
        return False
    def up(self): self.pressed=False

def run_match():
    PLAYER_RADIUS = S(40); BALL_RADIUS = S(12)
    BTN_MARGIN=S(26); BTN_W=S(200); BTN_H=S(160); PAD_H=S(240)
    left_btn=Button(pygame.Rect(BTN_MARGIN, PHONE_H-PAD_H+S(30), BTN_W, BTN_H))
    right_btn=Button(pygame.Rect(BTN_MARGIN+BTN_W+S(24), PHONE_H-PAD_H+S(30), BTN_W, BTN_H))
    action_btn=Button(pygame.Rect(PHONE_W-BTN_MARGIN-BTN_W, PHONE_H-PAD_H+S(30), BTN_W, BTN_H))
    jump_btn=Button(pygame.Rect(PHONE_W-BTN_MARGIN-BTN_W*2-S(24), PHONE_H-PAD_H+S(30), BTN_W, BTN_H))
    restart_btn=Button(pygame.Rect(S(20), S(18), S(100), S(80)))

    class P:
        def __init__(self,x,min_x,max_x,gy,is_left,color,human):
            self.x=x; self.y=gy; self.vy=0.0; self.min=min_x; self.max=max_x; self.gy=gy
            self.is_left=is_left; self.color=color; self.human=human
        def on_ground(self): return abs(self.y-self.gy)<0.5 and self.vy==0.0
        def jump(self): 
            if self.on_ground(): self.vy=-1500.0
        def update(self,dt,dx):
            self.x=max(self.min, min(self.max, self.x+dx*520.0*dt))
            if not self.on_ground() or self.vy!=0.0:
                self.vy+=3000.0*dt; self.y+=self.vy*dt
                if self.y>self.gy: self.y=self.gy; self.vy=0.0
        def draw(self,s):
            pygame.draw.circle(s,self.color,(int(self.x),int(self.y)),PLAYER_RADIUS)

    class B:
        def __init__(self,W,H,NX,GY):
            self.x=W/2; self.y=S(140); self.vx=0.0; self.vy=0.0; self.prev_x=self.x; self.prev_y=self.y
            self.net_x=NX; self.gy=GY
        def upd(self,dt):
            self.prev_x=self.x; self.prev_y=self.y
            self.vy+=1450.0*dt; self.x+=self.vx*dt; self.y+=self.vy*dt

    W,H=PHONE_W,PHONE_H; GY=H-PAD_H-S(60); NX=W//2
    LMIN=S(60); LMAX=NX-S(80); RMIN=NX+S(80); RMAX=W-S(60)
    player=P((LMIN+LMAX)/2,LMIN,LMAX,GY,True,(70,140,255),True)
    ai=P((RMIN+RMAX)/2,RMIN,RMAX,GY,False,(255,120,80),False)
    ball=B(W,H,NX,GY)

    left_score=right_score=0
    serve_to='left'
    def reset_ball(side):
        nonlocal ball,player,ai
        if side=='left':
            player.x=LMIN; ball.x=player.x
        else:
            ai.x=(RMIN+RMAX)/2; ball.x=ai.x
        ball.y=S(120); ball.vx=ball.vy=0.0

    reset_ball(serve_to)
    serve_wait=0.40
    touch={'left':0,'right':0}
    def reset_touches(n): touch['left']=0; touch['right']=0
    def reg(side):
        touch[side]+=1
        if touch[side]>3:
            add_point('right' if side=='left' else 'left')
            return False
        return True
    def add_point(who):
        nonlocal left_score,right_score,serve_to
        if who=='left': left_score+=1; serve_to='left'
        else: right_score+=1; serve_to='right'
        reset_ball(serve_to)

    space_buf=0.0

    while True:
        dt=clock.tick(FPS)/1000.0
        for e in pygame.event.get():
            if e.type==pygame.QUIT: return 'quit'
            if e.type==pygame.KEYDOWN:
                if e.key==pygame.K_ESCAPE: return 'menu'
                if e.key==pygame.K_r: reset_ball(serve_to)
                if e.key==pygame.K_SPACE: space_buf=0.16
                if e.key in (pygame.K_w, pygame.K_UP): player.jump()
            if e.type==pygame.MOUSEBUTTONDOWN:
                mx,my=e.pos
                if left_btn.down(mx,my): pass
                if right_btn.down(mx,my): pass
                if action_btn.down(mx,my): space_buf=0.16
                if jump_btn.down(mx,my): player.jump()
                if restart_btn.down(mx,my): reset_ball(serve_to)
            if e.type==pygame.MOUSEBUTTONUP:
                left_btn.up(); right_btn.up(); action_btn.up(); jump_btn.up(); restart_btn.up()

        move=0.0
        if left_btn.pressed and not right_btn.pressed: move=-1.0
        if right_btn.pressed and not left_btn.pressed: move=1.0
        keys=pygame.key.get_pressed()
        move += (1.0 if keys[pygame.K_d] or keys[pygame.K_RIGHT] else 0.0) - (1.0 if keys[pygame.K_a] or keys[pygame.K_LEFT] else 0.0)
        if keys[pygame.K_w] or keys[pygame.K_UP]: player.jump()
        if keys[pygame.K_SPACE]: space_buf=0.16

        player.update(dt, max(-1.0,min(1.0,move)))

        if serve_wait>0: serve_wait-=dt
        else:
            ball.upd(dt)
            if ball.x-BALL_RADIUS<0: ball.x=BALL_RADIUS; ball.vx=abs(ball.vx)*WALL_DAMP
            if ball.x+BALL_RADIUS>W: ball.x=W-BALL_RADIUS; ball.vx=-abs(ball.vx)*WALL_DAMP
            if ball.y+BALL_RADIUS>=GY+PLAYER_RADIUS:
                add_point('right' if ball.x<NX else 'left')
                serve_wait=0.40; reset_touches(0); continue
            crossed=(ball.prev_x<NX<=ball.x) or (ball.prev_x>NX>=ball.x)
            if crossed: reset_touches(0)

        if space_buf>0:
            did=False
            if not did and not player.on_ground() and ball.x<NX:
                dx=ball.x-player.x; dy=ball.y-player.y; reach=PLAYER_RADIUS+BALL_RADIUS+SPIKE_REACH_BONUS
                if dx*dx+dy*dy<=reach*reach:
                    if reg('left'):
                        ball.vy=SPIKE_DOWN_VY; ball.vx=max(600.0,(RMAX-ball.x)/0.3/2)
                        did=True
            if not did and ball.x<NX and abs(ball.x-player.x)<=X_ALIGN_WINDOW and player.on_ground():
                iy=CONTACT_Y(player.y)
                if abs(ball.y-iy)<= (GOOD_Y_WINDOW+S(6)):
                    if reg('left'):
                        t=SET_TO_SPIKE_TIME; tx=(NX-S(92)); ty=NET_TOP_Y+S(18)
                        ball.vx=(tx-ball.x)/t; ball.vy=(ty-ball.y-0.5*GRAVITY*t*t)/t
                        did=True
            space_buf=0.0 if did else (space_buf - dt)

        # Draw
        scene=pygame.Surface((PHONE_W,PHONE_H),pygame.SRCALPHA); scene.fill(BG_COLOR)
        pygame.draw.rect(scene,COURT_LEFT_COLOR,pygame.Rect(0,GY-S(200),NX,S(300)))
        pygame.draw.rect(scene,COURT_RIGHT_COLOR,pygame.Rect(NX,GY-S(200),W-NX,S(300)))
        pygame.draw.line(scene,LINE_COLOR,(0,GY+PLAYER_RADIUS),(W,GY+PLAYER_RADIUS),2)
        pygame.draw.line(scene,NET_COLOR,(NX,NET_TOP_Y),(NX,GY+PLAYER_RADIUS),S(6))
        pygame.draw.line(scene,(220,220,220),(NX-S(22),NET_TOP_Y),(NX+S(22),NET_TOP_Y),S(6))

        scene.blit(big_font.render(f"{left_score}  -  {right_score}",True,(20,20,20)), (W - S(200), S(24)))
        pad=pygame.Rect(0,H-PAD_H,W,PAD_H)
        pad_s=pygame.Surface((pad.w,pad.h),pygame.SRCALPHA); pad_s.fill(UI_BG); scene.blit(pad_s,pad.topleft)

        player.draw(scene)
        pygame.draw.circle(scene,(50,50,50),(int(ball.x),int(ball.y)),BALL_RADIUS,2)

        # Buttons
        for b,icon in [(left_btn,'<'),(right_btn,'>'),(action_btn,'SET'),(jump_btn,'JUMP')]:
            pygame.draw.rect(scene, BTN_FACE_PRESSED if b.pressed else BTN_FACE, b.rect, border_radius=S(24))
            pygame.draw.rect(scene, BTN_OUTLINE, b.rect, S(4), border_radius=S(24))
            lab = font.render(icon, True, BTN_TEXT)
            scene.blit(lab,(b.rect.centerx-lab.get_width()//2,b.rect.centery-lab.get_height()//2))
        pygame.draw.rect(scene, BTN_FACE, restart_btn.rect, border_radius=S(18))
        pygame.draw.rect(scene, BTN_OUTLINE, restart_btn.rect, S(4), border_radius=S(18))
        scene.blit(font.render("↻", True, BTN_TEXT), (restart_btn.rect.centerx - S(14), restart_btn.rect.centery - S(18)))

        draw_flash(scene)
        screen.fill((0,0,0)); screen.blit(scene,(0,0)); pygame.display.flip()

def main():
    cur='menu'
    while True:
        if cur=='menu':
            nxt=run_menu()
            if nxt=='play': cur='match'
            elif nxt=='quit': break
        elif cur=='match':
            nxt=run_match()
            if nxt=='menu': cur='menu'
            elif nxt=='quit': break
    pygame.quit()

if __name__ == "__main__":
    main()
