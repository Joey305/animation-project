
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mindful Diabetes / University of Miami-inspired webseries opener
----------------------------------------------------------------
Miami-branded classroom/webseries intro with a cleaner host design.

Main fixes in this version:
- board is taller and less stretched
- lower-right topic sprites stay visible instead of disappearing
- board writing stays white chalk
- teacher back-of-head and front-of-head are drawn as separate clean poses
- front-facing teacher has filled long dark hair and an inviting smile
- slow natural side-to-side head motion only happens after turning forward
- hard board-title character limit is enforced in code and documented below

Assets expected in working directory:
- MDI_Logo.jpg   (or change LOGO_PATH below)
"""

import math
import os
import random
import shutil
import subprocess
import sys
from dataclasses import dataclass

import pygame

pygame.init()
pygame.font.init()

# -----------------------------------------------------------------------------
# Setup
# -----------------------------------------------------------------------------
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 30

TOTAL_DURATION = 15.0
WRITING_DURATION = 7.2
END_HOLD_DURATION = 2.8
BODY_DROP = 45

# Timing offsets so the opener breathes more before the board writing starts
INTRO_IN_DURATION = 1.4
INTRO_HOLD_DURATION = 1.6
TOPIC_REVEAL_START = 4.8
TOPIC_REVEAL_END = 6.4
WRITING_DELAY = 3.2


FRAMES_DIR = "frames"
VIDEO_NAME = "animation_video.mp4"
LOGO_PATH = "MDI_Logo.jpg"

SERIES_NAME = "Mindful Diabetes Classroom"
EPISODE_TOPIC = "How Exercise Recycles Proteins for Better Brain Health"
EPISODE_KICKER = "Tonight's Topic"
EPISODE_NUMBER = "EP. 01"
TOPIC_STYLES = ["protein", "brain", "spark", "dumbbell", "arrow"]
TOPIC_LABELS = ["Protein junk!", "Cell cleanup!", "Repair mode!", "Workout signal!", "Brain gain!"]
# -----------------------------------------------------------------------------
# #### BOARD TITLE CHARACTER LIMIT
# Use this exact limit so the chalk text does not run too far on the board.
# Reference example supplied by the user:
# "The Secret to Cleaning Up Your Cells: How Exercise Recycles Proteins for Better"
# Character count = 79
# Keep BOARD_TEXT at 79 characters or fewer.
# -----------------------------------------------------------------------------
BOARD_TEXT_CHAR_LIMIT = 79
# BOARD_TEXT = "The Secret to Cleaning Up Your Cells: How Exercise Recycles Proteins for Better"
BOARD_TEXT = "The More You Know! How Exercise Recycles Proteins for Better Brain Health!"

os.makedirs(FRAMES_DIR, exist_ok=True)

# -----------------------------------------------------------------------------
# Colors
# -----------------------------------------------------------------------------
WHITE = (248, 247, 243)
IVORY = (244, 239, 230)
BLACK = (19, 24, 28)
CHARCOAL = (35, 40, 52)

MIAMI_ORANGE = (245, 115, 32)
UM_ANGRY_GREEN = (0, 95, 74)
TRON_BLUE = (79, 224, 255)   # available for optional accents if needed
ELECTRIC_YELLOW = (255, 231, 68)

SAND = (232, 216, 194)
WARM_GRAY = (210, 208, 200)
DEEP_WOOD = (81, 50, 28)
COPPER = (170, 102, 54)
CORAL = (255, 126, 103)

CHALK = (248, 248, 244)
BOARD_MAIN = (6, 92, 82)
BOARD_DARK = (0, 64, 58)
FLOOR_WOOD = (124, 82, 49)
FLOOR_WOOD_DARK = (78, 48, 28)
WALL_TOP = (252, 246, 238)
WALL_BOTTOM = (233, 240, 242)

SKIN = (240, 213, 177)
ARM = (171, 101, 57)
SHIRT = (250, 250, 248)
PANTS = (39, 55, 99)
SHOE = (28, 28, 28)
HAIR = (45, 26, 18)
HAIR_HIGHLIGHT = (85, 57, 43)

TOPIC_COLORS = [MIAMI_ORANGE, ELECTRIC_YELLOW, UM_ANGRY_GREEN, COPPER, CORAL]

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Webseries Classroom Opener - Miami Brand v7")
clock = pygame.time.Clock()

# -----------------------------------------------------------------------------
# Fonts
# -----------------------------------------------------------------------------
def get_font(size, bold=False):
    name = "arial" if not bold else "arialbold"
    return pygame.font.SysFont(name, size)

FONT_SMALL = get_font(24)
FONT_BODY = get_font(32)
FONT_SUB = get_font(38, bold=True)
FONT_TITLE = get_font(54, bold=True)
FONT_BOARD = get_font(54, bold=False)
FONT_EP = get_font(26, bold=True)

# -----------------------------------------------------------------------------
# Assets
# -----------------------------------------------------------------------------
def load_logo(path):
    if os.path.exists(path):
        img = pygame.image.load(path).convert_alpha()
        return pygame.transform.smoothscale(img, (188, 188))
    surf = pygame.Surface((188, 188), pygame.SRCALPHA)
    pygame.draw.circle(surf, MIAMI_ORANGE, (94, 94), 88)
    pygame.draw.circle(surf, WHITE, (94, 94), 74)
    text = FONT_SUB.render("MDI", True, BLACK)
    surf.blit(text, text.get_rect(center=(94, 94)))
    return surf

mdi_logo = load_logo(LOGO_PATH)

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def validate_board_text(text):
    if len(text) > BOARD_TEXT_CHAR_LIMIT:
        raise ValueError(
            f"BOARD_TEXT is {len(text)} characters. Limit is {BOARD_TEXT_CHAR_LIMIT}. "
            "Shorten it so the title stays safely on the board."
        )

def ease_out_cubic(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3

def ease_in_out_sine(t):
    t = max(0.0, min(1.0, t))
    return -(math.cos(math.pi * t) - 1) / 2

def lerp(a, b, t):
    return a + (b - a) * t

def wrap_text(text, font, max_width):
    words = text.split()
    if not words:
        return [""]
    lines = [words[0]]
    for word in words[1:]:
        test = lines[-1] + " " + word
        if font.size(test)[0] <= max_width:
            lines[-1] = test
        else:
            lines.append(word)
    return lines

def draw_rounded_rect(surface, rect, color, radius=18, width=0):
    pygame.draw.rect(surface, color, rect, border_radius=radius, width=width)

def alpha_surface(size, color=(0, 0, 0, 0)):
    surf = pygame.Surface(size, pygame.SRCALPHA)
    surf.fill(color)
    return surf

def safe_clear_frames(directory):
    if not os.path.isdir(directory):
        os.makedirs(directory, exist_ok=True)
        return
    for name in os.listdir(directory):
        path = os.path.join(directory, name)
        if os.path.isfile(path) and name.lower().endswith(".png"):
            os.remove(path)

def draw_glow_outline(surface, rect, glow_color, line_color, radius=18, strength=3):
    glow = alpha_surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    for i in range(strength, 0, -1):
        alpha = 20 * i
        pygame.draw.rect(
            glow,
            (*glow_color, alpha),
            rect.inflate(i * 8, i * 8),
            border_radius=radius + i * 2,
            width=max(2, i * 2),
        )
    surface.blit(glow, (0, 0))
    pygame.draw.rect(surface, line_color, rect, width=3, border_radius=radius)

def draw_text_with_glow(surface, font, text, color, glow_color, pos, center=False, glow_strength=1):
    base = font.render(text, True, color)
    rect = base.get_rect(center=pos) if center else base.get_rect(topleft=pos)
    glow = alpha_surface((base.get_width() + 24, base.get_height() + 24))
    offsets = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    if glow_strength > 1:
        offsets += [(-2, 0), (2, 0), (0, -2), (0, 2), (-1, -1), (1, 1), (-1, 1), (1, -1)]
    for dx, dy in offsets:
        g = font.render(text, True, glow_color)
        glow.blit(g, (12 + dx, 12 + dy))
    surface.blit(glow, (rect.x - 12, rect.y - 12), special_flags=pygame.BLEND_RGBA_ADD)
    surface.blit(base, rect)
    return rect

def draw_lightning_border(surface, rect, color, seed_offset=0):
    rng = random.Random(1000 + seed_offset)
    points_top = []
    x = rect.left + 12
    while x < rect.right - 12:
        y = rect.top - rng.randint(2, 9)
        points_top.append((x, y))
        x += rng.randint(22, 42)
    points_bottom = []
    x = rect.left + 10
    while x < rect.right - 10:
        y = rect.bottom + rng.randint(2, 9)
        points_bottom.append((x, y))
        x += rng.randint(24, 44)
    if len(points_top) > 1:
        pygame.draw.lines(surface, color, False, points_top, 2)
    if len(points_bottom) > 1:
        pygame.draw.lines(surface, color, False, points_bottom, 2)

# -----------------------------------------------------------------------------
# Topic sprites
# -----------------------------------------------------------------------------
@dataclass
class TopicSprite:
    x: float
    y: float
    base_y: float
    drift: float
    speed: float
    radius: int
    color: tuple
    phase: float
    label: str
    style: str

TOPIC_STYLES = ["protein", "brain", "spark", "dumbbell", "arrow"]

def make_topic_sprites():
    sprites = []
    start_positions = [
        (965, 528),
        (1090, 554),
        (1182, 500),
        (1008, 635),
        (1185, 623),
    ]
    for i, (x, y) in enumerate(start_positions):
        sprites.append(
            TopicSprite(
                x=float(x),
                y=float(y),
                base_y=float(y),
                drift=random.choice([-1.1, -0.8, 0.8, 1.2]),
                speed=random.uniform(0.8, 1.25),
                radius=random.randint(28, 38),
                color=TOPIC_COLORS[i % len(TOPIC_COLORS)],
                phase=random.uniform(0, math.pi * 2),
                label=TOPIC_LABELS[i % len(TOPIC_LABELS)],
                style=TOPIC_STYLES[i % len(TOPIC_STYLES)],
            )
        )
    return sprites

topic_sprites = make_topic_sprites()

def draw_icon(surface, sprite: TopicSprite):
    x = int(sprite.x)
    y = int(sprite.y)
    r = sprite.radius
    c = sprite.color

    shadow = alpha_surface((r * 3, r * 2), (0, 0, 0, 50))
    pygame.draw.ellipse(shadow, (0, 0, 0, 60), (0, r, r * 2, r // 2))
    surface.blit(shadow, (x - r, y + r - 4))

    ring = alpha_surface((r * 2 + 40, r * 2 + 40))
    pygame.draw.circle(ring, (*ELECTRIC_YELLOW, 28), (r + 20, r + 20), r + 10)
    surface.blit(ring, (x - r - 20, y - r - 20), special_flags=pygame.BLEND_RGBA_ADD)

    pygame.draw.circle(surface, c, (x, y), r)
    pygame.draw.circle(surface, WHITE, (x, y), r - 8)
    pygame.draw.circle(surface, UM_ANGRY_GREEN, (x, y), r - 6, 2)

    if sprite.style == "protein":
        pts = [(x - 14, y + 2), (x - 4, y - 12), (x + 8, y - 4), (x + 16, y - 14), (x + 13, y + 8), (x - 2, y + 15)]
        pygame.draw.lines(surface, BLACK, False, pts, 4)
        for px, py in pts[1:-1]:
            pygame.draw.circle(surface, MIAMI_ORANGE, (px, py), 4)
    elif sprite.style == "brain":
        pygame.draw.circle(surface, CORAL, (x - 8, y), 12)
        pygame.draw.circle(surface, CORAL, (x + 8, y), 12)
        pygame.draw.circle(surface, CORAL, (x, y - 8), 11)
        pygame.draw.line(surface, BLACK, (x, y - 4), (x, y + 13), 3)
        pygame.draw.arc(surface, BLACK, (x - 16, y - 12, 14, 18), 4.8, 1.5, 2)
        pygame.draw.arc(surface, BLACK, (x + 2, y - 12, 14, 18), 1.6, 4.9, 2)
    elif sprite.style == "spark":
        points = [(x, y - 18), (x + 8, y - 4), (x + 20, y - 2), (x + 6, y + 8), (x + 10, y + 22), (x, y + 11), (x - 10, y + 22), (x - 6, y + 8), (x - 20, y - 2), (x - 8, y - 4)]
        pygame.draw.polygon(surface, ELECTRIC_YELLOW, points)
        pygame.draw.polygon(surface, BLACK, points, 2)
    elif sprite.style == "dumbbell":
        pygame.draw.rect(surface, BLACK, (x - 14, y - 3, 28, 6), border_radius=3)
        pygame.draw.rect(surface, COPPER, (x - 22, y - 11, 6, 22))
        pygame.draw.rect(surface, COPPER, (x - 16, y - 8, 5, 16))
        pygame.draw.rect(surface, COPPER, (x + 16, y - 11, 6, 22))
        pygame.draw.rect(surface, COPPER, (x + 11, y - 8, 5, 16))
    elif sprite.style == "arrow":
        pygame.draw.line(surface, UM_ANGRY_GREEN, (x - 15, y + 10), (x + 12, y - 12), 6)
        pygame.draw.polygon(surface, UM_ANGRY_GREEN, [(x + 12, y - 12), (x + 4, y - 12), (x + 13, y - 22), (x + 23, y - 14), (x + 17, y - 14)])

def draw_caption_bubble(surface, x, y, text, wobble=0.0):
    bubble_rect = pygame.Rect(0, 0, 166, 42)
    bubble_rect.center = (x, y - 64 + int(wobble))
    draw_glow_outline(surface, bubble_rect, ELECTRIC_YELLOW, DEEP_WOOD, radius=16, strength=2)
    draw_rounded_rect(surface, bubble_rect, WHITE, 16)
    pygame.draw.polygon(surface, WHITE, [(x - 8, bubble_rect.bottom - 2), (x + 8, bubble_rect.bottom - 2), (x, bubble_rect.bottom + 10)])
    label = FONT_SMALL.render(text, True, CHARCOAL)
    surface.blit(label, label.get_rect(center=bubble_rect.center))

def update_and_draw_topic_zone(surface, frame):
    for i, sprite in enumerate(topic_sprites):
        sprite.x += sprite.drift * sprite.speed
        sprite.y = sprite.base_y + math.sin(frame * 0.06 + sprite.phase) * 9
        if sprite.x < 930:
            sprite.drift = abs(sprite.drift)
        elif sprite.x > 1212:
            sprite.drift = -abs(sprite.drift)

        draw_icon(surface, sprite)
        if (frame // 24 + i) % 4 == 0:
            draw_caption_bubble(surface, int(sprite.x), int(sprite.y), sprite.label, math.sin(frame * 0.18 + i) * 2)

# -----------------------------------------------------------------------------
# Hair / head drawing
# -----------------------------------------------------------------------------
def draw_back_head(surface, cx, cy):
    # Full hair silhouette for the back-of-head pose.
    hair_points = [
        (cx - 48, cy - 28),
        (cx - 60, cy - 6),
        (cx - 58, cy + 24),
        (cx - 44, cy + 54),
        (cx - 18, cy + 70),
        (cx + 18, cy + 70),
        (cx + 44, cy + 54),
        (cx + 58, cy + 24),
        (cx + 60, cy - 6),
        (cx + 48, cy - 28),
        (cx + 16, cy - 58),
        (cx - 16, cy - 58),
    ]
    pygame.draw.polygon(surface, HAIR, hair_points)
    pygame.draw.arc(surface, HAIR_HIGHLIGHT, (cx - 34, cy - 42, 68, 36), math.pi * 1.05, math.pi * 1.95, 4)
    pygame.draw.arc(surface, HAIR_HIGHLIGHT, (cx - 40, cy - 20, 80, 60), math.pi * 1.05, math.pi * 1.95, 3)

def draw_front_hair(surface, cx, cy, sway=0):
    # Keep the front-facing hair simple and clean.
    # This creates a gentle top/back mass without letting the back-of-head silhouette
    # spill into the face from the sides.
    back_cap = [
        (cx - 40 + sway, cy - 26),
        (cx - 34 + sway, cy - 42),
        (cx - 14 + sway, cy - 56),
        (cx + 14 + sway, cy - 56),
        (cx + 34 + sway, cy - 42),
        (cx + 40 + sway, cy - 26),
        (cx + 34 + sway, cy - 4),
        (cx + 20 + sway, cy + 8),
        (cx - 20 + sway, cy + 8),
        (cx - 34 + sway, cy - 4),
    ]
    pygame.draw.polygon(surface, HAIR, back_cap)


def draw_front_hair_overlay(surface, cx, cy, sway=0):
    # Rounded top cap with a little more hair across the top.
    pygame.draw.ellipse(surface, HAIR, (cx - 48 + sway, cy - 58, 96, 36))
    pygame.draw.polygon(surface, HAIR, [
        (cx - 38 + sway, cy - 32),
        (cx - 48 + sway, cy - 6),
        (cx - 22 + sway, cy - 2),
        (cx, cy + 2),
        (cx + 22 + sway, cy - 2),
        (cx + 48 + sway, cy - 6),
        (cx + 38 + sway, cy - 32),
        (cx, cy - 56),
    ])
    pygame.draw.arc(surface, HAIR_HIGHLIGHT, (cx - 34 + sway, cy - 48, 68, 26), math.pi * 1.03, math.pi * 1.95, 3)

# -----------------------------------------------------------------------------
# Scene drawing
# -----------------------------------------------------------------------------
def draw_background(frame):
    for y in range(SCREEN_HEIGHT):
        blend = y / SCREEN_HEIGHT
        r = int(lerp(WALL_TOP[0], WALL_BOTTOM[0], blend))
        g = int(lerp(WALL_TOP[1], WALL_BOTTOM[1], blend))
        b = int(lerp(WALL_TOP[2], WALL_BOTTOM[2], blend))
        pygame.draw.line(screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))

    for x in range(20, SCREEN_WIDTH, 80):
        pygame.draw.line(screen, WARM_GRAY, (x, 0), (x, SCREEN_HEIGHT - 180), 1)
    for y in range(60, SCREEN_HEIGHT - 180, 78):
        pygame.draw.line(screen, WARM_GRAY, (0, y), (SCREEN_WIDTH, y), 1)

    pygame.draw.rect(screen, FLOOR_WOOD, (0, SCREEN_HEIGHT - 180, SCREEN_WIDTH, 180))
    for i in range(0, SCREEN_WIDTH, 80):
        pygame.draw.line(screen, FLOOR_WOOD_DARK, (i, SCREEN_HEIGHT - 180), (i + 28, SCREEN_HEIGHT), 2)

    pygame.draw.rect(screen, MIAMI_ORANGE, (0, 0, SCREEN_WIDTH, 16))
    pygame.draw.rect(screen, UM_ANGRY_GREEN, (0, 16, SCREEN_WIDTH, 16))

    cx, cy = 130, 98
    pygame.draw.circle(screen, BLACK, (cx, cy), 48)
    pygame.draw.circle(screen, WHITE, (cx, cy), 45)
    ang1 = -math.pi / 2 + math.sin(frame * 0.01) * 0.1
    ang2 = frame * 0.02 - math.pi / 2
    pygame.draw.line(screen, BLACK, (cx, cy), (cx + int(math.cos(ang1) * 18), cy + int(math.sin(ang1) * 18)), 5)
    pygame.draw.line(screen, BLACK, (cx, cy), (cx + int(math.cos(ang2) * 30), cy + int(math.sin(ang2) * 30)), 3)

    frame_rect = pygame.Rect(1002, 112, 210, 210)
    draw_glow_outline(screen, frame_rect, ELECTRIC_YELLOW, UM_ANGRY_GREEN, radius=24, strength=3)
    draw_rounded_rect(screen, frame_rect, IVORY, 24)
    pygame.draw.rect(screen, MIAMI_ORANGE, frame_rect, 4, border_radius=24)
    draw_lightning_border(screen, frame_rect, ELECTRIC_YELLOW, seed_offset=frame)
    screen.blit(mdi_logo, mdi_logo.get_rect(center=frame_rect.center))

def draw_top_branding(frame):
    tag = pygame.Rect(40, 44, 210, 40)
    draw_glow_outline(screen, tag, ELECTRIC_YELLOW, MIAMI_ORANGE, radius=14, strength=2)
    draw_rounded_rect(screen, tag, UM_ANGRY_GREEN, 14)
    txt = FONT_EP.render(EPISODE_NUMBER, True, WHITE)
    screen.blit(txt, txt.get_rect(center=tag.center))
    draw_text_with_glow(screen, FONT_SMALL, SERIES_NAME, WHITE, ELECTRIC_YELLOW, (40, 94), center=False)

def draw_board():
    board_rect = pygame.Rect(50, 34, 860, 430)
    shadow = alpha_surface((board_rect.width + 30, board_rect.height + 30), (0, 0, 0, 0))
    draw_rounded_rect(shadow, shadow.get_rect(), (0, 0, 0, 60), 22)
    screen.blit(shadow, (board_rect.x + 8, board_rect.y + 8))

    outer = board_rect.inflate(10, 10)
    draw_glow_outline(screen, outer, ELECTRIC_YELLOW, MIAMI_ORANGE, radius=24, strength=3)
    draw_rounded_rect(screen, board_rect, BOARD_MAIN, 20)
    pygame.draw.rect(screen, BOARD_DARK, board_rect, 8, border_radius=20)

    random.seed(7)
    for _ in range(24):
        sx = random.randint(board_rect.x + 20, board_rect.right - 60)
        sy = random.randint(board_rect.y + 18, board_rect.bottom - 30)
        sw = random.randint(24, 70)
        sh = random.randint(4, 10)
        surf = alpha_surface((sw, sh), (255, 255, 255, random.randint(8, 18)))
        screen.blit(surf, (sx, sy))

    # corner accents
    pygame.draw.line(screen, ELECTRIC_YELLOW, (board_rect.x + 16, board_rect.y + 18), (board_rect.x + 86, board_rect.y + 18), 3)
    pygame.draw.line(screen, ELECTRIC_YELLOW, (board_rect.x + 16, board_rect.y + 18), (board_rect.x + 16, board_rect.y + 86), 3)
    pygame.draw.line(screen, ELECTRIC_YELLOW, (board_rect.right - 16, board_rect.bottom - 18), (board_rect.right - 86, board_rect.bottom - 18), 3)
    pygame.draw.line(screen, ELECTRIC_YELLOW, (board_rect.right - 16, board_rect.bottom - 18), (board_rect.right - 16, board_rect.bottom - 86), 3)

    # tray
    pygame.draw.rect(screen, FLOOR_WOOD_DARK, (92, 450, 610, 18), border_radius=9)
    pygame.draw.rect(screen, CHALK, (135, 452, 90, 8), border_radius=4)
    pygame.draw.rect(screen, ELECTRIC_YELLOW, (245, 452, 28, 8), border_radius=4)



def draw_electric_arc(surface, start, end, color, frame, amplitude=6, segments=6, width=2):
    points = [start]
    sx, sy = start
    ex, ey = end
    for i in range(1, segments):
        t = i / segments
        x = sx + (ex - sx) * t
        y = sy + (ey - sy) * t
        wobble = math.sin(frame * 0.35 + i * 1.7) * amplitude
        if abs(ex - sx) > abs(ey - sy):
            y += wobble
        else:
            x += wobble
        points.append((x, y))
    points.append(end)
    pygame.draw.lines(surface, color, False, points, width)

def draw_card_shimmer(surface, rect, frame, alpha=38):
    shimmer = alpha_surface((rect.width, rect.height))
    band_x = int((frame * 8) % (rect.width + 80)) - 80
    for i in range(80):
        x = band_x + i
        if 0 <= x < rect.width:
            a = int(alpha * (1 - abs(i - 40) / 40))
            pygame.draw.line(shimmer, (255, 255, 255, max(0, a)), (x, 0), (x, rect.height), 1)
    surface.blit(shimmer, rect.topleft, special_flags=pygame.BLEND_RGBA_ADD)

def draw_power_orbs(surface, rect, frame, color):
    corners = [
        (rect.left + 14, rect.top + 14),
        (rect.right - 14, rect.top + 14),
        (rect.left + 14, rect.bottom - 14),
        (rect.right - 14, rect.bottom - 14),
    ]
    for i, (cx, cy) in enumerate(corners):
        pulse = 1 + 0.18 * math.sin(frame * 0.18 + i * 1.4)
        glow = alpha_surface((40, 40))
        pygame.draw.circle(glow, (*color, 55), (20, 20), int(8 * pulse))
        surface.blit(glow, (cx - 20, cy - 20), special_flags=pygame.BLEND_RGBA_ADD)
        pygame.draw.circle(surface, color, (cx, cy), max(2, int(3 * pulse)))

def draw_live_card_energy(surface, rect, frame):
    pulse_alpha = 18 + int(10 * math.sin(frame * 0.14))
    pulse_layer = alpha_surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.draw.rect(
        pulse_layer,
        (*ELECTRIC_YELLOW, pulse_alpha),
        rect.inflate(10, 10),
        border_radius=26,
        width=2,
    )
    surface.blit(pulse_layer, (0, 0))

    draw_card_shimmer(surface, rect, frame, alpha=32)
    draw_power_orbs(surface, rect, frame, ELECTRIC_YELLOW)

    # top-left small arc
    draw_electric_arc(
        surface,
        (rect.left + 8, rect.top + 28),
        (rect.left + 42, rect.top + 8),
        ELECTRIC_YELLOW,
        frame,
        amplitude=3,
        segments=5,
        width=2,
    )

    # bottom-right small arc
    draw_electric_arc(
        surface,
        (rect.right - 42, rect.bottom - 8),
        (rect.right - 8, rect.bottom - 28),
        ELECTRIC_YELLOW,
        frame + 7,
        amplitude=3,
        segments=5,
        width=2,
    )


def draw_intro_card(frame):
    intro_in_frames = int(INTRO_IN_DURATION * FPS)
    intro_hold_frames = int(INTRO_HOLD_DURATION * FPS)
    intro_total_frames = intro_in_frames + intro_hold_frames

    if frame > intro_total_frames:
        return

    if frame <= intro_in_frames:
        t = ease_out_cubic(frame / max(1, intro_in_frames))
    else:
        t = 1.0

    hover_y = 0
    if frame > intro_in_frames:
        hover_y = math.sin((frame - intro_in_frames) * 0.10) * 2.0

    card_w = int(lerp(60, 1030, t))
    card_h = int(lerp(20, 178, t))
    rect = pygame.Rect(0, 0, card_w, card_h)
    rect.center = (SCREEN_WIDTH // 2, int(166 + hover_y))

    layer = alpha_surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.draw.rect(layer, (255, 255, 255, int(234 * t)), rect, border_radius=28)
    screen.blit(layer, (0, 0))

    glow_strength = 3 + (1 if math.sin(frame * 0.22) > 0.75 else 0)
    draw_glow_outline(screen, rect, ELECTRIC_YELLOW, MIAMI_ORANGE, radius=28, strength=glow_strength)
    draw_live_card_energy(screen, rect, frame)

    if t > 0.4:
        y_jitter = math.sin(frame * 0.12) * 1.5
        draw_text_with_glow(
            screen, FONT_EP, EPISODE_KICKER.upper(),
            MIAMI_ORANGE, ELECTRIC_YELLOW,
            (SCREEN_WIDTH // 2, rect.y + 40 + y_jitter), center=True
        )
        draw_text_with_glow(
            screen, FONT_TITLE, SERIES_NAME.upper(),
            UM_ANGRY_GREEN, ELECTRIC_YELLOW,
            (SCREEN_WIDTH // 2, rect.y + 88 + y_jitter), center=True
        )
        draw_text_with_glow(
            screen, FONT_BODY, "science made visual, funny, and memorable",
            CHARCOAL, ELECTRIC_YELLOW,
            (SCREEN_WIDTH // 2, rect.y + 134 + y_jitter), center=True
        )


def draw_topic_card(frame):
    reveal_start = int(TOPIC_REVEAL_START * FPS)
    reveal_end = int(TOPIC_REVEAL_END * FPS)
    if frame < reveal_start:
        return

    t = ease_in_out_sine((frame - reveal_start) / max(1, (reveal_end - reveal_start)))
    card = pygame.Rect(0, 0, 286, 170)
    card.topleft = (930, int(90 - (1 - t) * 36))

    layer = alpha_surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.draw.rect(layer, (255, 255, 255, int(238 * t)), card, border_radius=22)
    screen.blit(layer, (0, 0))

    glow_strength = 3 + (1 if math.sin(frame * 0.28) > 0.82 else 0)
    draw_glow_outline(screen, card, ELECTRIC_YELLOW, MIAMI_ORANGE, radius=22, strength=glow_strength)
    draw_live_card_energy(screen, card, frame)

    if t > 0.2:
        header_font = FONT_SUB
        topic_font = get_font(26, bold=True)
        footer_font = get_font(22, bold=False)

        header_y = card.y + 12
        topic_y = card.y + 56
        footer_y = card.bottom - 30

        draw_text_with_glow(
            screen, header_font, "TONIGHT'S TOPIC",
            MIAMI_ORANGE, ELECTRIC_YELLOW,
            (card.x + 14, header_y), center=False
        )

        pygame.draw.line(screen, WARM_GRAY, (card.x + 14, footer_y - 8), (card.right - 14, footer_y - 8), 1)

        topic_lines = wrap_text(EPISODE_TOPIC, topic_font, 228)
        max_topic_bottom = footer_y - 16
        line_step = 31
        y = topic_y

        for idx, line in enumerate(topic_lines):
            if y + 24 > max_topic_bottom:
                break
            line_wobble = math.sin(frame * 0.10 + idx * 0.8) * 0.8
            draw_text_with_glow(
                screen, topic_font, line,
                UM_ANGRY_GREEN, ELECTRIC_YELLOW,
                (card.x + 14, y + line_wobble), center=False
            )
            y += line_step

        draw_text_with_glow(
            screen, footer_font, "Big science. Clear stories.",
            CHARCOAL, ELECTRIC_YELLOW,
            (card.x + 14, footer_y), center=False
        )





def draw_teacher_writing(x, y, arm_up, frame):
    bob = math.sin(frame * 0.14) * 2
    head_x = x
    head_y = int(y - 96 + bob)

    body_y = y + BODY_DROP

    pygame.draw.line(screen, PANTS, (x, body_y + 72), (x - 64, body_y + 190), 16)
    pygame.draw.line(screen, PANTS, (x, body_y + 72), (x + 62, body_y + 190), 16)
    pygame.draw.line(screen, SHOE, (x - 82, body_y + 192), (x - 46, body_y + 192), 8)
    pygame.draw.line(screen, SHOE, (x + 42, body_y + 192), (x + 78, body_y + 192), 8)
    pygame.draw.rect(screen, SHIRT, (x - 60, body_y - 82, 120, 164), border_radius=18)

    draw_back_head(screen, head_x, head_y)

    pygame.draw.line(screen, ARM, (x + 10, body_y - 22), (x + 94, body_y + 24), 14)
    end = (x - 132, body_y - 116) if arm_up else (x - 130, body_y - 44)
    pygame.draw.line(screen, ARM, (x - 34, body_y - 22), end, 14)
    pygame.draw.circle(screen, SKIN, end, 11)
    pygame.draw.rect(screen, CHALK, (end[0] - 9, end[1] - 4, 18, 8), border_radius=3)


def draw_teacher_front(x, y, frame):
    wave = math.sin(frame * 0.22)
    body_y = y + BODY_DROP
    arm_y = body_y - 100 + wave * 16

    head_turn = math.sin(frame * 0.055) * 6
    head_x = int(x + head_turn)
    head_y = int(y - 82 + math.sin(frame * 0.09) * 1.5)

    # body
    pygame.draw.line(screen, PANTS, (x, body_y + 76), (x - 64, body_y + 190), 16)
    pygame.draw.line(screen, PANTS, (x, body_y + 76), (x + 62, body_y + 190), 16)
    pygame.draw.line(screen, SHOE, (x - 82, body_y + 192), (x - 46, body_y + 192), 8)
    pygame.draw.line(screen, SHOE, (x + 42, body_y + 192), (x + 78, body_y + 192), 8)
    pygame.draw.rect(screen, SHIRT, (x - 60, body_y - 82, 120, 164), border_radius=18)

    logo_small = pygame.transform.smoothscale(mdi_logo, (68, 68))
    screen.blit(logo_small, logo_small.get_rect(center=(x, body_y + 10)))

    sway = int(head_turn * 0.10)

    hair_back = [
        (head_x - 46 + sway, head_y - 26),
        (head_x - 38 + sway, head_y - 48),
        (head_x - 18 + sway, head_y - 62),
        (head_x + 18 + sway, head_y - 62),
        (head_x + 38 + sway, head_y - 48),
        (head_x + 46 + sway, head_y - 26),
        (head_x + 42 + sway, head_y + 8),
        (head_x + 30 + sway, head_y + 34),
        (head_x + 14 + sway, head_y + 48),
        (head_x - 14 + sway, head_y + 48),
        (head_x - 30 + sway, head_y + 34),
        (head_x - 42 + sway, head_y + 8),
    ]
    pygame.draw.polygon(screen, HAIR, hair_back)

    pygame.draw.arc(
        screen,
        HAIR_HIGHLIGHT,
        (head_x - 30 + sway, head_y - 54, 60, 20),
        math.pi * 1.05,
        math.pi * 1.95,
        2,
    )

    pygame.draw.circle(screen, SKIN, (head_x, head_y), 52)

    top_cap = [
        (head_x - 34 + sway, head_y - 28),
        (head_x - 42 + sway, head_y - 48),
        (head_x - 14 + sway, head_y - 58),
        (head_x + 14 + sway, head_y - 58),
        (head_x + 42 + sway, head_y - 48),
        (head_x + 34 + sway, head_y - 28),
        (head_x + 12 + sway, head_y - 18),
        (head_x,             head_y - 14),
        (head_x - 12 + sway, head_y - 18),
    ]
    pygame.draw.polygon(screen, HAIR, top_cap)

    eye_offset = int(head_turn * 0.10)
    pygame.draw.circle(screen, BLACK, (head_x - 14 + eye_offset, head_y - 8), 4)
    pygame.draw.circle(screen, BLACK, (head_x + 14 + eye_offset, head_y - 8), 4)

    pygame.draw.arc(
        screen,
        BLACK,
        (head_x - 16, head_y + 14, 32, 16),
        math.pi + 0.25,
        (2 * math.pi) - 0.25,
        3,
    )

    pygame.draw.line(screen, ARM, (x + 38, body_y - 8), (x + 102, body_y + 46), 14)
    pygame.draw.line(screen, ARM, (x - 40, body_y - 14), (x - 130, arm_y), 14)
    pygame.draw.circle(screen, SKIN, (x - 130, int(arm_y)), 12)
    pygame.draw.line(screen, BLACK, (x - 120, int(arm_y - 4)), (x - 112, int(arm_y - 18)), 4)



def draw_board_text(frame):
    validate_board_text(BOARD_TEXT)
    lines = wrap_text(BOARD_TEXT, FONT_BOARD, 720)
    total_chars = sum(len(line) for line in lines)

    writing_delay_frames = int(WRITING_DELAY * FPS)
    writing_frames = int(WRITING_DURATION * FPS)

    progress = 0.0
    if frame > writing_delay_frames:
        progress = min((frame - writing_delay_frames) / max(1, writing_frames), 1.0)

    visible = int(total_chars * progress)

    x = 82
    y = 92
    remaining = visible
    last_char_pos = (x, y)

    for i, line in enumerate(lines):
        ty = y + i * 62
        if remaining >= len(line):
            screen.blit(FONT_BOARD.render(line, True, CHALK), (x, ty))
            if line:
                w = FONT_BOARD.size(line)[0]
                last_char_pos = (x + w, ty + 26)
            remaining -= len(line)
        else:
            partial = line[:max(0, remaining)]
            screen.blit(FONT_BOARD.render(partial, True, CHALK), (x, ty))
            w = FONT_BOARD.size(partial)[0]
            last_char_pos = (x + w, ty + 26)
            remaining = 0
            break

    if writing_delay_frames < frame < writing_delay_frames + writing_frames:
        glow = alpha_surface((50, 50))
        pygame.draw.circle(glow, (*ELECTRIC_YELLOW, 90), (25, 25), 12)
        screen.blit(glow, (last_char_pos[0] - 17, last_char_pos[1] - 25), special_flags=pygame.BLEND_RGBA_ADD)
        pygame.draw.circle(screen, ELECTRIC_YELLOW, (last_char_pos[0] + 8, last_char_pos[1]), 6)
        pygame.draw.circle(screen, WHITE, (last_char_pos[0] + 8, last_char_pos[1]), 3)

    underline_start_progress = 0.72
    if progress > underline_start_progress:
        t = ease_out_cubic((progress - underline_start_progress) / (1.0 - underline_start_progress))
        start_x = 88
        end_x = int(88 + 690 * max(0, min(t, 1)))
        pygame.draw.line(screen, ELECTRIC_YELLOW, (start_x, 320), (end_x, 320), 4)

def draw_dust(frame):
    for i in range(6):
        px = 208 + i * 8 + int(math.sin(frame * 0.13 + i) * 4)
        py = 396 + i * 3 - int(frame % 12)
        pygame.draw.circle(screen, (255, 255, 255), (px, py), 2)
        glow = alpha_surface((20, 20))
        pygame.draw.circle(glow, (*ELECTRIC_YELLOW, 36), (10, 10), 6)
        screen.blit(glow, (px - 10, py - 10), special_flags=pygame.BLEND_RGBA_ADD)


def draw_logo_expansion(frame, total_frames):
    start = int((TOTAL_DURATION - END_HOLD_DURATION) * FPS)
    if frame < start:
        return

    t = ease_out_cubic((frame - start) / max(1, (total_frames - start)))

    # start from the framed logo area on the wall
    start_cx, start_cy = 1107, 218

    # end centered on screen
    end_cx, end_cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2

    cx = int(lerp(start_cx, end_cx, t))
    cy = int(lerp(start_cy, end_cy, t))

    # scale until the image covers the whole screen
    base_w, base_h = mdi_logo.get_width(), mdi_logo.get_height()
    cover_scale = max(SCREEN_WIDTH / base_w, SCREEN_HEIGHT / base_h) * 1.02
    scale = lerp(1.0, cover_scale, t)

    w = max(1, int(base_w * scale))
    h = max(1, int(base_h * scale))
    logo = pygame.transform.smoothscale(mdi_logo, (w, h))

    left = cx - w // 2
    top = cy - h // 2

    # optional glow during travel
    glow = alpha_surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.draw.circle(
        glow,
        (*ELECTRIC_YELLOW, int(80 * (1 - t) + 20)),
        (cx, cy),
        int(120 + 220 * t),
    )
    screen.blit(glow, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

    screen.blit(logo, (left, top))



def generate_video():
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path is None:
        print("⚠️ ffmpeg was not found on PATH. Frames were saved, but video was not created.")
        return
    try:
        subprocess.run(
            [
                ffmpeg_path,
                "-y",
                "-r", str(FPS),
                "-i", os.path.join(FRAMES_DIR, "frame_%04d.png"),
                "-vcodec", "libx264",
                "-crf", "20",
                "-pix_fmt", "yuv420p",
                VIDEO_NAME,
            ],
            check=True,
        )
        print(f"✅ Video created successfully: {VIDEO_NAME}")
    except subprocess.CalledProcessError as exc:
        print(f"❌ Error creating video: {exc}")

def main():
    validate_board_text(BOARD_TEXT)
    safe_clear_frames(FRAMES_DIR)

    total_frames = int(TOTAL_DURATION * FPS)
    writing_delay_frames = int(WRITING_DELAY * FPS)
    writing_frames = int(WRITING_DURATION * FPS)
    teacher_x, teacher_y = 345, 544

    for frame in range(total_frames):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        draw_background(frame)
        draw_top_branding(frame)
        draw_board()
        draw_intro_card(frame)
        draw_topic_card(frame)
        draw_board_text(frame)
        update_and_draw_topic_zone(screen, frame)

        turned = frame >= (writing_delay_frames + writing_frames)
        if not turned:
            arm_up = (frame // 6) % 2 == 0
            draw_teacher_writing(teacher_x, teacher_y, arm_up, frame)
            draw_dust(frame)
        else:
            draw_teacher_front(teacher_x, teacher_y, frame)

        draw_logo_expansion(frame, total_frames)

        pygame.display.flip()
        pygame.image.save(screen, os.path.join(FRAMES_DIR, f"frame_{frame:04d}.png"))
        clock.tick(FPS)

    generate_video()
    pygame.quit()

if __name__ == "__main__":
    main()
