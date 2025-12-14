import sys, math, signal, time, struct
import pygame
import vgamepad as vg

SERIAL_PORT = "COM8"
BAUD_RATE   = 115200

try:
    import serial
except ImportError:
    serial = None

USE_SERIAL = False
ser = None
rx_buf = bytearray()

if serial is not None:
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.01)
        USE_SERIAL = True
        print(f"[UART] Using {SERIAL_PORT} @ {BAUD_RATE}")
    except Exception as e:
        print("[UART] Disabled:", e)
        ser = None
        USE_SERIAL = False
else:
    print("[UART] pyserial not installed, run: pip install pyserial")
    ser = None
    USE_SERIAL = False

# vGamepad 初始化
pygame.init()
W, H = 1280, 720
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("DriveSync Dashboard")
clock = pygame.time.Clock()

glow_surface = pygame.Surface((W, H), pygame.SRCALPHA)

font_title = pygame.font.SysFont("Consolas", 46, bold=True)
font_big   = pygame.font.SysFont("Consolas", 90, bold=True)
font_mid   = pygame.font.SysFont("Consolas", 40, bold=True)
font_sm    = pygame.font.SysFont("Consolas", 26)
font_tiny  = pygame.font.SysFont("Consolas", 20, bold=False)

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
        pad.reset()
        pad.update()
        if ser is not None:
            ser.close()
    finally:
        pygame.quit()
        sys.exit(0)

signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

# --------- 狀態變數 ---------
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

# UART 封包
# 0xAB, gear(1B), rpm(2B), speed(2B), thr(1B), brk(1B), steer*10(2B)
# Little-endian: <B B H H B B h  (總長 10 bytes)
"""
Byte0 : 0xAB       (Header)
Byte1 : Gearbox    (1B)
Byte2 : RPM Low    (RPM = uint16)
Byte3 : RPM High
Byte4 : Speed Low  (Speed = uint16)
Byte5 : Speed High
Byte6 : Throttle   (0 – 255)
Byte7 : Brake      (0 – 255)
Byte8 : Steering Low   (int16 = real_angle * 10)
Byte9 : Steering High
"""

FRAME_LEN = 16

def process_serial():
    """讀取 UART 並解碼到全域變數（AB . gear . rpm . speed . thr . brk . steer）。"""
    global rx_buf, gear, rpm, speed_kmh, throttle, brake, steer_norm

    if not USE_SERIAL or ser is None:
        return

    data = ser.read(64)
    if not data:
        return

    rx_buf.extend(data)

    while len(rx_buf) >= FRAME_LEN:
        # 尋找封包開頭 0xAB
        if rx_buf[0] != 0xAB:
            rx_buf.pop(0)
            continue

        if len(rx_buf) < FRAME_LEN:
            # 不夠一個完整封包，等下次再解
            break

        frame = rx_buf[:FRAME_LEN]
        rx_buf = rx_buf[FRAME_LEN:]

        # 確認 '.' 分隔符的位置都正確（防止不同步）
        if not (
            frame[1]  == 0x2E and
            frame[3]  == 0x2E and
            frame[6]  == 0x2E and
            frame[9]  == 0x2E and
            frame[11] == 0x2E and
            frame[13] == 0x2E
        ):
            # 封包壞掉，丟掉這個 header 繼續找下一個
            print("分隔符錯誤，丟棄一個 byte 重新同步")
            continue

        # ---- 依照實際排列解碼（16 bits 一律 big-endian：Hi 在前）----
        gear_val   = frame[2]

        rpm_val    = (frame[4]  << 8) | frame[5]      # 0x1F40 = 8000
        speed_val  = (frame[7]  << 8) | frame[8]
        thr_val    = frame[10]
        brk_val    = frame[12]
        steer_raw  = (frame[14] << 8) | frame[15]     # int16 (*10)

        # int16 符號處理
        if steer_raw >= 0x8000:
            steer_raw -= 0x10000

        # ---- 更新全域變數 ----
        gear      = int(gear_val)
        rpm       = int(rpm_val)
        speed_kmh = float(speed_val)
        throttle  = int(thr_val)
        brake     = int(brk_val)

        steer_angle = steer_raw / 10.0
        steer_norm  = clamp(steer_angle / 180.0, -1.0, 1.0)

        # Debug：先確認是否有正確解析（你現在最關心的 gear=5, rpm=8000）
        print(
            f"解析成功 → gear={gear}, rpm={rpm}, "
            f"speed={speed_kmh}, thr={throttle}, brk={brake}, steer={steer_angle}"
        )

# UI
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
    x, y, w, h = rect
    progress = clamp(progress, 0.0, 1.0)

    glow_surface.fill((0, 0, 0, 0))

    perim = 2 * (w + h)
    L = perim * progress

    pts = []
    cx, cy = x, y + h
    pts.append((cx, cy))

    segments = [
        (h,  0, -1),
        (w,  1,  0),
        (h,  0,  1),
        (w, -1,  0),
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

        pygame.draw.lines(glow_surface, inner_color, False, pts, 4)
        pygame.draw.lines(glow_surface, outer_color, False, pts, 10)

        screen.blit(glow_surface, (0, 0))

# UI
def draw_top():
    draw_text("bullshit", font_title, 40, 24, CYAN)

    bar_w, bar_h = 480, 54
    bar_rect = (W//2 - bar_w//2, 42, bar_w, bar_h)
    pill_radius = bar_h // 2

    draw_card(bar_rect, bg=(6, 24, 24), radius=pill_radius, border_width=2)

    x, y, w, h = bar_rect
    inner = (x+4, y+4, w-8, h-8)
    fill_round_rect(screen, inner, (5, 60, 40), pill_radius-4)

    pygame.draw.rect(screen, (0,0,0), (x+16, y+h//2-2, w-32, 4), border_radius=2)
    pygame.draw.line(screen, (0,0,0), (x+w//2, y+8), (x+w//2, y+h-8), 2)

    norm = clamp(steer_norm, -1.0, 1.0)
    cx = x + w//2 + int(norm * (w//2 - 60))
    knob = (cx-18, y+10, 36, h-20)
    fill_round_rect(screen, knob, GREEN_BAR, pill_radius-10)

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
    max_speed_for_glow = 240.0
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
    mode_label = "UART" if USE_SERIAL else "Keyboard"
    titles = [
        ("STEER", f"{steer_norm:+0.2f}"),
        ("THR %", f"{int(throttle/255.0*100):3d}"),
        ("BRK %", f"{int(brake/255.0*100):3d}"),
        ("TEMP", f"{int(temp_c):2d}°C"),
        ("LAP",  str(lap_count)),
        ("MODE", mode_label),
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

        draw_text(title, font_tiny, center_x, y + card_h * 0.30, TEXT_SUB, center=True)
        draw_text(val,   font_sm,   center_x, y + card_h * 0.70, TEXT_MAIN, center=True)

# --------- 主迴圈 ---------
while True:
    dt = clock.tick(60) / 1000.0
    now = time.time()
    current_lap = now - lap_start

    # 事件處理（鍵盤：Esc / Lap 功能還是保留）
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            cleanup()
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                cleanup()
            if not USE_SERIAL:  # 只有在 Keyboard 模式才用方向＋油門
                if e.key == pygame.K_LEFT:
                    left_held = True
                if e.key == pygame.K_RIGHT:
                    right_held = True
                if e.key == pygame.K_SPACE:
                    gas_held = True
                if e.key == pygame.K_LSHIFT:
                    brk_held = True
            if e.key == pygame.K_RETURN:
                last_lap = current_lap
                if best_lap == 0 or last_lap < best_lap:
                    best_lap = last_lap
                lap_count += 1
                lap_start = now
                pad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_X)
            if e.key == pygame.K_z and not USE_SERIAL:
                gear = clamp(gear + 1, 0, 8)
                rpm = max(800, rpm - 2000)
                pad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
            if e.key == pygame.K_x and not USE_SERIAL:
                gear = clamp(gear - 1, 0, 8)
                rpm = max(800, rpm + 2000)
                pad.press_button(button=vg.XUSB_BUTTON_XUSB_GAMEPAD_B)
        if e.type == pygame.KEYUP:
            if not USE_SERIAL:
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
            if e.key == pygame.K_z and not USE_SERIAL:
                pad.release_button(button=vg.XUSB_BUTTON_XUSB_GAMEPAD_A)
            if e.key == pygame.K_x and not USE_SERIAL:
                pad.release_button(button=vg.XUSB_BUTTON_XUSB_GAMEPAD_B)

    # UART 更新（若有開啟）
    process_serial()

    # ---- Keyboard 模式：自己模擬物理 ----
    if not USE_SERIAL:
        # Steering
        steer_speed = 2.0
        if left_held and not right_held:
            steer_norm -= steer_speed * dt
        elif right_held and not left_held:
            steer_norm += steer_speed * dt
        else:
            steer_norm *= (1.0 - 3.0 * dt)
        steer_norm = clamp(steer_norm, -1.0, 1.0)

        # 油門 / 煞車
        if gas_held:
            throttle = clamp(throttle + int(420 * dt), 0, 255)
        else:
            throttle = clamp(throttle - int(360 * dt), 0, 255)
        if brk_held:
            brake = clamp(brake + int(460 * dt), 0, 255)
        else:
            brake = clamp(brake - int(360 * dt), 0, 255)

        # 物理模型
        accel = (throttle/255.0) * (3.0 + gear) - (brake/255.0)*8.0 - 0.02*speed_kmh
        speed_kmh = clamp(speed_kmh + accel * 14.0 * dt, 0.0, 360.0)

        rpm_target = 900 + speed_kmh*(40 + gear*5) + (throttle/255.0)*800
        rpm += (rpm_target - rpm) * min(1.0, 5.0*dt)
        rpm = clamp(rpm, 800, 10000)

    # ---- 共用：溫度模擬 + 搖桿輸出 ----
    temp_c += (0.02 if throttle>0 else -0.015) * (60*dt)
    temp_c = clamp(temp_c, 70, 105)

    steer_raw = int(clamp(steer_norm, -1.0, 1.0) * 32767)

    pad.left_joystick(x_value=steer_raw, y_value=0)
    pad.right_trigger(value=int(throttle))
    pad.left_trigger(value=int(brake))
    pad.update()

    screen.fill(BG)
    draw_top()
    draw_left_panel()
    draw_center_panel()
    draw_right_panel(current_lap, last_lap, best_lap)
    draw_bottom_strip()
    pygame.display.flip()