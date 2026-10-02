#!/usr/bin/env python3
"""Taaffeite Trace — neon light-cycle arcade for ElbowOS. Python 3 + pygame.

Steer a lilac blade. Trails linger, then fade. Snatch amber sparks.
Rivals in saffron and aqua cut the same grid. Crash, flash, respawn.

  python3 taaffeite_trace.py --play
  python3 taaffeite_trace.py --record
"""
import math
import os
import random
import subprocess
import sys

RECORD = "--record" in sys.argv or os.environ.get("ELBOWOS_RECORD") == "1"
PLAY = "--play" in sys.argv
if not PLAY:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

W, H, FPS, SECS = 1080, 1920, 30, 15
OUT = os.environ.get("ELBOWOS_MP4", "/home/workdir/artifacts/TAAFFEITE_TRACE_ElbowOS.mp4")
COLS, ROWS, CELL = 16, 26, 56
OX = (W - COLS * CELL) // 2
OY = 300
DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))
PLUM = (16, 6, 28)
LILAC = (231, 166, 255)
SAFFRON = (255, 176, 64)
AQUA = (64, 255, 214)
AMBER = (255, 214, 92)
INK = (8, 2, 16)
CREAM = (255, 244, 230)

class Bike:
    def __init__(self, bid, x, y, dx, dy, color):
        self.bid, self.color = bid, color
        self.x, self.y, self.dx, self.dy = x, y, dx, dy
        self.alive, self.flash = True, 0
        self.trail = []  # (x, y, age)

    def head(self):
        return self.x, self.y

class Game:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        self.font = pygame.font.SysFont("dejavusans", 64, bold=True)
        self.mid = pygame.font.SysFont("dejavusans", 40, bold=True)
        self.small = pygame.font.SysFont("dejavusans", 32, bold=True)
        flags = 0 if PLAY else pygame.HIDDEN
        try:
            self.screen = pygame.display.set_mode((W, H), flags)
        except pygame.error:
            self.screen = pygame.Surface((W, H))
        pygame.display.set_caption("Taaffeite Trace")
        self.rng = random.Random(7)
        self.reset()

    def reset(self):
        self.score = 0
        self.tick = 0
        self.sparks = []
        self.bikes = [
            Bike(0, 8, 20, 0, -1, LILAC),
            Bike(1, 3, 6, 1, 0, SAFFRON),
            Bike(2, 12, 8, -1, 0, AQUA),
        ]
        for b in self.bikes:
            b.trail.append((b.x, b.y, 0))
        self.seed_sparks(5)

    def occupied(self):
        occ = {}
        for b in self.bikes:
            for x, y, age in b.trail:
                if age < 42:
                    occ[(x, y)] = b.bid
        return occ

    def seed_sparks(self, n):
        occ = self.occupied()
        for _ in range(40):
            if len(self.sparks) >= n:
                return
            p = (self.rng.randrange(COLS), self.rng.randrange(ROWS))
            if p not in occ and p not in self.sparks:
                self.sparks.append(p)

    def open_dirs(self, bike, occ):
        opts = []
        for dx, dy in DIRS:
            if (dx, dy) == (-bike.dx, -bike.dy):
                continue
            nx, ny = bike.x + dx, bike.y + dy
            if 0 <= nx < COLS and 0 <= ny < ROWS and (nx, ny) not in occ:
                opts.append((dx, dy))
        return opts

    def choose(self, bike, occ, auto):
        opts = self.open_dirs(bike, occ)
        if not opts:
            return None
        if not auto and bike.bid != 0:
            auto = True
        if bike.bid == 0 and not auto:
            return bike.dx, bike.dy
        best, best_s = opts[0], -10**9
        for dx, dy in opts:
            nx, ny = bike.x + dx, bike.y + dy
            score = 0
            if self.sparks:
                sx, sy = min(self.sparks, key=lambda p: abs(p[0] - nx) + abs(p[1] - ny))
                score -= (abs(sx - nx) + abs(sy - ny)) * 3
            for k in range(1, 5):
                tx, ty = nx + dx * k, ny + dy * k
                if not (0 <= tx < COLS and 0 <= ty < ROWS) or (tx, ty) in occ:
                    score -= 8
                    break
                score += 2
            score += self.rng.randint(0, 2)
            if score > best_s:
                best, best_s = (dx, dy), score
        return best

    def step(self, auto=False):
        self.tick += 1
        for b in self.bikes:
            b.trail = [(x, y, a + 1) for x, y, a in b.trail if a < 46]
            if b.flash:
                b.flash -= 1
        if self.tick % 3:
            return
        occ = self.occupied()
        moves = []
        for b in self.bikes:
            if not b.alive:
                continue
            pick = self.choose(b, occ, auto or b.bid != 0)
            if pick is None:
                moves.append((b, None))
            else:
                b.dx, b.dy = pick
                moves.append((b, (b.x + b.dx, b.y + b.dy)))
        claimed = {}
        for b, nxt in moves:
            if nxt is None or nxt in occ or nxt in claimed:
                self.crash(b)
            else:
                claimed[nxt] = b.bid
                b.x, b.y = nxt
                b.trail.append((b.x, b.y, 0))
                if (b.x, b.y) in self.sparks:
                    self.sparks.remove((b.x, b.y))
                    self.score += 25 if b.bid == 0 else 5
                    self.seed_sparks(4)
                elif b.bid == 0:
                    self.score += 1
        if len(self.sparks) < 3:
            self.seed_sparks(4)

    def crash(self, bike):
        bike.alive = False
        bike.flash = 10
        bike.trail.clear()
        self.score = max(0, self.score - (4 if bike.bid == 0 else 0))
        occ = self.occupied()
        for _ in range(30):
            x, y = self.rng.randrange(1, COLS - 1), self.rng.randrange(1, ROWS - 1)
            if (x, y) not in occ:
                dx, dy = self.rng.choice(DIRS)
                bike.x, bike.y, bike.dx, bike.dy = x, y, dx, dy
                bike.alive = True
                bike.trail = [(x, y, 0)]
                return

    def turn(self, dx, dy):
        me = self.bikes[0]
        if (dx, dy) != (-me.dx, -me.dy):
            me.dx, me.dy = dx, dy

    def draw(self, surf):
        surf.fill(INK)
        for i in range(18):
            c = 18 + i * 2
            pygame.draw.rect(surf, (c, 4 + i, 28 + i), (0, i * 110, W, 110))
        arena = pygame.Rect(OX - 16, OY - 16, COLS * CELL + 32, ROWS * CELL + 32)
        pygame.draw.rect(surf, (32, 10, 48), arena, border_radius=28)
        pygame.draw.rect(surf, LILAC, arena, 4, border_radius=28)
        for gx in range(COLS + 1):
            pygame.draw.line(surf, (48, 22, 64), (OX + gx * CELL, OY), (OX + gx * CELL, OY + ROWS * CELL), 1)
        for gy in range(ROWS + 1):
            pygame.draw.line(surf, (48, 22, 64), (OX, OY + gy * CELL), (OX + COLS * CELL, OY + gy * CELL), 1)
        pulse = 0.55 + 0.45 * math.sin(self.tick / 6)
        for sx, sy in self.sparks:
            cx, cy = OX + sx * CELL + CELL // 2, OY + sy * CELL + CELL // 2
            r = int(12 + 6 * pulse)
            pygame.draw.circle(surf, (90, 50, 10), (cx, cy), r + 8)
            pygame.draw.circle(surf, AMBER, (cx, cy), r)
            pygame.draw.circle(surf, CREAM, (cx, cy), 5)
        for b in self.bikes:
            for x, y, age in b.trail:
                if age > 40:
                    continue
                fade = 1 - age / 46
                col = tuple(max(0, min(255, int(c * (0.35 + 0.65 * fade)))) for c in b.color)
                rect = pygame.Rect(OX + x * CELL + 8, OY + y * CELL + 8, CELL - 16, CELL - 16)
                pygame.draw.rect(surf, col, rect, border_radius=10)
            if b.alive:
                hx = OX + b.x * CELL + CELL // 2
                hy = OY + b.y * CELL + CELL // 2
                nose = (hx + b.dx * 18, hy + b.dy * 18)
                pygame.draw.circle(surf, b.color, (hx, hy), 16)
                pygame.draw.circle(surf, CREAM, nose, 6)
                if b.flash:
                    pygame.draw.circle(surf, CREAM, (hx, hy), 22 + b.flash, 3)
        title = self.font.render("TAAFFEITE TRACE", True, LILAC)
        surf.blit(title, title.get_rect(center=(W // 2, 110)))
        sub = self.small.render("LIGHT-CYCLE  ·  PYTHON 3", True, SAFFRON)
        surf.blit(sub, sub.get_rect(center=(W // 2, 176)))
        sc = self.mid.render(f"SCORE  {self.score}", True, AMBER)
        surf.blit(sc, sc.get_rect(center=(W // 2, 236)))
        tag = self.mid.render("x.com/ElbowOS", True, AQUA)
        surf.blit(tag, tag.get_rect(center=(W // 2, H - 78)))

    def play_interactive(self):
        clock = pygame.time.Clock()
        running = True
        while running:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    running = False
                elif ev.type == pygame.KEYDOWN:
                    if ev.key in (pygame.K_LEFT, pygame.K_a):
                        self.turn(-1, 0)
                    elif ev.key in (pygame.K_RIGHT, pygame.K_d):
                        self.turn(1, 0)
                    elif ev.key in (pygame.K_UP, pygame.K_w):
                        self.turn(0, -1)
                    elif ev.key in (pygame.K_DOWN, pygame.K_s):
                        self.turn(0, 1)
                    elif ev.key == pygame.K_r:
                        self.reset()
            self.step(auto=False)
            self.draw(self.screen)
            pygame.display.flip()
            clock.tick(FPS)
        pygame.quit()

    def record(self):
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        cmd = [
            "ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
            "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "20", "-preset", "veryfast", "-movflags", "+faststart", OUT,
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        frames = FPS * SECS
        try:
            for _ in range(frames):
                self.step(auto=True)
                self.draw(self.screen)
                proc.stdin.write(pygame.image.tobytes(self.screen, "RGB"))
        finally:
            proc.stdin.close()
        err = proc.stderr.read().decode("utf-8", "ignore")
        rc = proc.wait()
        if rc != 0:
            raise SystemExit(f"ffmpeg failed ({rc}):\n{err[-1200:]}")
        alt = "/workspace/artifacts/TAAFFEITE_TRACE_ElbowOS.mp4"
        if os.path.abspath(OUT) != os.path.abspath(alt):
            import shutil
            shutil.copy2(OUT, alt)
        print("wrote", OUT)
        pygame.quit()

def main():
    g = Game()
    if PLAY and not RECORD:
        g.play_interactive()
    else:
        g.record()

if __name__ == "__main__":
    main()
