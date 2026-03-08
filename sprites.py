"""
sprites.py — Procedural sprite generators for the Dungeon Crawler.

Every visual asset is created entirely in code (no external image files).
Functions return ``pygame.Surface`` objects ready to blit.
"""

import math
import random

import pygame

from settings import (
    TILE_SIZE, HERO_SIZE, ENEMY_SIZE,
    SCREEN_WIDTH, SCREEN_HEIGHT,
    # Floor colours
    COLOR_BLACK, COLOR_FLOOR_BASE, COLOR_FLOOR_ACCENT1, COLOR_FLOOR_ACCENT2,
    COLOR_FLOOR_CRACK, COLOR_FLOOR_MOSS,
    # Wall colours
    COLOR_WALL_FACE, COLOR_WALL_TOP, COLOR_WALL_DARK,
    COLOR_WALL_HIGHLIGHT, COLOR_WALL_MORTAR,
    # Hero colours
    COLOR_HERO_BODY, COLOR_HERO_ARMOR, COLOR_HERO_ARMOR_LIGHT,
    COLOR_HERO_SKIN, COLOR_HERO_HAIR, COLOR_HERO_EYES,
    COLOR_HERO_CLOAK, COLOR_HERO_CLOAK_DARK,
    COLOR_HERO_SWORD_BLADE, COLOR_HERO_SWORD_HILT, COLOR_HERO_BOOTS,
    # Enemy colours
    COLOR_ENEMY_SKIN, COLOR_ENEMY_SKIN_LIGHT, COLOR_ENEMY_EYES,
    COLOR_ENEMY_HORN, COLOR_ENEMY_TEETH, COLOR_ENEMY_CLAWS,
)


# ── Floor tiles ──────────────────────────────────────────────────────────────

def _create_floor_tile(seed: int) -> pygame.Surface:
    """Create one atmospheric dungeon floor tile with cracks and moss."""
    rng = random.Random(seed)
    tile = pygame.Surface((TILE_SIZE, TILE_SIZE))
    tile.fill(COLOR_FLOOR_BASE)

    # Stone texture — subtle random rectangles
    for _ in range(6):
        rx = rng.randint(0, TILE_SIZE - 6)
        ry = rng.randint(0, TILE_SIZE - 6)
        rw = rng.randint(4, 12)
        rh = rng.randint(4, 12)
        shade = rng.choice([COLOR_FLOOR_ACCENT1, COLOR_FLOOR_ACCENT2,
                            COLOR_FLOOR_BASE])
        pygame.draw.rect(tile, shade, (rx, ry, rw, rh))

    # Cracks
    if rng.random() < 0.4:
        cx, cy = rng.randint(8, TILE_SIZE - 8), rng.randint(8, TILE_SIZE - 8)
        for _ in range(rng.randint(2, 5)):
            nx = cx + rng.randint(-8, 8)
            ny = cy + rng.randint(-8, 8)
            pygame.draw.line(tile, COLOR_FLOOR_CRACK, (cx, cy), (nx, ny), 1)
            cx, cy = nx, ny

    # Occasional moss spots
    if rng.random() < 0.15:
        mx = rng.randint(4, TILE_SIZE - 4)
        my = rng.randint(4, TILE_SIZE - 4)
        pygame.draw.circle(tile, COLOR_FLOOR_MOSS, (mx, my), rng.randint(2, 4))

    # Subtle noise dots
    for _ in range(8):
        dx = rng.randint(0, TILE_SIZE - 1)
        dy = rng.randint(0, TILE_SIZE - 1)
        v = rng.randint(18, 36)
        tile.set_at((dx, dy), (v, v - 2, v - 4))

    return tile


def create_floor_tiles(count: int = 8) -> list[pygame.Surface]:
    """Pre-generate *count* floor tile variations."""
    return [_create_floor_tile(i * 137 + 42) for i in range(count)]


# ── Wall sprite ──────────────────────────────────────────────────────────────

def create_wall_sprite() -> pygame.Surface:
    """Create a detailed dungeon wall block with brick pattern."""
    surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
    surf.fill(COLOR_WALL_FACE)

    # Top face (lighter — lit from above)
    top_height = 12
    pygame.draw.rect(surf, COLOR_WALL_TOP, (0, 0, TILE_SIZE, top_height))
    pygame.draw.line(surf, COLOR_WALL_HIGHLIGHT, (0, 0), (TILE_SIZE - 1, 0), 1)

    # Brick pattern on the face
    brick_h = 9
    mortar = 1
    row = 0
    y = top_height
    while y < TILE_SIZE:
        bh = min(brick_h, TILE_SIZE - y)
        offset = (TILE_SIZE // 4) if (row % 2 == 1) else 0
        x = -offset
        while x < TILE_SIZE:
            bw = TILE_SIZE // 2
            rx = max(x, 0)
            rw = min(x + bw, TILE_SIZE) - rx
            if rw > mortar:
                sr = max(0, min(255, COLOR_WALL_FACE[0] + random.randint(-6, 6)))
                sg = max(0, min(255, COLOR_WALL_FACE[1] + random.randint(-6, 6)))
                sb = max(0, min(255, COLOR_WALL_FACE[2] + random.randint(-6, 6)))
                pygame.draw.rect(surf, (sr, sg, sb),
                                 (rx + mortar, y + mortar, rw - mortar, bh - mortar))
            x += bw
        pygame.draw.line(surf, COLOR_WALL_MORTAR, (0, y), (TILE_SIZE, y), 1)
        row += 1
        y += brick_h

    # Vertical mortar lines
    for row_i in range(3):
        y_start = top_height + row_i * brick_h
        y_end = min(y_start + brick_h, TILE_SIZE)
        offset = (TILE_SIZE // 4) if (row_i % 2 == 1) else 0
        x = -offset + TILE_SIZE // 2
        while x < TILE_SIZE:
            if 0 <= x < TILE_SIZE:
                pygame.draw.line(surf, COLOR_WALL_MORTAR,
                                 (x, y_start), (x, y_end), 1)
            x += TILE_SIZE // 2

    # Depth edges
    pygame.draw.line(surf, COLOR_WALL_DARK,
                     (0, TILE_SIZE - 1), (TILE_SIZE - 1, TILE_SIZE - 1), 1)
    pygame.draw.line(surf, COLOR_WALL_DARK,
                     (TILE_SIZE - 1, 0), (TILE_SIZE - 1, TILE_SIZE - 1), 1)
    return surf


# ── Hero sprites (4 directions) ─────────────────────────────────────────────

def create_hero_sprites() -> dict[str, pygame.Surface]:
    """Return ``{'down', 'up', 'left', 'right'}`` hero surfaces."""
    sprites: dict[str, pygame.Surface] = {}

    for direction in ('down', 'up', 'left', 'right'):
        surf = pygame.Surface((HERO_SIZE, HERO_SIZE), pygame.SRCALPHA)
        cx = HERO_SIZE // 2
        cy = HERO_SIZE // 2

        if direction == 'down':
            pygame.draw.ellipse(surf, COLOR_HERO_CLOAK_DARK,
                                (cx - 10, cy + 2, 20, 16))
            pygame.draw.ellipse(surf, COLOR_HERO_BODY,
                                (cx - 8, cy - 6, 16, 18))
            pygame.draw.ellipse(surf, COLOR_HERO_ARMOR,
                                (cx - 6, cy - 4, 12, 12))
            pygame.draw.ellipse(surf, COLOR_HERO_ARMOR_LIGHT,
                                (cx - 3, cy - 3, 6, 6))
            pygame.draw.circle(surf, COLOR_HERO_SKIN, (cx, cy - 10), 7)
            pygame.draw.arc(surf, COLOR_HERO_HAIR,
                            (cx - 7, cy - 18, 14, 12), 0, math.pi, 3)
            pygame.draw.circle(surf, COLOR_HERO_EYES, (cx - 3, cy - 11), 2)
            pygame.draw.circle(surf, COLOR_HERO_EYES, (cx + 3, cy - 11), 2)
            pygame.draw.circle(surf, COLOR_BLACK, (cx - 3, cy - 10), 1)
            pygame.draw.circle(surf, COLOR_BLACK, (cx + 3, cy - 10), 1)
            pygame.draw.ellipse(surf, COLOR_HERO_BOOTS,
                                (cx - 7, cy + 12, 6, 5))
            pygame.draw.ellipse(surf, COLOR_HERO_BOOTS,
                                (cx + 1, cy + 12, 6, 5))
            pygame.draw.line(surf, COLOR_HERO_SWORD_BLADE,
                             (cx + 12, cy - 8), (cx + 12, cy + 8), 2)
            pygame.draw.line(surf, COLOR_HERO_SWORD_HILT,
                             (cx + 10, cy - 2), (cx + 14, cy - 2), 2)
            pygame.draw.circle(surf, COLOR_HERO_SWORD_HILT,
                               (cx + 12, cy - 9), 2)

        elif direction == 'up':
            pygame.draw.ellipse(surf, COLOR_HERO_CLOAK,
                                (cx - 11, cy - 2, 22, 20))
            pygame.draw.ellipse(surf, COLOR_HERO_CLOAK_DARK,
                                (cx - 9, cy + 6, 18, 12))
            pygame.draw.ellipse(surf, COLOR_HERO_BODY,
                                (cx - 8, cy - 6, 16, 18))
            pygame.draw.circle(surf, COLOR_HERO_HAIR, (cx, cy - 10), 7)
            pygame.draw.ellipse(surf, COLOR_HERO_BOOTS,
                                (cx - 7, cy + 12, 6, 5))
            pygame.draw.ellipse(surf, COLOR_HERO_BOOTS,
                                (cx + 1, cy + 12, 6, 5))
            pygame.draw.line(surf, COLOR_HERO_SWORD_BLADE,
                             (cx + 6, cy - 16), (cx + 4, cy + 4), 2)
            pygame.draw.line(surf, COLOR_HERO_SWORD_HILT,
                             (cx + 3, cy + 2), (cx + 7, cy - 2), 2)

        elif direction == 'left':
            pygame.draw.ellipse(surf, COLOR_HERO_CLOAK,
                                (cx - 2, cy - 2, 16, 18))
            pygame.draw.ellipse(surf, COLOR_HERO_CLOAK_DARK,
                                (cx + 2, cy + 6, 12, 12))
            pygame.draw.ellipse(surf, COLOR_HERO_BODY,
                                (cx - 6, cy - 6, 14, 18))
            pygame.draw.ellipse(surf, COLOR_HERO_ARMOR,
                                (cx - 5, cy - 4, 10, 12))
            pygame.draw.circle(surf, COLOR_HERO_SKIN, (cx - 2, cy - 10), 7)
            pygame.draw.arc(surf, COLOR_HERO_HAIR,
                            (cx - 9, cy - 18, 14, 14), 0, math.pi, 3)
            pygame.draw.circle(surf, COLOR_HERO_EYES, (cx - 6, cy - 11), 2)
            pygame.draw.circle(surf, COLOR_BLACK, (cx - 7, cy - 10), 1)
            pygame.draw.ellipse(surf, COLOR_HERO_BOOTS,
                                (cx - 9, cy + 12, 7, 5))
            pygame.draw.ellipse(surf, COLOR_HERO_BOOTS,
                                (cx - 4, cy + 13, 7, 4))
            pygame.draw.line(surf, COLOR_HERO_SWORD_BLADE,
                             (cx - 14, cy - 2), (cx - 4, cy - 2), 2)
            pygame.draw.line(surf, COLOR_HERO_SWORD_HILT,
                             (cx - 5, cy - 5), (cx - 5, cy + 1), 2)

        elif direction == 'right':
            pygame.draw.ellipse(surf, COLOR_HERO_CLOAK,
                                (cx - 14, cy - 2, 16, 18))
            pygame.draw.ellipse(surf, COLOR_HERO_CLOAK_DARK,
                                (cx - 14, cy + 6, 12, 12))
            pygame.draw.ellipse(surf, COLOR_HERO_BODY,
                                (cx - 8, cy - 6, 14, 18))
            pygame.draw.ellipse(surf, COLOR_HERO_ARMOR,
                                (cx - 5, cy - 4, 10, 12))
            pygame.draw.circle(surf, COLOR_HERO_SKIN, (cx + 2, cy - 10), 7)
            pygame.draw.arc(surf, COLOR_HERO_HAIR,
                            (cx - 5, cy - 18, 14, 14), 0, math.pi, 3)
            pygame.draw.circle(surf, COLOR_HERO_EYES, (cx + 6, cy - 11), 2)
            pygame.draw.circle(surf, COLOR_BLACK, (cx + 7, cy - 10), 1)
            pygame.draw.ellipse(surf, COLOR_HERO_BOOTS,
                                (cx + 2, cy + 12, 7, 5))
            pygame.draw.ellipse(surf, COLOR_HERO_BOOTS,
                                (cx - 3, cy + 13, 7, 4))
            pygame.draw.line(surf, COLOR_HERO_SWORD_BLADE,
                             (cx + 4, cy - 2), (cx + 14, cy - 2), 2)
            pygame.draw.line(surf, COLOR_HERO_SWORD_HILT,
                             (cx + 5, cy - 5), (cx + 5, cy + 1), 2)

        sprites[direction] = surf
    return sprites


# ── Enemy sprites (4 directions) ────────────────────────────────────────────

def create_enemy_sprites() -> dict[str, pygame.Surface]:
    """Return ``{'down', 'up', 'left', 'right'}`` goblin-like enemy surfaces."""
    sprites: dict[str, pygame.Surface] = {}
    S = ENEMY_SIZE

    for direction in ('down', 'up', 'left', 'right'):
        surf = pygame.Surface((S, S), pygame.SRCALPHA)
        cx = S // 2
        cy = S // 2

        if direction == 'down':
            # Body
            pygame.draw.ellipse(surf, COLOR_ENEMY_SKIN,
                                (cx - 8, cy - 4, 16, 16))
            pygame.draw.ellipse(surf, COLOR_ENEMY_SKIN_LIGHT,
                                (cx - 5, cy - 2, 10, 10))
            # Head
            pygame.draw.circle(surf, COLOR_ENEMY_SKIN, (cx, cy - 9), 7)
            # Ears (pointy)
            pygame.draw.polygon(surf, COLOR_ENEMY_SKIN,
                                [(cx - 7, cy - 10), (cx - 12, cy - 16),
                                 (cx - 4, cy - 13)])
            pygame.draw.polygon(surf, COLOR_ENEMY_SKIN,
                                [(cx + 7, cy - 10), (cx + 12, cy - 16),
                                 (cx + 4, cy - 13)])
            # Eyes (menacing red)
            pygame.draw.circle(surf, COLOR_ENEMY_EYES, (cx - 3, cy - 10), 2)
            pygame.draw.circle(surf, COLOR_ENEMY_EYES, (cx + 3, cy - 10), 2)
            pygame.draw.circle(surf, COLOR_BLACK, (cx - 3, cy - 10), 1)
            pygame.draw.circle(surf, COLOR_BLACK, (cx + 3, cy - 10), 1)
            # Teeth
            for tx in range(-2, 3, 2):
                pygame.draw.line(surf, COLOR_ENEMY_TEETH,
                                 (cx + tx, cy - 4), (cx + tx, cy - 2), 1)
            # Claws
            pygame.draw.line(surf, COLOR_ENEMY_CLAWS,
                             (cx - 10, cy + 4), (cx - 13, cy + 8), 2)
            pygame.draw.line(surf, COLOR_ENEMY_CLAWS,
                             (cx + 10, cy + 4), (cx + 13, cy + 8), 2)
            # Feet
            pygame.draw.ellipse(surf, COLOR_ENEMY_CLAWS,
                                (cx - 6, cy + 11, 5, 4))
            pygame.draw.ellipse(surf, COLOR_ENEMY_CLAWS,
                                (cx + 1, cy + 11, 5, 4))

        elif direction == 'up':
            pygame.draw.ellipse(surf, COLOR_ENEMY_SKIN,
                                (cx - 8, cy - 4, 16, 16))
            pygame.draw.circle(surf, COLOR_ENEMY_SKIN, (cx, cy - 9), 7)
            pygame.draw.polygon(surf, COLOR_ENEMY_SKIN,
                                [(cx - 7, cy - 10), (cx - 12, cy - 16),
                                 (cx - 4, cy - 13)])
            pygame.draw.polygon(surf, COLOR_ENEMY_SKIN,
                                [(cx + 7, cy - 10), (cx + 12, cy - 16),
                                 (cx + 4, cy - 13)])
            pygame.draw.ellipse(surf, COLOR_ENEMY_CLAWS,
                                (cx - 6, cy + 11, 5, 4))
            pygame.draw.ellipse(surf, COLOR_ENEMY_CLAWS,
                                (cx + 1, cy + 11, 5, 4))

        elif direction == 'left':
            pygame.draw.ellipse(surf, COLOR_ENEMY_SKIN,
                                (cx - 8, cy - 4, 14, 16))
            pygame.draw.circle(surf, COLOR_ENEMY_SKIN, (cx - 2, cy - 9), 7)
            pygame.draw.polygon(surf, COLOR_ENEMY_SKIN,
                                [(cx - 3, cy - 14), (cx - 8, cy - 20),
                                 (cx - 1, cy - 16)])
            pygame.draw.circle(surf, COLOR_ENEMY_EYES, (cx - 6, cy - 10), 2)
            pygame.draw.circle(surf, COLOR_BLACK, (cx - 7, cy - 10), 1)
            for ty in range(-2, 1):
                pygame.draw.line(surf, COLOR_ENEMY_TEETH,
                                 (cx - 8, cy + ty - 3),
                                 (cx - 10, cy + ty - 3), 1)
            pygame.draw.line(surf, COLOR_ENEMY_CLAWS,
                             (cx - 10, cy + 4), (cx - 14, cy + 6), 2)
            pygame.draw.ellipse(surf, COLOR_ENEMY_CLAWS,
                                (cx - 8, cy + 11, 5, 4))
            pygame.draw.ellipse(surf, COLOR_ENEMY_CLAWS,
                                (cx - 2, cy + 12, 5, 3))

        elif direction == 'right':
            pygame.draw.ellipse(surf, COLOR_ENEMY_SKIN,
                                (cx - 6, cy - 4, 14, 16))
            pygame.draw.circle(surf, COLOR_ENEMY_SKIN, (cx + 2, cy - 9), 7)
            pygame.draw.polygon(surf, COLOR_ENEMY_SKIN,
                                [(cx + 3, cy - 14), (cx + 8, cy - 20),
                                 (cx + 1, cy - 16)])
            pygame.draw.circle(surf, COLOR_ENEMY_EYES, (cx + 6, cy - 10), 2)
            pygame.draw.circle(surf, COLOR_BLACK, (cx + 7, cy - 10), 1)
            for ty in range(-2, 1):
                pygame.draw.line(surf, COLOR_ENEMY_TEETH,
                                 (cx + 8, cy + ty - 3),
                                 (cx + 10, cy + ty - 3), 1)
            pygame.draw.line(surf, COLOR_ENEMY_CLAWS,
                             (cx + 10, cy + 4), (cx + 14, cy + 6), 2)
            pygame.draw.ellipse(surf, COLOR_ENEMY_CLAWS,
                                (cx + 3, cy + 11, 5, 4))
            pygame.draw.ellipse(surf, COLOR_ENEMY_CLAWS,
                                (cx - 3, cy + 12, 5, 3))

        sprites[direction] = surf
    return sprites


def create_ranged_enemy_sprites() -> dict[str, pygame.Surface]:
    """Return sprites for ranged enemy variant."""
    sprites: dict[str, pygame.Surface] = {}
    S = ENEMY_SIZE

    for direction in ('down', 'up', 'left', 'right'):
        surf = pygame.Surface((S, S), pygame.SRCALPHA)
        cx = S // 2
        cy = S // 2

        # Base body in cooler tones
        base = (70, 90, 140)
        highlight = (110, 140, 200)
        pygame.draw.ellipse(surf, base, (cx - 8, cy - 4, 16, 16))
        pygame.draw.ellipse(surf, highlight, (cx - 6, cy - 2, 12, 12))

        # Hooded head
        pygame.draw.circle(surf, base, (cx, cy - 9), 7)
        pygame.draw.arc(surf, highlight, (cx - 7, cy - 16, 14, 12), 0, math.pi, 2)

        # Eyes (glowing blue)
        eye = (120, 200, 255)
        if direction in ('left', 'right'):
            offset = -2 if direction == 'left' else 2
            pygame.draw.circle(surf, eye, (cx + offset, cy - 10), 2)
            pygame.draw.circle(surf, COLOR_BLACK, (cx + offset, cy - 10), 1)
        else:
            pygame.draw.circle(surf, eye, (cx - 3, cy - 10), 2)
            pygame.draw.circle(surf, eye, (cx + 3, cy - 10), 2)
            pygame.draw.circle(surf, COLOR_BLACK, (cx - 3, cy - 10), 1)
            pygame.draw.circle(surf, COLOR_BLACK, (cx + 3, cy - 10), 1)

        # Staff/glow indicator
        pygame.draw.circle(surf, (160, 220, 255), (cx + 8, cy - 2), 3)

        sprites[direction] = surf
    return sprites


# ── Vignette overlay ─────────────────────────────────────────────────────────

def create_vignette(width: int = SCREEN_WIDTH,
                    height: int = SCREEN_HEIGHT) -> pygame.Surface:
    """Create a dark vignette overlay for atmospheric lighting."""
    vignette = pygame.Surface((width, height), pygame.SRCALPHA)

    steps = 40
    for i in range(steps):
        ratio = i / steps
        alpha = min(int(180 * (ratio ** 1.8)), 220)
        rect_w = int(width * (1 - ratio * 0.5))
        rect_h = int(height * (1 - ratio * 0.5))
        x = (width - rect_w) // 2
        y = (height - rect_h) // 2
        s = pygame.Surface((rect_w, rect_h), pygame.SRCALPHA)
        s.fill((0, 0, 0, 0))
        border = max(width, height) // steps + 2
        pygame.draw.rect(s, (0, 0, 0, alpha), (0, 0, rect_w, border))
        pygame.draw.rect(s, (0, 0, 0, alpha),
                         (0, rect_h - border, rect_w, border))
        pygame.draw.rect(s, (0, 0, 0, alpha), (0, 0, border, rect_h))
        pygame.draw.rect(s, (0, 0, 0, alpha),
                         (rect_w - border, 0, border, rect_h))
        vignette.blit(s, (x, y))

    return vignette
