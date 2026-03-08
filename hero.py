"""
hero.py — Player-controlled hero with health, invincibility frames,
wall collision, melee attack, and movement in eight directions.
"""

import math

import pygame

from settings import (
    HERO_SIZE, HERO_SPEED, HERO_MAX_HP, HERO_HITBOX_SHRINK,
    HERO_INVINCIBILITY_MS, SCREEN_WIDTH, SCREEN_HEIGHT,
    ATTACK_DURATION_MS, ATTACK_COOLDOWN_MS, ATTACK_RANGE, ATTACK_ARC_DEG,
    COLOR_ATTACK_BLADE, COLOR_ATTACK_TRAIL, COLOR_ATTACK_GLOW,
    ULTIMATE_DURATION_MS, ULTIMATE_RANGE,
)

# Pre-computed facing → base angle (radians, 0 = right, counter-clockwise)
_FACING_ANGLE: dict[str, float] = {
    'right': 0.0,
    'up':    math.pi / 2,
    'left':  math.pi,
    'down':  -math.pi / 2,
}


class Hero:
    """The player-controlled hero character."""

    def __init__(self, x: float, y: float,
                 sprites: dict[str, pygame.Surface]) -> None:
        self.x = x
        self.y = y
        self.sprites = sprites
        self.facing: str = 'down'
        self.speed: float = HERO_SPEED
        self.width: int = HERO_SIZE
        self.height: int = HERO_SIZE
        self.hitbox_shrink: int = HERO_HITBOX_SHRINK

        # Health
        self.max_hp: int = HERO_MAX_HP
        self.hp: int = HERO_MAX_HP
        self.alive: bool = True

        # Invincibility after taking damage (milliseconds)
        self._invincible_until: int = 0  # pygame.time.get_ticks() value

        # Animation
        self.bob_timer: float = 0.0
        self.is_moving: bool = False

        # ── Attack state ─────────────────────────────────────────────
        self.attacking: bool = False
        self._attack_start: int = 0       # tick when current attack began
        self._attack_cooldown_until: int = 0  # earliest tick for next attack

        # ── Ultimate state ────────────────────────────────────────────
        self.ultimate_active: bool = False
        self._ultimate_start: int = 0

    # ── public helpers ───────────────────────────────────────────────────

    @property
    def center_x(self) -> float:
        return self.x + self.width / 2

    @property
    def center_y(self) -> float:
        return self.y + self.height / 2

    @property
    def is_invincible(self) -> bool:
        return pygame.time.get_ticks() < self._invincible_until

    @property
    def attack_progress(self) -> float:
        """0.0 → 1.0 progress through the current swing animation."""
        if not self.attacking:
            return 0.0
        elapsed = pygame.time.get_ticks() - self._attack_start
        return min(elapsed / ATTACK_DURATION_MS, 1.0)

    @property
    def ultimate_progress(self) -> float:
        """0.0 → 1.0 progress through the ultimate animation."""
        if not self.ultimate_active:
            return 0.0
        elapsed = pygame.time.get_ticks() - self._ultimate_start
        return min(elapsed / ULTIMATE_DURATION_MS, 1.0)

    def get_hitbox(self) -> pygame.Rect:
        s = self.hitbox_shrink
        return pygame.Rect(self.x + s, self.y + s,
                           self.width - 2 * s, self.height - 2 * s)

    # ── damage / healing ─────────────────────────────────────────────────

    def take_damage(self, amount: int) -> None:
        """Reduce HP (respects invincibility window).  Sets alive=False at 0."""
        if self.is_invincible or not self.alive:
            return
        self.hp = max(0, self.hp - amount)
        self._invincible_until = (pygame.time.get_ticks()
                                  + HERO_INVINCIBILITY_MS)
        if self.hp <= 0:
            self.alive = False

    def heal(self, amount: int) -> int:
        """Restore HP, capped at *max_hp*.  Returns actual HP gained."""
        if not self.alive:
            return 0
        before = self.hp
        self.hp = min(self.max_hp, self.hp + amount)
        return self.hp - before

    # ── melee attack ─────────────────────────────────────────────────────

    def start_attack(self) -> None:
        """Begin a sword swing if not on cooldown and alive."""
        if not self.alive:
            return
        now = pygame.time.get_ticks()
        if now < self._attack_cooldown_until:
            return
        self.attacking = True
        self._attack_start = now
        self._attack_cooldown_until = now + ATTACK_COOLDOWN_MS

    def start_ultimate(self) -> None:
        """Begin the ultimate sword animation."""
        if not self.alive:
            return
        self.ultimate_active = True
        self._ultimate_start = pygame.time.get_ticks()

    def get_attack_arc(self) -> tuple[float, float, float, float, float] | None:
        """Return the current swing arc geometry, or *None* if not attacking.

        Returns ``(cx, cy, radius, start_angle, end_angle)`` where angles
        are in **radians** (standard math convention: 0 = right, CCW positive).
        The arc sweeps from *start_angle* → *end_angle*.
        """
        if not self.attacking:
            return None

        half_arc = math.radians(ATTACK_ARC_DEG / 2)
        base = _FACING_ANGLE[self.facing]

        # The sword sweeps from one side of the facing direction to the other
        # Progress drives which part of the arc has been reached so far
        t = self.attack_progress
        start_angle = base - half_arc
        end_angle = base - half_arc + (2 * half_arc * t)

        return (self.center_x, self.center_y, ATTACK_RANGE,
                start_angle, end_angle)

    def is_point_in_attack(self, px: float, py: float) -> bool:
        """Return True if point (*px*, *py*) falls inside the active swing arc."""
        arc = self.get_attack_arc()
        if arc is None:
            return False

        cx, cy, radius, start_a, end_a = arc
        dx = px - cx
        dy = -(py - cy)  # flip y for standard math coords
        dist = math.hypot(dx, dy)
        if dist > radius:
            return False

        angle = math.atan2(dy, dx)

        # Normalise angles into [-π, π]
        def _norm(a: float) -> float:
            while a > math.pi:
                a -= 2 * math.pi
            while a < -math.pi:
                a += 2 * math.pi
            return a

        # Check if *angle* lies between start_a and end_a
        # (sweep is always start→end in the positive direction)
        span = _norm(end_a - start_a)
        if span < 0:
            span += 2 * math.pi
        diff = _norm(angle - start_a)
        if diff < 0:
            diff += 2 * math.pi
        return diff <= span

    # ── per-frame update ─────────────────────────────────────────────────

    def update(self, keys: pygame.key.ScancodeWrapper,
               walls: list[pygame.Rect]) -> None:
        if not self.alive:
            return

        # Expire attack animation
        if self.attacking:
            if pygame.time.get_ticks() - self._attack_start >= ATTACK_DURATION_MS:
                self.attacking = False

        # Expire ultimate animation
        if self.ultimate_active:
            if pygame.time.get_ticks() - self._ultimate_start >= ULTIMATE_DURATION_MS:
                self.ultimate_active = False

        dx, dy = 0.0, 0.0

        # WASD + Arrow keys
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy += 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx += 1

        # Normalise diagonal movement
        if dx != 0 and dy != 0:
            inv_sqrt2 = 1.0 / math.sqrt(2)
            dx *= inv_sqrt2
            dy *= inv_sqrt2

        self.is_moving = dx != 0 or dy != 0

        # Facing direction (only update when NOT mid-swing so the arc
        # stays consistent for the attack's duration)
        if not self.attacking:
            if dx < 0 and abs(dx) >= abs(dy):
                self.facing = 'left'
            elif dx > 0 and abs(dx) >= abs(dy):
                self.facing = 'right'
            elif dy < 0:
                self.facing = 'up'
            elif dy > 0:
                self.facing = 'down'

        # Axis-separated movement + wall collision (enables wall sliding)
        if dx != 0:
            self.x += dx * self.speed
            self._resolve_wall_collisions(walls, axis='x', delta=dx)
        if dy != 0:
            self.y += dy * self.speed
            self._resolve_wall_collisions(walls, axis='y', delta=dy)

        # Screen boundary clamping
        self.x = max(0, min(self.x, SCREEN_WIDTH - self.width))
        self.y = max(0, min(self.y, SCREEN_HEIGHT - self.height))

        # Bob animation timer
        if self.is_moving:
            self.bob_timer += 0.15
        else:
            self.bob_timer = 0.0

    # ── wall collision resolution ────────────────────────────────────────

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
        sprite = self.sprites[self.facing]

        # Flicker when invincible (skip every other frame pair)
        if self.is_invincible:
            tick = pygame.time.get_ticks()
            if (tick // 60) % 2 == 0:
                flash = sprite.copy()
                flash.set_alpha(100)
                sprite = flash

        bob_offset = 0
        if self.is_moving:
            bob_offset = int(math.sin(self.bob_timer) * 1.5)

        surface.blit(sprite, (int(self.x), int(self.y) + bob_offset))

        # Shadow
        shadow = pygame.Surface((self.width - 8, 6), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 60),
                            (0, 0, self.width - 8, 6))
        surface.blit(shadow,
                     (int(self.x) + 4,
                      int(self.y) + self.height - 2 + bob_offset))

        # Sword swing visual
        if self.attacking:
            self._draw_attack(surface)

        # Ultimate sword visual
        if self.ultimate_active:
            self._draw_ultimate(surface)

    def _draw_attack(self, surface: pygame.Surface) -> None:
        """Draw the animated sword swing arc."""
        arc = self.get_attack_arc()
        if arc is None:
            return

        cx, cy, radius, start_a, end_a = arc
        t = self.attack_progress
        icx, icy = int(cx), int(cy)

        # ── Glow flash (brief, at the start of the swing) ────────────
        if t < 0.3:
            glow_alpha = int(60 * (1.0 - t / 0.3))
            glow_r = int(radius * 0.7)
            glow_surf = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf,
                               (*COLOR_ATTACK_GLOW, glow_alpha),
                               (glow_r, glow_r), glow_r)
            surface.blit(glow_surf, (icx - glow_r, icy - glow_r),
                         special_flags=pygame.BLEND_RGBA_ADD)

        # ── Trail (filled arc wedge) ─────────────────────────────────
        # Build a polygon from the arc for the trail
        num_segments = 10
        span = end_a - start_a
        if abs(span) > 0.01:
            trail_alpha = int(100 * (1.0 - t * 0.5))
            trail_surf = pygame.Surface((radius * 2 + 4, radius * 2 + 4),
                                        pygame.SRCALPHA)
            local_cx = radius + 2
            local_cy = radius + 2
            points = [(local_cx, local_cy)]
            for i in range(num_segments + 1):
                a = start_a + span * (i / num_segments)
                px = local_cx + math.cos(a) * radius
                # screen y is inverted relative to math y
                py = local_cy - math.sin(a) * radius
                points.append((px, py))
            if len(points) >= 3:
                pygame.draw.polygon(trail_surf,
                                    (*COLOR_ATTACK_TRAIL, trail_alpha),
                                    points)
            surface.blit(trail_surf, (icx - local_cx, icy - local_cy))

        # ── Leading blade edge (bright line at the current tip) ──────
        blade_a = end_a
        bx = icx + math.cos(blade_a) * radius
        by = icy - math.sin(blade_a) * radius
        # Inner point (shorter)
        inner = radius * 0.35
        bx_in = icx + math.cos(blade_a) * inner
        by_in = icy - math.sin(blade_a) * inner
        blade_alpha = max(0, int(220 * (1.0 - t * 0.6)))
        blade_surf = pygame.Surface((surface.get_width(), surface.get_height()),
                                     pygame.SRCALPHA)
        pygame.draw.line(blade_surf,
                         (*COLOR_ATTACK_BLADE, blade_alpha),
                         (int(bx_in), int(by_in)),
                         (int(bx), int(by)), 3)
        # Small bright tip
        pygame.draw.circle(blade_surf,
                           (*COLOR_ATTACK_GLOW, blade_alpha),
                           (int(bx), int(by)), 3)
        surface.blit(blade_surf, (0, 0))

    def _draw_ultimate(self, surface: pygame.Surface) -> None:
        """Draw an expanded, dramatic sword arc for the ultimate."""
        t = self.ultimate_progress
        if t <= 0:
            return
        cx, cy = self.center_x, self.center_y
        icx, icy = int(cx), int(cy)
        base = _FACING_ANGLE[self.facing]
        half_arc = math.radians(170 / 2)
        start_a = base - half_arc
        end_a = base + half_arc
        radius = ULTIMATE_RANGE

        # Expanding glow ring
        glow_alpha = int(140 * (1.0 - t * 0.4))
        glow_r = int(radius * (0.6 + 0.4 * math.sin(t * math.pi)))
        glow_surf = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*COLOR_ATTACK_GLOW, glow_alpha),
                           (glow_r, glow_r), glow_r, 2)
        surface.blit(glow_surf, (icx - glow_r, icy - glow_r),
                     special_flags=pygame.BLEND_RGBA_ADD)

        # Wide arc trail
        num_segments = 18
        trail_alpha = int(120 * (1.0 - t * 0.3))
        trail_surf = pygame.Surface((radius * 2 + 6, radius * 2 + 6), pygame.SRCALPHA)
        local_cx = radius + 3
        local_cy = radius + 3
        points = [(local_cx, local_cy)]
        for i in range(num_segments + 1):
            a = start_a + (end_a - start_a) * (i / num_segments)
            px = local_cx + math.cos(a) * radius
            py = local_cy - math.sin(a) * radius
            points.append((px, py))
        if len(points) >= 3:
            pygame.draw.polygon(trail_surf,
                                (*COLOR_ATTACK_TRAIL, trail_alpha),
                                points)
        surface.blit(trail_surf, (icx - local_cx, icy - local_cy))

        # Bright leading edge
        blade_surf = pygame.Surface((surface.get_width(), surface.get_height()),
                                     pygame.SRCALPHA)
        blade_a = end_a
        bx = icx + math.cos(blade_a) * radius
        by = icy - math.sin(blade_a) * radius
        inner = radius * 0.4
        bx_in = icx + math.cos(blade_a) * inner
        by_in = icy - math.sin(blade_a) * inner
        blade_alpha = max(0, int(220 * (1.0 - t * 0.3)))
        pygame.draw.line(blade_surf,
                         (*COLOR_ATTACK_BLADE, blade_alpha),
                         (int(bx_in), int(by_in)),
                         (int(bx), int(by)), 4)
        pygame.draw.circle(blade_surf,
                           (*COLOR_ATTACK_GLOW, blade_alpha),
                           (int(bx), int(by)), 4)
        surface.blit(blade_surf, (0, 0))
