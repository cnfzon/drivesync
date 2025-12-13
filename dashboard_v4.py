import sys, math, signal
import pygame
import vgamepad as vg

# ----------------- 初始化 -----------------
pygame.init()
W, H = 1200, 650
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("DriveSync Dashboard")
clock = pygame.time.Clock()

font_xl = pygame.font.SysFont("consolas", 56, bold=True)
font_lg = pygame.font.SysFont("consolas", 44, bold=True)
font_md = pygame.font.SysFont("consolas", 28, bold=True)
font_sm = pygame.font.SysFont("consolas", 20)
font_ti = pygame.font.SysFont("consolas", 18)

BG      = (10,10,14)
FG      = (230,235,245)
ACCENT  = (90,180,255)
AMBER   = (237,168,57)
RED     = (234,66,66)
SUB     = (170,180,195)
BORDER  = (38,42,50)
BAR     = (36,40,48)
GREEN   = (78,212,140)

pad = vg.VX360Gamepad()

def cleanup(*_):
    try:
        pad.reset(); pad.update()
    finally:
        pygame.quit(); sys.exit(0)

signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

# ----------------- 狀態變數 -----------------
steer_raw = 0          # -32768..32767 給手把用
throttle  = 0          # 0..255
brake     = 0          # 0..255
gear      = 1          # 1..7
rpm       = 900
speed_kmh = 0.0
coolant   = 85.0
battery_v = 12.4

# 物理模型參數（只是 demo，不是物理正確）
GEAR_ACCEL = [0.0, 5.0, 4.0, 3.0, 2.3, 1.7, 1.3, 1.0]
GEAR_RPM_K = [0.0,140.0,120.0,100.0, 90.0,80.0,72.0,66.0]

def clamp(x, lo, hi): return max(lo, min(hi, x))

# ----------------- 小工具 -----------------
def draw_text(txt, f, x, y, color=FG, center=False):
    surf = f.render(txt, True, color)
    rect = surf.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    screen.blit(surf, rect)

def draw_rect(x,y,w,h,fill,border_color=BORDER, radius=12):
    pygame.draw.rect(screen, border_color, (x,y,w,h), border_radius=radius)
    pygame.draw.rect(screen, fill, (x+2,y+2,w-4,h-4), border_radius=radius)

# ----------------- 速度表（中間大顆） -----------------
def draw_speed_gauge(cx, cy, r, speed):
    # 半圓背景
    pygame.draw.circle(screen, (30,32,38), (cx,cy), r+10, width=14)
    start = math.radians(210)   # 左邊
    end   = math.radians(-30)   # 右邊
    pygame.draw.arc(screen, AMBER, (cx-r, cy-r, 2*r, 2*r), start, end, 26)

    # 刻度 0~260 km/h
    max_spd = 260
    step = 20
    for v in range(0, max_spd+1, step):
        ang = math.radians(210 + (v/max_spd)*240)
        x1 = cx + int((r-8) * math.cos(ang))
        y1 = cy + int((r-8) * math.sin(ang))
        x2 = cx + int((r-36) * math.cos(ang))
        y2 = cy + int((r-36) * math.sin(ang))
        pygame.draw.line(screen, FG if v%40==0 else SUB, (x1,y1), (x2,y2), 2)
        if v % 40 == 0:
            lx = cx + int((r-60) * math.cos(ang))
            ly = cy + int((r-60) * math.sin(ang))
            draw_text(str(v//10), font_sm, lx-8, ly-8, FG)

    # 指針
    spd_clamp = clamp(speed, 0, max_spd)
    ang = math.radians(210 + (spd_clamp/max_spd)*240)
    px = cx + int((r-70) * math.cos(ang))
    py = cy + int((r-70) * math.sin(ang))
    pygame.draw.line(screen, ACCENT, (cx,cy), (px,py), 8)
    pygame.draw.circle(screen, (240,240,240), (cx,cy), 10)

    # 中央：數字速度
    draw_text(str(int(speed)), font_xl, cx, cy-35, FG, center=True)
    draw_text("km/h", font_md, cx+90, cy-10, FG)
    draw_text("Speed", font_sm, cx, cy+30, SUB, center=True)

# ----------------- 轉速表（右側縮小） -----------------
def draw_tacho_small(cx, cy, r, rpm, gear):
    # 背景弧 0~8000
    pygame.draw.circle(screen, (30,32,38), (cx,cy), r+6, width=10)
    start = math.radians(210)
    end   = math.radians(-30)
    pygame.draw.arc(screen, AMBER, (cx-r, cy-r, 2*r, 2*r), start, end, 18)

    red_s = math.radians(210 + (7000/8000.0)*240)
    red_e = math.radians(210 + (8000/8000.0)*240)
    pygame.draw.arc(screen, RED, (cx-r, cy-r, 2*r, 2*r), red_s, red_e, 20)

    for i in range(0,9):
        ang = math.radians(210 + (i/8)*240)
        x1 = cx + int((r-6) * math.cos(ang))
        y1 = cy + int((r-6) * math.sin(ang))
        x2 = cx + int((r-22)* math.cos(ang))
        y2 = cy + int((r-22)* math.sin(ang))
        pygame.draw.line(screen, FG if i%2==0 else SUB, (x1,y1), (x2,y2), 2)

    # 指針
    ratio = clamp(rpm,0,8000)/8000.0
    ang = math.radians(210 + ratio*240)
    px = cx + int((r-35) * math.cos(ang))
    py = cy + int((r-35) * math.sin(ang))
    pygame.draw.line(screen, ACCENT, (cx,cy), (px,py), 6)
    pygame.draw.circle(screen, (240,240,240), (cx,cy), 8)
    draw_text(f"{int(rpm):d} RPM", font_sm, cx-55, cy+34, FG)
    draw_text(f"G{gear if gear>0 else 0}", font_sm, cx+36, cy-40, ACCENT)

# ----------------- 油門 / 煞車條 -----------------
def draw_throttle_brake_bars(x, y, w, h, thr, brk):
    draw_rect(x, y, w, h, BAR)
    th = int((h-8) * (thr/255.0))
    pygame.draw.rect(screen, GREEN, (x+4, y+h-4-th, w-8, th), border_radius=8)
    draw_text("Throttle", font_sm, x-4, y+h+10, SUB)

    draw_rect(x+115, y, w, h, BAR)
    bh = int((h-8) * (brk/255.0))
    pygame.draw.rect(screen, RED, (x+119, y+h-4-bh, w-8, bh), border_radius=8)
    draw_text("Brake", font_sm, x+118, y+h+10, SUB)

# ----------------- 其它小 UI -----------------
def draw_bottom(speed, coolant, battery_v):
    # 左下水溫
    draw_text(f"{int(coolant)}°C", font_lg, 60, H-120, FG)
    # 右下電壓 + 小綠條
    draw_text(f"{battery_v:4.1f} V", font_sm, W-150, H-80, SUB)
    for i in range(6):
        x = W-210 + i*16
        col = GREEN if i < 4 else (160,160,160)
        pygame.draw.rect(screen, col, (x, H-60, 12, 26))

# ----------------- 主迴圈 -----------------
space = False; lshift = False
start_ms = pygame.time.get_ticks()

while True:
    dt = clock.tick(60) / 1000.0
    for e in pygame.event.get():
        if e.type == pygame.QUIT: cleanup()
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE: cleanup()
            if e.key == pygame.K_LEFT:  steer_raw = clamp(steer_raw-6000, -32768, 32767)
            if e.key == pygame.K_RIGHT: steer_raw = clamp(steer_raw+6000, -32768, 32767)
            if e.key == pygame.K_SPACE: space = True        # 空白鍵 = 油門
            if e.key == pygame.K_LSHIFT: lshift = True      # 左 Shift = 煞車
            if e.key == pygame.K_z:      gear = clamp(gear+1, 0, 7)
            if e.key == pygame.K_x:      gear = clamp(gear-1, 0, 7)
        if e.type == pygame.KEYUP:
            if e.key == pygame.K_SPACE:  space = False
            if e.key == pygame.K_LSHIFT: lshift = False

    # 踏板狀態
    throttle = 255 if space else max(0, throttle - int(220*dt))
    brake    = 255 if lshift else max(0, brake   - int(260*dt))

    # 簡易速度 / 轉速模型
    a = GEAR_ACCEL[gear] * (throttle/255.0) - (0.9 + 0.002*speed_kmh) - (brake/255.0)*8.0
    speed_kmh = clamp(speed_kmh + a*12.0*dt, 0.0, 320.0)

    base = speed_kmh * (GEAR_RPM_K[gear] if gear>0 else 60.0)
    rpm_target = clamp(900 + base + (throttle/255.0)*800, 900, 8000)
    rpm += (rpm_target - rpm) * min(1.0, 6.0*dt)

    coolant += (0.02 if throttle>0 else -0.015) * (60*dt)
    coolant = clamp(coolant, 70, 105)
    battery_v += (0.0005 if throttle==0 else -0.0007) * (60*dt)
    battery_v = clamp(battery_v, 11.8, 12.8)

    # 餵給虛擬手把（Forza 用）
    pad.left_joystick(x_value=steer_raw, y_value=0)
    pad.right_trigger(value=throttle)
    pad.left_trigger(value=brake)
    pad.update()

    # ------------- 繪圖 -------------
    screen.fill(BG)
    draw_text("DriveSync Telemetry HUD", font_lg, 20, 15, ACCENT)

    # 左：油門 / 煞車
    draw_throttle_brake_bars(90, 250, 80, 260, throttle, brake)

    # 中：速度表
    draw_speed_gauge(W//2, 320, 210, speed_kmh)

    # 右：小轉速表
    draw_tacho_small(W-230, 250, 130, rpm, gear)

    # 底部資訊
    draw_bottom(speed_kmh, coolant, battery_v)
    draw_text(f"FPS: {int(clock.get_fps())}", font_sm, 20, H-40, SUB)
    draw_text("Mode: Keyboard", font_sm, 20, H-20, ACCENT)

    pygame.display.flip()
