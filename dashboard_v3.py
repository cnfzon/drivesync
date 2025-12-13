import sys, time, math, signal
import pygame
import vgamepad as vg

# ---------- 基本初始化 ----------
pygame.init()
W, H = 1100, 640
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("DriveSync Dashboard")
clock = pygame.time.Clock()

font_xl = pygame.font.SysFont("Eurostile,consolas", 56, bold=True)
font_lg = pygame.font.SysFont("Eurostile,consolas", 44, bold=True)
font_md = pygame.font.SysFont("Eurostile,consolas", 28, bold=True)
font_sm = pygame.font.SysFont("Eurostile,consolas", 20)
font_ti = pygame.font.SysFont("Eurostile,consolas", 18)

BG      = (10,10,14)
FG      = (230,235,245)
ACCENT  = (90,180,255)
AMBER   = (237, 168, 57)
RED     = (234, 66, 66)
SUB     = (170,180,195)
BORDER  = (38,42,50)
BAR     = (36,40,48)
GREEN   = (78,212,140)

# ---------- 虛擬手把 ----------
pad = vg.VX360Gamepad()

def cleanup(*_):
    try:
        pad.reset(); pad.update()
    finally:
        pygame.quit(); sys.exit(0)

signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

# ---------- 模擬狀態（鍵盤模式；之後你可換成 UDP 餵值） ----------
steer_raw = 0            # -32768..32767  (仍可保留，用於未來轉向視覺或校正頁)
throttle  = 0            # 0..255
brake     = 0            # 0..255
gear      = 1            # 1..7；Z升檔、X降檔；0 表示 N
rpm       = 900          # 轉速
speed_kmh = 0.0          # 時速
coolant   = 85.0         # 水溫℃
battery_v = 12.4         # 電壓
lap_ms    = 0            # 圈時
recording = False

# 檔位加速度係數與轉速映射（簡化的展示模型）
GEAR_ACCEL = [0.0, 5.0, 4.0, 3.0, 2.3, 1.7, 1.3, 1.0]         # index=檔位
GEAR_RPM_K = [0.0, 140.0, 120.0, 100.0, 90.0, 80.0, 72.0, 66.0]  # rpm 對應時速比例

# ---------- 小工具 ----------
def clamp(x, lo, hi): return max(lo, min(hi, x))
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

# ---------- 轉速錶（弧形 + 刻度 + 紅線） ----------
def draw_tacho(cx, cy, r, rpm, gear):
    # 背板
    pygame.draw.circle(screen, (30,32,38), (cx,cy), r+10, width=14)
    # 橘色區域 0~7000
    start = math.radians(220)     # 起點角度（螢幕座標）
    end   = math.radians(-40)     # 終點
    pygame.draw.arc(screen, AMBER, (cx-r, cy-r, 2*r, 2*r), start, end, 22)

    # 紅線區域 7000~8000
    red_s = math.radians(220 + (7000/8000.0)*260)
    red_e = math.radians(220 + (8000/8000.0)*260)
    pygame.draw.arc(screen, RED, (cx-r, cy-r, 2*r, 2*r), red_s, red_e, 24)

    # 刻度與數字 0~8
    for i in range(0, 9):
        a = math.radians(220 + (i/8)*260)
        x1 = cx + int((r-8) * math.cos(a))
        y1 = cy + int((r-8) * math.sin(a))
        x2 = cx + int((r-36) * math.cos(a))
        y2 = cy + int((r-36) * math.sin(a))
        pygame.draw.line(screen, FG if i%1==0 else SUB, (x1,y1), (x2,y2), 2)
        if i>0:
            lx = cx + int((r-58) * math.cos(a))
            ly = cy + int((r-58) * math.sin(a))
            draw_text(str(i), font_md, lx-8, ly-12, FG)

    # 指針 (rpm 0..8000 -> 角度 220°..-40°)
    ratio = clamp(rpm, 0, 8000) / 8000.0
    ang   = math.radians(220 + ratio*260)
    x = cx + int((r-70) * math.cos(ang))
    y = cy + int((r-70) * math.sin(ang))
    pygame.draw.line(screen, ACCENT, (cx,cy), (x,y), 8)
    pygame.draw.circle(screen, (240,240,240), (cx,cy), 10)

    # 中央區塊：檔位、轉速
    draw_text(str(gear if gear>0 else 0), font_xl, cx, cy-34, FG, center=True)
    draw_text(f"{int(rpm):d}", font_xl, cx, cy+18, FG, center=True)
    draw_text("RPM", font_sm, cx+78, cy+22, FG)

# ---------- 垂直條（時速、溫度、電量） ----------
def draw_stat_blocks(speed, coolant, batt):
    # 左下 85°C
    draw_text(f"{int(coolant):d}°C", font_lg, 70, H-140, FG)
    # 右下 224 km/h
    val = f"{int(speed):d} km/h"
    w = font_lg.size(val)[0]
    draw_text(val, font_lg, W-70-w, H-140, FG)

def draw_bottom_icons(x, y):
    # 略做幾個圓形/方形表示指示燈列
    r = 12
    gap = 38
    colors = [(120,120,120)]*8
    colors[3] = RED           # P（手煞車）示意
    for i,c in enumerate(colors):
        pygame.draw.circle(screen, c, (x+i*gap, y), r, 0 if i in (3,) else 2)

def draw_throttle_brake_bars(x, y, w, h, thr, brk):
    draw_rect(x, y, w, h, BAR);  # throttle
    th = int((h-8) * (thr/255.0))
    pygame.draw.rect(screen, GREEN, (x+4, y+h-4-th, w-8, th), border_radius=8)
    draw_text("Throttle", font_sm, x-2, y+h+10, SUB)

    draw_rect(x+120, y, w, h, BAR);  # brake
    bh = int((h-8) * (brk/255.0))
    pygame.draw.rect(screen, RED, (x+124, y+h-4-bh, w-8, bh), border_radius=8)
    draw_text("Brake", font_sm, x+118, y+h+10, SUB)

# ---------- 主要迴圈 ----------
space = False; lshift = False; a_btn=False; b_btn=False
start_ms = pygame.time.get_ticks()

while True:
    dt = clock.tick(60) / 1000.0  # 秒
    for e in pygame.event.get():
        if e.type == pygame.QUIT: cleanup()
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE: cleanup()
            if e.key == pygame.K_LEFT:  steer_raw = clamp(steer_raw - 6000, -32768, 32767)
            if e.key == pygame.K_RIGHT: steer_raw = clamp(steer_raw + 6000, -32768, 32767)
            if e.key == pygame.K_SPACE: space = True
            if e.key == pygame.K_LSHIFT: lshift = True
            if e.key == pygame.K_z:      gear = clamp(gear+1, 0, 7)  # 升檔
            if e.key == pygame.K_x:      gear = clamp(gear-1, 0, 7)  # 降檔
        if e.type == pygame.KEYUP:
            if e.key == pygame.K_SPACE:  space = False
            if e.key == pygame.K_LSHIFT: lshift = False

    # 踏板狀態（帶衰減）
    throttle = 255 if space else max(0, throttle - int(220*dt))
    brake    = 255 if lshift else max(0, brake - int(260*dt))

    # 速度模型（極簡展示用）
    a = GEAR_ACCEL[gear] * (throttle/255.0) - (0.9 + 0.002*speed_kmh) - (brake/255.0)*8.0
    speed_kmh = clamp(speed_kmh + a*12.0*dt, 0.0, 360.0)

    # 轉速模型：由時速與檔位推算，再受油門影響（展示用途）
    base = speed_kmh * (GEAR_RPM_K[gear] if gear>0 else 60.0)
    rpm_target = clamp(900 + base + (throttle/255.0)*800, 900, 8000)
    rpm += (rpm_target - rpm) * min(1.0, 6.0*dt)

    # 水溫/電壓簡單飄動（展示）
    coolant += (0.02 if throttle>0 else -0.015) * (60*dt)
    coolant = clamp(coolant, 70, 105)
    battery_v += (0.0005 if throttle==0 else -0.0007) * (60*dt)
    battery_v = clamp(battery_v, 11.8, 12.8)

    # 圈時計時
    lap_ms = pygame.time.get_ticks() - start_ms

    # ---------- 餵虛擬手把（可讓 Forza 接） ----------
    pad.left_joystick(x_value=steer_raw, y_value=0)
    pad.right_trigger(value=throttle)
    pad.left_trigger(value=brake)
    pad.update()

    # ---------- 繪圖 ----------
    screen.fill(BG)
    # 標題列
    draw_text("DriveSync Telemetry HUD", font_lg, 22, 16, ACCENT)

    # 轉速錶（中央）
    draw_tacho(W//2, 290, 210, rpm, gear)

    # 中下資訊（Lap/Delta/Mode）
    mm = lap_ms//60000; ss = (lap_ms//1000)%60; ms = (lap_ms%1000)//10
    draw_text(f"{mm}:{ss:02d}.{ms:02d}", font_lg, W//2-70, 520, FG)
    draw_text("Lap", font_sm, W//2-30, 555, SUB)
    draw_text(f"Mode: Keyboard", font_sm, W//2+120, 555, ACCENT)

    # 左：油門/煞車條
    draw_throttle_brake_bars(120, 260, 80, 240, throttle, brake)

    # 右上：A/B（示意：當前程式不使用，保留占位）
    pygame.draw.circle(screen, (70,72,80), (850, 230), 26, 2)
    pygame.draw.circle(screen, (70,72,80), (930, 230), 26, 2)
    draw_text("A", font_sm, 842, 265, SUB)
    draw_text("B", font_sm, 924, 265, SUB)

    # 左右下：水溫/時速/電量
    draw_stat_blocks(speed_kmh, coolant, battery_v)

    # 下方指示列
    draw_bottom_icons(220, H-36)

    # 右下角小資訊
    draw_text(f"{int(rpm):d} RPM", font_sm, W-170, 30, SUB)
    draw_text(f"{speed_kmh:5.1f} km/h", font_sm, W-190, 52, SUB)

    pygame.display.flip()