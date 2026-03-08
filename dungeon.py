"""
dungeon.py — Dungeon environment: map rendering, wall collision rects,
and torch ambient lighting.
"""

import math
import random

import pygame

from settings import (
    TILE_SIZE, SCREEN_WIDTH, SCREEN_HEIGHT,
    DUNGEON_MAP, MAP_ROWS, MAP_COLS,
    COLOR_BLACK,
)
from sprites import create_floor_tiles, create_wall_sprite, create_vignette


class Torch:
    """A wall-mounted torch that flickers for atmosphere."""

    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y
        self.flicker_timer: float = random.uniform(0, math.pi * 2)
        self.base_radius: int = random.randint(50, 70)

    def update(self) -> None:
        self.flicker_timer += 0.08 + random.uniform(-0.01, 0.01)

    def draw(self, surface: pygame.Surface) -> None:
        flicker = (math.sin(self.flicker_timer) * 8
                   + math.sin(self.flicker_timer * 2.3) * 4)
        radius = int(self.base_radius + flicker)

        # Warm glow (additive)
        glow = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        for r in range(radius, 0, -2):
            alpha = int(25 * (r / radius))
            pygame.draw.circle(glow, (255, 180, 80, alpha), (radius, radius), r)
        surface.blit(glow, (self.x - radius, self.y - radius),
                     special_flags=pygame.BLEND_RGBA_ADD)

        # Flame
        flame_h = 6 + int(math.sin(self.flicker_timer * 3) * 2)
        pygame.draw.ellipse(surface, (255, 160, 40),
                            (self.x - 3, self.y - flame_h, 6, flame_h))
        pygame.draw.ellipse(surface, (255, 220, 100),
                            (self.x - 2, self.y - flame_h + 2, 4, flame_h - 2))


class Dungeon:
    """Manages the static dungeon map surface, wall collision rects,
    torches, and the atmospheric vignette overlay."""

    def __init__(self) -> None:
        # Pre-render the static floor + wall surface once
        self.surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.surface.fill(COLOR_BLACK)

        floor_tiles = create_floor_tiles(8)
        wall_sprite = create_wall_sprite()

        rng = random.Random(12345)

        # Assign random floor tile variant per cell
        tile_map: dict[tuple[int, int], int] = {}
        for row in range(MAP_ROWS):
            for col in range(MAP_COLS):
                tile_map[(row, col)] = rng.randint(0, len(floor_tiles) - 1)

        # Blit floor tiles
        for row in range(MAP_ROWS):
            for col in range(MAP_COLS):
                x = col * TILE_SIZE
                y = row * TILE_SIZE
                if DUNGEON_MAP[row][col] == 0:
                    self.surface.blit(floor_tiles[tile_map[(row, col)]], (x, y))

        # Build wall collision rects and draw walls
        self.wall_rects: list[pygame.Rect] = []
        for row in range(MAP_ROWS):
            for col in range(MAP_COLS):
                if DUNGEON_MAP[row][col] == 1:
                    x = col * TILE_SIZE
                    y = row * TILE_SIZE
                    self.surface.blit(wall_sprite, (x, y))
                    self.wall_rects.append(pygame.Rect(x, y, TILE_SIZE, TILE_SIZE))

        # Place torches on walls adjacent to open floor
        self.torches: list[Torch] = []
        for row in range(MAP_ROWS):
            for col in range(MAP_COLS):
                if DUNGEON_MAP[row][col] == 1:
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nr, nc = row + dr, col + dc
                        if 0 <= nr < MAP_ROWS and 0 <= nc < MAP_COLS:
                            if DUNGEON_MAP[nr][nc] == 0:
                                if rng.random() < 0.15:
                                    tx = col * TILE_SIZE + TILE_SIZE // 2
                                    ty = row * TILE_SIZE + TILE_SIZE // 2
                                    self.torches.append(Torch(tx, ty))
                                break

        # Vignette overlay (pre-rendered once)
        self.vignette = create_vignette()

    # ── helpers for spawning ─────────────────────────────────────────────

    def is_floor(self, row: int, col: int) -> bool:
        """Return True if (row, col) is a walkable floor tile."""
        if 0 <= row < MAP_ROWS and 0 <= col < MAP_COLS:
            return DUNGEON_MAP[row][col] == 0
        return False

    def get_edge_floor_tiles(self) -> list[tuple[int, int]]:
        """Return pixel positions of floor tiles on the outermost ring
        (row 1, last-1 row, col 1, last-1 col) — used for enemy spawning."""
        positions: list[tuple[int, int]] = []
        for row in range(MAP_ROWS):
            for col in range(MAP_COLS):
                if DUNGEON_MAP[row][col] != 0:
                    continue
                # Keep tiles that are on the second ring (just inside walls)
                if row <= 1 or row >= MAP_ROWS - 2 or col <= 1 or col >= MAP_COLS - 2:
                    px = col * TILE_SIZE + TILE_SIZE // 2
                    py = row * TILE_SIZE + TILE_SIZE // 2
                    positions.append((px, py))
        return positions

    # ── per-frame ────────────────────────────────────────────────────────

    def update(self) -> None:
        for torch in self.torches:
            torch.update()

    def draw_background(self, surface: pygame.Surface) -> None:
        """Draw the static dungeon (floor + walls)."""
        surface.blit(self.surface, (0, 0))

    def draw_torches(self, surface: pygame.Surface) -> None:
        """Draw flickering torch glow (call after background, before vignette)."""
        for torch in self.torches:
            torch.draw(surface)

    def draw_vignette(self, surface: pygame.Surface) -> None:
        """Draw the atmospheric vignette overlay (call last)."""
        surface.blit(self.vignette, (0, 0))
