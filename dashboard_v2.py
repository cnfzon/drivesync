import sys, time, signal, math
import pygame
import vgamepad as vg

pad = vg.VX360Gamepad()
pygame.init()
W, H = 950, 500
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("DriveSync Telemetry HUD")
font_big = pygame.font.SysFont("consolas", 36, bold=True)
font_med = pygame.font.SysFont("consolas", 24)
font_small = pygame.font.SysFont("consolas", 18)
clock = pygame.time.Clock()

BG = (14,17,23)
TEXT = (200,210,230)
BAR = (45,50,60)
ACCENT = (90,180,255)
ACTIVE = (255,80,80)

steer = 0
thr = 0
brk = 0
btn_a = False
btn_b = False

def cleanup(*_):
    pad.reset(); pad.update()
    pygame.quit(); sys.exit(0)

signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

def draw_text(txt, x, y, f=font_med, color=TEXT, center=False):
    surf = f.render(txt, True, color)
    rect = surf.get_rect()
    if center: rect.center = (x, y)
    else: rect.topleft = (x, y)
    screen.blit(surf, rect)

def draw_gauge(cx, cy, r, angle):
    pygame.draw.circle(screen, BAR, (cx, cy), r, width=12)
    # 指針
    ang = math.radians(angle/1000 * 120)  # 最大轉 ±120度
    px = cx + int(r*0.8*math.sin(ang))
    py = cy - int(r*0.8*math.cos(ang))
    pygame.draw.line(screen, ACCENT, (cx, cy), (px, py), 6)
    pygame.draw.circle(screen, (230,230,230), (cx, cy), 8)
    draw_text(f"{angle:+4d}", cx, cy+r+25, font_small, color=TEXT, center=True)
    draw_text("Steering", cx, cy+r+45, font_small, center=True)

def draw_bar(x, y, w, h, val, label, color):
    pygame.draw.rect(screen, BAR, (x, y, w, h), border_radius=8)
    fill_h = int((h-6) * (val/255))
    pygame.draw.rect(screen, color, (x+3, y+h-3-fill_h, w-6, fill_h), border_radius=8)
    draw_text(f"{label}: {int(val/2.55):3d}%", x, y+h+10, font_small)

def draw_button(x, y, label, pressed):
    pygame.draw.circle(screen, BAR, (x,y), 25)
    if pressed:
        pygame.draw.circle(screen, ACTIVE, (x,y), 23)
    else:
        pygame.draw.circle(screen, (120,120,130), (x,y), 23, 2)
    draw_text(label, x, y+38, font_small, center=True)

while True:
    for e in pygame.event.get():
        if e.type == pygame.QUIT: cleanup()
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE: cleanup()

    keys = pygame.key.get_pressed()

    if keys[pygame.K_LEFT]: steer = max(-32768, steer - 3000)
    elif keys[pygame.K_RIGHT]: steer = min(32767, steer + 3000)
    else: steer = int(steer * 0.85)

    thr = 255 if keys[pygame.K_SPACE] else max(0, thr - 15)
    brk = 255 if keys[pygame.K_LSHIFT] else max(0, brk - 15)
    btn_a = keys[pygame.K_z]
    btn_b = keys[pygame.K_x]

    # 虛擬手把
    pad.left_joystick(x_value=steer, y_value=0)
    pad.right_trigger(value=thr)
    pad.left_trigger(value=brk)
    if btn_a: pad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
    else: pad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
    if btn_b: pad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_B)
    else: pad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_B)
    pad.update()

    screen.fill(BG)
    draw_text("DriveSync Telemetry HUD", 20, 15, font_big, color=ACCENT)

    # 儀表：方向盤
    draw_gauge(W//2, 220, 120, int(steer/32.767))

    # 踏板
    draw_bar(130, 200, 60, 200, thr, "Throttle", (100,220,150))
    draw_bar(260, 200, 60, 200, brk, "  Brake", (255,100,100))

    # 按鍵狀態
    draw_button(720, 210, "A", btn_a)
    draw_button(800, 210, "B", btn_b)

    # 資訊欄
    draw_text(f"STEER RAW: {steer:+6d}", 600, 360, font_small)
    draw_text(f"FPS: {int(clock.get_fps())}", 600, 380, font_small)
    draw_text(f"Mode: Keyboard", 600, 400, font_small, color=(150,200,255))

    pygame.display.flip()
    clock.tick(60)
