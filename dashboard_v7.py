import sys, math, signal, time
import pygame
import vgamepad as vg

# ----------------- 初始化 -----------------
pygame.init()
W, H = 1280, 720
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("DriveSync Dashboard")
clock = pygame.time.Clock()

# 速度發光邊框用的透明畫布
glow_surface = pygame.Surface((W, H), pygame.SRCALPHA)

# 字型
font_title = pygame.font.SysFont("Consolas", 46, bold=True)
font_big   = pygame.font.SysFont("Consolas", 90, bold=True)
font_mid   = pygame.font.SysFont("Consolas", 40, bold=True)
font_sm    = pygame.font.SysFont("Consolas", 26)
font_tiny  = pygame.font.SysFont("Consolas", 20, bold=False)

# 顏色主題
BG          = (4, 9, 16)
CARD_BG     = (9, 21, 32)
CARD_BG_SOFT= (12, 26, 40)
CARD_BORDER = (0, 200, 255)
TEXT_MAIN   = (235, 245, 255)
TEXT_SUB    = (130, 195, 235)
GREEN_BAR   = (0, 210, 80)
PINK        = (255, 80, 180)
YELLOW      = (245, 210, 40)
CYAN        = (0, 220, 255)
THR_COL     = (50, 220, 140)
BRK_COL     = (240, 90, 90)
BAR_BG      = (12, 35, 55)

pad = vg.VX360Gamepad()

def cleanup(*_):
    try:
        pad.reset(); pad.update()
    finally:
        pygame.quit(); sys.exit(0)

signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

# ----------------- 狀態變數 -----------------
steer_norm = 0.0   # -1..1
throttle   = 0     # 0..255
brake      = 0     # 0..255
gear       = 1
rpm        = 900
speed_kmh  = 0.0
temp_c     = 83.0

left_held  = False
right_held = False
gas_held   = False
brk_held   = False

start_time = time.time()
lap_start  = start_time
last_lap   = 0.0
best_lap   = 0.0
lap_count  = 0

def clamp(x, lo, hi):
    return max(lo, min(hi, x))

# ----------------- 小工具 -----------------
def draw_text(txt, font, x, y, color=TEXT_MAIN, center=False, align_right=False):
    surf = font.render(txt, True, color)
    rect = surf.get_rect()
    if center:
        rect.center = (x, y)
    elif align_right:
        rect.topright = (x, y)
    else:
        rect.topleft = (x, y)
    screen.blit(surf, rect)

def fill_round_rect(surface, rect, color, radius):
    pygame.draw.rect(surface, color, rect, border_radius=radius)

# 統一的卡片外框：圓角矩形 + 單一藍線
def draw_card(rect, bg=None, border_color=None, radius=None, border_width=2):
    x, y, w, h = rect
    if radius is None:
        radius = min(int(min(w, h) * 0.25), 40)
    if bg is None:
        bg = CARD_BG
    if border_color is None:
        border_color = CARD_BORDER

    pygame.draw.rect(screen, bg, rect, border_radius=radius)
    pygame.draw.rect(screen, border_color, rect, width=border_width, border_radius=radius)

def fmt_time(sec):
    m = int(sec // 60)
    s = int(sec % 60)
    ms = int((sec * 1000) % 1000)
    return f"{m:01d}:{s:02d}.{ms//10:02d}"

def draw_speed_glow(rect, progress):
    """
    rect: (x, y, w, h)
    progress: 0.0 ~ 1.0，代表繞完整個框的比例
    方向：逆時針
    """
    x, y, w, h = rect
    progress = clamp(progress, 0.0, 1.0)

    # 清空發光畫布
    glow_surface.fill((0, 0, 0, 0))

    perim = 2 * (w + h)
    L = perim * progress

    # 從左下角開始
    pts = []
    cx, cy = x, y + h
    pts.append((cx, cy))

    # 逆時針順序：
    # 左邊往上 → 上邊往右 → 右邊往下 → 下邊往左
    segments = [
        (h,  0, -1),  # 左邊：往上
        (w,  1,  0),  # 上邊：往右
        (h,  0,  1),  # 右邊：往下
        (w, -1,  0),  # 下邊：往左
    ]

    for seg_len, dx, dy in segments:
        if L <= 0:
            break
        draw_len = min(seg_len, L)
        ex = cx + dx * draw_len
        ey = cy + dy * draw_len
        pts.append((ex, ey))
        cx, cy = ex, ey
        L -= draw_len

    if len(pts) >= 2:
        inner_color = (CARD_BORDER[0], CARD_BORDER[1], CARD_BORDER[2], 210)
        outer_color = (CARD_BORDER[0], CARD_BORDER[1], CARD_BORDER[2], 80)

        # 內圈亮線
        pygame.draw.lines(
            glow_surface,
            inner_color,
            False,
            pts,
            4
        )
        # 外圈柔光
        pygame.draw.lines(
            glow_surface,
            outer_color,
            False,
            pts,
            10
        )

        screen.blit(glow_surface, (0, 0))

# ----------------- UI 區塊繪製 -----------------
def draw_top():
    # 左上標題
    draw_text("bullshit", font_title, 40, 24, CYAN)

    # 上方 steer pill bar
    bar_w, bar_h = 480, 54
    bar_rect = (W//2 - bar_w//2, 42, bar_w, bar_h)
    pill_radius = bar_h // 2

    draw_card(bar_rect, bg=(6, 24, 24), radius=pill_radius, border_width=2)

    x, y, w, h = bar_rect
    # 內部漸層條
    inner = (x+4, y+4, w-8, h-8)
    fill_round_rect(screen, inner, (5, 60, 40), pill_radius-4)

    # 中間黑線 + 中央 reference line
    pygame.draw.rect(screen, (0,0,0), (x+16, y+h//2-2, w-32, 4), border_radius=2)
    pygame.draw.line(screen, (0,0,0), (x+w//2, y+8), (x+w//2, y+h-8), 2)

    # STEER knob
    norm = clamp(steer_norm, -1.0, 1.0)
    cx = x + w//2 + int(norm * (w//2 - 60))
    knob = (cx-18, y+10, 36, h-20)
    fill_round_rect(screen, knob, GREEN_BAR, pill_radius-10)

    # 左邊文字：STEER + 數值
    draw_text("STEER", font_tiny, x+18, y+10, TEXT_SUB)
    draw_text(f"{norm:+0.3f}", font_sm, x+18, y+24, TEXT_MAIN)

def draw_left_panel():
    card_rect = (40, 130, 360, 380)
    draw_card(card_rect, bg=CARD_BG_SOFT)
    x, y, w, h = card_rect

    draw_text("PEDALS / TEMP", font_sm, x+80, y+30, TEXT_SUB)

    bar_w, bar_h = 70, 240
    base_y = y + 70
    x_thr = x + 70
    x_brk = x + 210

    # Throttle
    fill_round_rect(screen, (x_thr, base_y, bar_w, bar_h), BAR_BG, 18)
    ratio_t = throttle / 255.0
    fill_ht = int((bar_h-16) * ratio_t)
    if fill_ht > 0:
        rect = (x_thr+8, base_y + bar_h-8-fill_ht, bar_w-16, fill_ht)
        fill_round_rect(screen, rect, THR_COL, 12)
    draw_text("THR", font_tiny, x_thr+bar_w//2, base_y+bar_h+6, TEXT_SUB, center=True)
    draw_text(f"{int(ratio_t*100):3d}%", font_sm, x_thr+bar_w//2, base_y+bar_h+26, TEXT_MAIN, center=True)

    # Brake
    fill_round_rect(screen, (x_brk, base_y, bar_w, bar_h), BAR_BG, 18)
    ratio_b = brake / 255.0
    fill_hb = int((bar_h-16) * ratio_b)
    if fill_hb > 0:
        rect = (x_brk+8, base_y + bar_h-8-fill_hb, bar_w-16, fill_hb)
        fill_round_rect(screen, rect, BRK_COL, 12)
    draw_text("BRK", font_tiny, x_brk+bar_w//2, base_y+bar_h+6, TEXT_SUB, center=True)
    draw_text(f"{int(ratio_b*100):3d}%", font_sm, x_brk+bar_w//2, base_y+bar_h+26, TEXT_MAIN, center=True)

def draw_center_panel():
    card_rect = (460, 130, 360, 380)
    draw_card(card_rect, bg=CARD_BG_SOFT)
    x, y, w, h = card_rect

    # 速度 -> 發光邊框進度 (0 ~ 1)
    max_speed_for_glow = 240.0  # 想要 360 再滿圈就改 360.0
    progress = clamp(speed_kmh / max_speed_for_glow, 0.0, 1.0)
    draw_speed_glow(card_rect, progress)

    gear_char = "N" if gear == 0 else str(gear)
    draw_text(gear_char, font_big, x+w//2, y+120, CYAN, center=True)

    draw_text(f"{int(rpm):4d}", font_mid, x+w//2, y+210, TEXT_MAIN, center=True)
    draw_text("RPM", font_sm, x+w//2, y+245, TEXT_SUB, center=True)

    draw_text(f"{int(speed_kmh):3d}", font_mid, x+w//2, y+300, TEXT_MAIN, center=True)
    draw_text("km/h", font_sm, x+w//2, y+335, TEXT_SUB, center=True)

def draw_right_panel(current_lap, last_lap, best_lap):
    card_rect = (880, 130, 360, 380)
    draw_card(card_rect, bg=CARD_BG_SOFT)
    x, y, w, h = card_rect
    draw_text("LAP TIMES", font_sm, x+w//2, y+45, TEXT_SUB, center=True)
    row_h = 90
    rows = [
        ("CURRENT", CYAN,   current_lap),
        ("LAST",    YELLOW, last_lap),
        ("BEST",    PINK,   best_lap if best_lap > 0 else current_lap)
    ]

    for i, (label, color, tval) in enumerate(rows):
        ty = y + 90 + i * row_h
        draw_text(label, font_tiny, x + 26, ty, TEXT_SUB)
        draw_text(fmt_time(tval), font_mid, x + w - 26, ty - 6, color, align_right=True)

def draw_bottom_strip():
    titles = [
        ("STEER", f"{steer_norm:+0.2f}"),
        ("THR %", f"{int(throttle/255.0*100):3d}"),
        ("BRK %", f"{int(brake/255.0*100):3d}"),
        ("TEMP", f"{int(temp_c):2d}°C"),
        ("LAP",  str(lap_count)),
        ("MODE", "Keyboard"),
    ]
    card_w = 180
    card_h = 64
    gap    = 12
    start_x = 40
    y = H - card_h - 22

    for i, (title, val) in enumerate(titles):
        x = start_x + i * (card_w + gap)
        radius = card_h // 2
        draw_card((x, y, card_w, card_h), bg=(9, 21, 32), radius=radius)
        center_x = x + card_w / 2

        draw_text(
            title,
            font_tiny,
            center_x,
            y + card_h * 0.30,
            TEXT_SUB,
            center=True
        )
        draw_text(
            val,
            font_sm,
            center_x,
            y + card_h * 0.70,
            TEXT_MAIN,
            center=True
        )

# ----------------- 主迴圈 -----------------
while True:
    dt = clock.tick(60) / 1000.0
    now = time.time()
    current_lap = now - lap_start

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
                brk_held = True
            if e.key == pygame.K_RETURN:   # 完成一圈 + X 鍵
                last_lap = current_lap
                if best_lap == 0 or last_lap < best_lap:
                    best_lap = last_lap
                lap_count += 1
                lap_start = now
                pad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_X)
            if e.key == pygame.K_z:        # 升檔 + A 鍵
                gear = clamp(gear + 1, 0, 8)
                rpm = max(800, rpm - 2000)
                pad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
            if e.key == pygame.K_x:        # 降檔 + B 鍵
                gear = clamp(gear - 1, 0, 8)
                rpm = max(800, rpm + 2000)
                pad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_B)
        if e.type == pygame.KEYUP:
            if e.key == pygame.K_LEFT:
                left_held = False
            if e.key == pygame.K_RIGHT:
                right_held = False
            if e.key == pygame.K_SPACE:
                gas_held = False
            if e.key == pygame.K_LSHIFT:
                brk_held = False
            if e.key == pygame.K_RETURN:
                pad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_X)
            if e.key == pygame.K_z:
                pad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
            if e.key == pygame.K_x:
                pad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_B)

    # Steering
    steer_speed = 2.0
    if left_held and not right_held:
        steer_norm -= steer_speed * dt
    elif right_held and not left_held:
        steer_norm += steer_speed * dt
    else:
        steer_norm *= (1.0 - 3.0 * dt)
    steer_norm = clamp(steer_norm, -1.0, 1.0)
    steer_raw = int(steer_norm * 32767)

    # 油門 / 煞車
    if gas_held:
        throttle = clamp(throttle + int(420 * dt), 0, 255)
    else:
        throttle = clamp(throttle - int(360 * dt), 0, 255)
    if brk_held:
        brake = clamp(brake + int(460 * dt), 0, 255)
    else:
        brake = clamp(brake - int(360 * dt), 0, 255)

    # 簡單物理模型
    accel = (throttle/255.0) * (3.0 + gear) - (brake/255.0)*8.0 - 0.02*speed_kmh
    speed_kmh = clamp(speed_kmh + accel * 14.0 * dt, 0.0, 360.0)  # 上限 360 km/h

    rpm_target = 900 + speed_kmh*(40 + gear*5) + (throttle/255.0)*800
    rpm += (rpm_target - rpm) * min(1.0, 5.0*dt)
    rpm = clamp(rpm, 800, 10000)

    temp_c += (0.02 if throttle>0 else -0.015) * (60*dt)
    temp_c = clamp(temp_c, 70, 105)

    # 餵虛擬手把（軸）
    pad.left_joystick(x_value=steer_raw, y_value=0)
    pad.right_trigger(value=int(throttle))
    pad.left_trigger(value=int(brake))
    pad.update()

    # 畫面
    screen.fill(BG)
    draw_top()
    draw_left_panel()
    draw_center_panel()
    draw_right_panel(current_lap, last_lap, best_lap)
    draw_bottom_strip()
    pygame.display.flip()
