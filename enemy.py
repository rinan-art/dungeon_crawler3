"""
enemy.py — Enemy entity that tracks and moves toward the player.

Enemies spawn from open floor tiles near the screen edges and constantly
navigate toward the hero's current position while respecting wall
collisions.
"""

import math

import pygame

from settings import (
    ENEMY_SIZE, ENEMY_SPEED, SCREEN_WIDTH, SCREEN_HEIGHT,
    RANGED_ENEMY_SPEED, RANGED_ENEMY_MIN_DISTANCE, RANGED_ENEMY_MAX_DISTANCE,
    RANGED_ENEMY_SHOOT_COOLDOWN_MS,
)


class Enemy:
    """A goblin-like creature that chases the hero."""

    def __init__(self, x: float, y: float,
                 sprites: dict[str, pygame.Surface]) -> None:
        self.x = x
        self.y = y
        self.sprites = sprites
        self.facing: str = 'down'
        self.speed: float = ENEMY_SPEED
        self.width: int = ENEMY_SIZE
        self.height: int = ENEMY_SIZE
        self.hitbox_shrink: int = 4
        self.alive: bool = True

        # Simple bob animation
        self.bob_timer: float = 0.0

    # ── helpers ──────────────────────────────────────────────────────────

    @property
    def center_x(self) -> float:
        return self.x + self.width / 2

    @property
    def center_y(self) -> float:
        return self.y + self.height / 2

    def get_hitbox(self) -> pygame.Rect:
        s = self.hitbox_shrink
        return pygame.Rect(self.x + s, self.y + s,
                           self.width - 2 * s, self.height - 2 * s)

    # ── per-frame update ─────────────────────────────────────────────────

    def update(self, target_x: float, target_y: float,
               walls: list[pygame.Rect]) -> None:
        """Move toward (*target_x*, *target_y*) — the hero's centre."""
        if not self.alive:
            return

        # Direction vector toward the target
        dx = target_x - self.center_x
        dy = target_y - self.center_y
        dist = math.hypot(dx, dy)

        if dist < 1.0:
            # Basically on top of the target — don't jitter
            return

        # Normalise
        dx /= dist
        dy /= dist

        # Update facing direction
        if abs(dx) >= abs(dy):
            self.facing = 'left' if dx < 0 else 'right'
        else:
            self.facing = 'up' if dy < 0 else 'down'

        # Axis-separated movement with wall collision (same technique as hero)
        if dx != 0:
            self.x += dx * self.speed
            self._resolve_wall_collisions(walls, axis='x', delta=dx)
        if dy != 0:
            self.y += dy * self.speed
            self._resolve_wall_collisions(walls, axis='y', delta=dy)

        # Screen boundary clamping
        self.x = max(0, min(self.x, SCREEN_WIDTH - self.width))
        self.y = max(0, min(self.y, SCREEN_HEIGHT - self.height))

        # Bob timer
        self.bob_timer += 0.12

    # ── wall collision ───────────────────────────────────────────────────

    def _resolve_wall_collisions(self, walls: list[pygame.Rect],
                                 axis: str, delta: float) -> None:
        hitbox = self.get_hitbox()
        for wall_rect in walls:
            if hitbox.colliderect(wall_rect):
                if axis == 'x':
                    if delta > 0:
                        self.x = wall_rect.left - self.width + self.hitbox_shrink
                    else:
                        self.x = wall_rect.right - self.hitbox_shrink
                else:
                    if delta > 0:
                        self.y = wall_rect.top - self.height + self.hitbox_shrink
                    else:
                        self.y = wall_rect.bottom - self.hitbox_shrink
                hitbox = self.get_hitbox()

    # ── drawing ──────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface) -> None:
        if not self.alive:
            return

        sprite = self.sprites[self.facing]
        bob = int(math.sin(self.bob_timer) * 1.2)
        surface.blit(sprite, (int(self.x), int(self.y) + bob))

        # Shadow
        shadow = pygame.Surface((self.width - 6, 5), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 50),
                            (0, 0, self.width - 6, 5))
        surface.blit(shadow,
                     (int(self.x) + 3,
                      int(self.y) + self.height - 2 + bob))


class RangedEnemy(Enemy):
    """Enemy that keeps distance and fires projectiles."""

    def __init__(self, x: float, y: float,
                 sprites: dict[str, pygame.Surface]) -> None:
        super().__init__(x, y, sprites)
        self.speed = RANGED_ENEMY_SPEED
        self._last_shot_ms: int = 0

    def update(self, target_x: float, target_y: float,
               walls: list[pygame.Rect]) -> bool:
        """Move to maintain range. Returns True if it should shoot."""
        if not self.alive:
            return False

        dx = target_x - self.center_x
        dy = target_y - self.center_y
        dist = math.hypot(dx, dy)
        if dist < 1.0:
            return False

        move_dir = 0.0
        if dist < RANGED_ENEMY_MIN_DISTANCE:
            move_dir = -1.0
        elif dist > RANGED_ENEMY_MAX_DISTANCE:
            move_dir = 1.0

        if move_dir != 0.0:
            dx /= dist
            dy /= dist
            if abs(dx) >= abs(dy):
                self.facing = 'left' if dx < 0 else 'right'
            else:
                self.facing = 'up' if dy < 0 else 'down'

            if dx != 0:
                self.x += dx * self.speed * move_dir
                self._resolve_wall_collisions(walls, axis='x', delta=dx * move_dir)
            if dy != 0:
                self.y += dy * self.speed * move_dir
                self._resolve_wall_collisions(walls, axis='y', delta=dy * move_dir)

            self.x = max(0, min(self.x, SCREEN_WIDTH - self.width))
            self.y = max(0, min(self.y, SCREEN_HEIGHT - self.height))

        self.bob_timer += 0.1

        now = pygame.time.get_ticks()
        if dist <= RANGED_ENEMY_MAX_DISTANCE:
            if now - self._last_shot_ms >= RANGED_ENEMY_SHOOT_COOLDOWN_MS:
                self._last_shot_ms = now
                return True
        return False
