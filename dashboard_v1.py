import time, sys, signal
import vgamepad as vg
import pygame

gamepad = vg.VX360Gamepad()
print("🎮 Virtual gamepad online. ←/→ 控方向，Space=油門，Esc 離開")

pygame.init()
screen = pygame.display.set_mode((400, 120))  # 小視窗避免搶焦點
pygame.display.set_caption("Gamepad Daemon (Keys)")
clock = pygame.time.Clock()

def cleanup(*_):
    try:
        gamepad.reset(); gamepad.update()
    finally:
        pygame.quit(); sys.exit(0)

signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

steer = 0   # -32768..32767
thr   = 0   # 0..255

while True:
    for e in pygame.event.get():
        if e.type == pygame.QUIT: cleanup()
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE: cleanup()

    keys = pygame.key.get_pressed()
    # 方向：左右鍵
    if keys[pygame.K_LEFT]:  steer = max(-32768, steer - 3000)
    elif keys[pygame.K_RIGHT]: steer = min(32767, steer + 3000)
    else: steer = int(steer * 0.85)  # 回中阻尼

    # 油門：Space
    thr = 255 if keys[pygame.K_SPACE] else max(0, thr - 10)

    # 虛擬手把
    gamepad.left_joystick(x_value=steer, y_value=0)
    gamepad.right_trigger(value=thr)
    gamepad.update()

    screen.fill((20,20,24))
    clock.tick(60)
