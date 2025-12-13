import sys, math, signal
import pygame
import vgamepad as vg

# ----------------- 初始化 -----------------
pygame.init()
W, H = 1200, 650
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("DriveSync Steering Dashboard")
clock = pygame.time.Clock()

# 字型
font_title = pygame.font.SysFont("Segoe UI", 46, bold=True)
font_big   = pygame.font.SysFont("Segoe UI", 52, bold=True)
font_mid   = pygame.font.SysFont("Segoe UI", 30, bold=True)
font_sm    = pygame.font.SysFont("Segoe UI", 22)
font_tiny  = pygame.font.SysFont("Segoe UI", 18)

# 色彩主題
BG       = (6, 10, 20)
PANEL_BG = (16, 24, 40)
FG       = (230, 235, 245)
SUB      = (155, 165, 185)
FRAME    = (60, 70, 90)
ACCENT   = (90, 190, 255)
BRAKE_C  = (244, 105, 105)
THR_C    = (110, 215, 150)
GLOW     = (40, 120, 220)

pad = vg.VX360Gamepad()

def cleanup(*_):
    try:
        pad.reset(); pad.update()
    finally:
        pygame.quit(); sys.exit(0)

signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

# ----------------- 狀態變數 -----------------
steer_norm = 0.0   # -1..1，用來表示方向盤位置
throttle   = 0     # 0..255
brake      = 0     # 0..255
gear       = 1
rpm        = 1000
speed_kmh  = 0.0
temp_c     = 85.0

left_held  = False
right_held = False
gas_held   = False
brake_held = False

def clamp(x, lo, hi): return max(lo, min(hi, x))

# ----------------- 小工具 -----------------
def draw_text(txt, font, x, y, color=FG, center=False):
    surf = font.render(txt, True, color)
    rect = surf.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    screen.blit(surf, rect)

def draw_panel(rect, radius=24):
    x,y,w,h = rect
    # 外框淡淡的陰影
    pygame.draw.rect(screen, (0,0,0), (x+3,y+6,w,h), border_radius=radius)
    pygame.draw.rect(screen, PANEL_BG, rect, border_radius=radius)
    pygame.draw.rect(screen, FRAME,    rect, 2, border_radius=radius)

# ----------------- 左右直條（煞車 / 油門） -----------------
def draw_vertical_bar(x, y, w, h, ratio, color, label):
    # 外框
    pygame.draw.rect(screen, FRAME, (x, y, w, h), width=2, border_radius=18)
    # 背景
    pygame.draw.rect(screen, (20, 30, 45), (x+2, y+2, w-4, h-4), border_radius=16)
    # 內部填色
    fill_h = int((h - 14) * ratio)
    if fill_h > 0:
        rect = pygame.Rect(x+6, y + h - 7 - fill_h, w-12, fill_h)
        pygame.draw.rect(screen, color, rect, border_radius=12)
    draw_text(label, font_mid, x + w//2, y - 30, SUB, center=True)

# ----------------- 中央橢圓錶盤 -----------------
def draw_center_ellipse(cx, cy, rx, ry, rpm, gear, throttle, steer_norm):
    # --- 外圈光暈 + 橢圓 ---
    glow_ratio = clamp(throttle/255.0, 0.0, 1.0)
    glow_r = int(6 + 10 * glow_ratio)
    if glow_ratio > 0.02:
        glow_surf = pygame.Surface((rx*2+40, ry*2+40), pygame.SRCALPHA)
        pygame.draw.ellipse(
            glow_surf,
            (*GLOW, int(80*glow_ratio)),
            (0, 0, rx*2+40, ry*2+40),
            width=glow_r
        )
        screen.blit(glow_surf, (cx-rx-20, cy-ry-20))

    rect = pygame.Rect(cx-rx, cy-ry, rx*2, ry*2)
    border_col = (180, 190, 205)
    pygame.draw.ellipse(screen, PANEL_BG, rect)
    pygame.draw.ellipse(screen, border_col, rect, width=3)

    # --- 上方刻度（純視覺） ---
    tick_angles_deg = [-80, -40, 0, 40, 80, 120]
    for ang_deg in tick_angles_deg:
        a = math.radians(ang_deg)
        x1 = cx + int(rx * math.cos(a))
        y1 = cy + int(ry * math.sin(a))
        x2 = cx + int((rx - 40) * math.cos(a))
        y2 = cy + int((ry - 40) * math.sin(a))
        pygame.draw.line(screen, border_col, (x1, y1), (x2, y2), 8)

    # --- 檔位與 RPM ---
    draw_text("Gear", font_sm, cx, cy - 60, SUB, center=True)
    draw_text(str(gear if gear > 0 else 0), font_big, cx, cy - 20, FG, center=True)

    draw_text("RPM", font_sm, cx, cy + 15, SUB, center=True)
    draw_text(f"{int(rpm):d}", font_mid, cx, cy + 45, FG, center=True)

    # --- 橫向方向滑桿 ---
    bar_w = rx * 1.35
    bar_h = 30
    bar_y = cy + ry * 0.5
    bar_x = cx - bar_w / 2
    bar_rect = pygame.Rect(int(bar_x), int(bar_y), int(bar_w), int(bar_h))

    pygame.draw.rect(screen, FRAME, bar_rect, border_radius=16)
    inner_rect = bar_rect.inflate(-4, -4)
    pygame.draw.rect(screen, (18, 26, 44), inner_rect, border_radius=14)

    draw_text("Steering", font_tiny, cx, bar_y - 8, SUB, center=True)

    norm = clamp(steer_norm, -1.0, 1.0)
    knob_w = bar_w * 0.18
    knob_center_x = cx + norm * (bar_w/2 - knob_w/2 - 6)
    knob_x = int(knob_center_x - knob_w/2)
    knob_rect = pygame.Rect(knob_x, inner_rect.y+3, int(knob_w), inner_rect.height-6)

    pygame.draw.rect(screen, ACCENT, knob_rect, border_radius=12)
    # 中間畫一條白線有方向感
    pygame.draw.line(
        screen, (245, 250, 255),
        (knob_rect.centerx, knob_rect.top+5),
        (knob_rect.centerx, knob_rect.bottom-5),
        2
    )

# ----------------- 速度 / 溫度 文字區 -----------------
def draw_bottom_readouts(speed, temp):
    # 左：溫度
    draw_text("Coolant", font_sm, 110, H - 90, SUB, center=True)
    draw_text(f"{int(temp)} °C", font_mid, 110, H - 58, FG, center=True)
    # 右：時速
    draw_text("Speed", font_sm, W - 150, H - 90, SUB, center=True)
    draw_text(f"{int(speed)} km/h", font_mid, W - 150, H - 58, FG, center=True)

# ----------------- 主迴圈 -----------------
while True:
    dt = clock.tick(60) / 1000.0

    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            cleanup()
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                cleanup()
            if e.key == pygame.K_LEFT:
                left_held = True
            if e.key == pygame.K_RIGHT:
                right_held = True
            if e.key == pygame.K_SPACE:
                gas_held = True
            if e.key == pygame.K_LSHIFT:
                brake_held = True
            if e.key == pygame.K_z:
                gear = clamp(gear + 1, 0, 7)
            if e.key == pygame.K_x:
                gear = clamp(gear - 1, 0, 7)
        if e.type == pygame.KEYUP:
            if e.key == pygame.K_LEFT:
                left_held = False
            if e.key == pygame.K_RIGHT:
                right_held = False
            if e.key == pygame.K_SPACE:
                gas_held = False
            if e.key == pygame.K_LSHIFT:
                brake_held = False

    # ---- 方向盤連續滑動 + 回中 ----
    steer_speed = 2.2  # 轉向速度
    if left_held and not right_held:
        steer_norm -= steer_speed * dt
    elif right_held and not left_held:
        steer_norm += steer_speed * dt
    else:
        # 自動回正（阻尼）
        steer_norm *= (1.0 - 3.0 * dt)
    steer_norm = clamp(steer_norm, -1.0, 1.0)
    steer_raw = int(steer_norm * 32767)

    # ---- 油門 / 煞車 ----
    if gas_held:
        throttle = clamp(throttle + int(420 * dt), 0, 255)
    else:
        throttle = clamp(throttle - int(360 * dt), 0, 255)

    if brake_held:
        brake = clamp(brake + int(460 * dt), 0, 255)
    else:
        brake = clamp(brake - int(360 * dt), 0, 255)

    # ---- 簡易物理模型 ----
    accel = (throttle/255.0) * (3.0 + gear) - (brake/255.0)*8.0 - 0.02*speed_kmh
    speed_kmh = clamp(speed_kmh + accel * 15.0 * dt, 0.0, 260.0)

    rpm_target = 1000 + speed_kmh*(40 + gear*5) + (throttle/255.0)*1000
    rpm += (rpm_target - rpm) * min(1.0, 5.0*dt)
    rpm = clamp(rpm, 800, 8000)

    temp_c += (0.02 if throttle>0 else -0.015) * (60*dt)
    temp_c = clamp(temp_c, 70, 105)

    # ---- 餵虛擬手把 ----
    pad.left_joystick(x_value=steer_raw, y_value=0)
    pad.right_trigger(value=int(throttle))
    pad.left_trigger(value=int(brake))
    pad.update()

    # ---- 繪圖 ----
    screen.fill(BG)

    # 外框 + 中央 Panel
    pygame.draw.rect(screen, FRAME, (20, 20, W-40, H-40), 2, border_radius=28)
    draw_text("DriveSync Telemetry HUD", font_title, 40, 26, ACCENT)

    draw_panel((80, 110, W-160, 370))   # 中央大面板

    # 左右油門 / 煞車區
    bar_h = 250
    bar_w = 80
    bar_y = 170
    draw_vertical_bar(80+40, bar_y, bar_w, bar_h, brake/255.0, BRAKE_C, "Brake")
    draw_vertical_bar(W-80-40-bar_w, bar_y, bar_w, bar_h, throttle/255.0, THR_C, "Throttle")

    # 中央橢圓儀表
    center_cx, center_cy = W//2, 300
    draw_center_ellipse(center_cx, center_cy, 340, 210, rpm, gear, throttle, steer_norm)

    # 底部資訊列
    draw_bottom_readouts(speed_kmh, temp_c)
    draw_text(f"FPS {int(clock.get_fps())}",
              font_tiny, 32, H-32, SUB)
    draw_text("←/→ Steering   Space Throttle   LShift Brake   Z/X Gear",
              font_tiny, 230, H-32, SUB)

    pygame.display.flip()
