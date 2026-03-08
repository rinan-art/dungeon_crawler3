"""
health_orb.py — Collectible health orb dropped by defeated enemies,
plus a short-lived visual effect when the hero picks one up.
"""

import math

import pygame

from settings import (
    ORB_RADIUS, ORB_COLLECT_RADIUS, ORB_LIFETIME_MS,
    ORB_BOB_SPEED, ORB_BOB_AMP, ORB_PULSE_SPEED,
    ORB_COLLECT_VFX_MS, ORB_HEAL_AMOUNT,
    COLOR_ORB_CORE, COLOR_ORB_BRIGHT, COLOR_ORB_GLOW,
    COLOR_ORB_COLLECT_FLASH, COLOR_ORB_HEAL_TEXT,
)


class HealthOrb:
    """A glowing green orb that bobs in place and heals the hero on contact."""

    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y
        self.alive: bool = True
        self.heal_amount: int = ORB_HEAL_AMOUNT

        self._spawn_tick: int = pygame.time.get_ticks()
        self._bob_timer: float = 0.0
        self._pulse_timer: float = 0.0

    # ── queries ────────────────────────────────────────────────────────────

    @property
    def expired(self) -> bool:
        """True when the orb has been on the ground too long."""
        return pygame.time.get_ticks() - self._spawn_tick >= ORB_LIFETIME_MS

    def distance_to(self, px: float, py: float) -> float:
        return math.hypot(px - self.x, py - self.y)

    def hero_can_collect(self, hero_cx: float, hero_cy: float) -> bool:
        """True if the hero centre is close enough to pick this orb up."""
        return self.alive and self.distance_to(hero_cx, hero_cy) <= ORB_COLLECT_RADIUS

    # ── per-frame ──────────────────────────────────────────────────────────

    def update(self) -> None:
        if not self.alive:
            return
        self._bob_timer += ORB_BOB_SPEED
        self._pulse_timer += ORB_PULSE_SPEED

        # Auto-expire
        if self.expired:
            self.alive = False

    # ── drawing ────────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface) -> None:
        if not self.alive:
            return

        bob_y = math.sin(self._bob_timer) * ORB_BOB_AMP
        cx = int(self.x)
        cy = int(self.y + bob_y)

        # Fade out during the last 1.5 seconds of lifetime
        age = pygame.time.get_ticks() - self._spawn_tick
        remaining = ORB_LIFETIME_MS - age
        master_alpha = 255 if remaining > 1500 else max(0, int(255 * remaining / 1500))

        # Pulsing glow radius
        pulse = 0.5 + 0.5 * math.sin(self._pulse_timer)  # 0..1
        glow_r = int(ORB_RADIUS * 2.5 + pulse * ORB_RADIUS)

        # Outer glow (additive)
        glow_surf = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
        glow_alpha = int((30 + 20 * pulse) * (master_alpha / 255))
        for r in range(glow_r, 0, -3):
            a = int(glow_alpha * (r / glow_r))
            pygame.draw.circle(glow_surf, (*COLOR_ORB_GLOW, a),
                               (glow_r, glow_r), r)
        surface.blit(glow_surf, (cx - glow_r, cy - glow_r),
                     special_flags=pygame.BLEND_RGBA_ADD)

        # Core orb
        core_alpha = master_alpha
        core_surf = pygame.Surface((ORB_RADIUS * 2 + 2, ORB_RADIUS * 2 + 2),
                                   pygame.SRCALPHA)
        local_c = ORB_RADIUS + 1
        pygame.draw.circle(core_surf, (*COLOR_ORB_CORE, core_alpha),
                           (local_c, local_c), ORB_RADIUS)
        # Bright highlight (upper-left)
        highlight_r = max(2, ORB_RADIUS // 2)
        pygame.draw.circle(core_surf, (*COLOR_ORB_BRIGHT, int(core_alpha * 0.8)),
                           (local_c - 2, local_c - 2), highlight_r)
        # Tiny specular dot
        pygame.draw.circle(core_surf, (255, 255, 255, int(core_alpha * 0.9)),
                           (local_c - 3, local_c - 3), 2)
        surface.blit(core_surf, (cx - local_c, cy - local_c))

        # Small shadow on the ground (below the bobbing orb)
        shadow_surf = pygame.Surface((ORB_RADIUS * 2, 4), pygame.SRCALPHA)
        shadow_alpha = int(40 * (master_alpha / 255))
        pygame.draw.ellipse(shadow_surf, (0, 0, 0, shadow_alpha),
                            (0, 0, ORB_RADIUS * 2, 4))
        surface.blit(shadow_surf, (cx - ORB_RADIUS, int(self.y) + ORB_RADIUS + 2))


# ---------------------------------------------------------------------------
# Collection VFX  — a brief expanding ring + floating "+HP" text
# ---------------------------------------------------------------------------

class OrbCollectVFX:
    """Short-lived visual feedback when a health orb is collected."""

    def __init__(self, x: float, y: float, heal_amount: int) -> None:
        self.x = x
        self.y = y
        self.heal_amount = heal_amount
        self._start_tick: int = pygame.time.get_ticks()
        self.alive: bool = True
        self._font = pygame.font.SysFont('monospace', 14, bold=True)

    @property
    def _progress(self) -> float:
        """0.0 → 1.0 over the effect duration."""
        elapsed = pygame.time.get_ticks() - self._start_tick
        return min(elapsed / ORB_COLLECT_VFX_MS, 1.0)

    def update(self) -> None:
        if self._progress >= 1.0:
            self.alive = False

    def draw(self, surface: pygame.Surface) -> None:
        if not self.alive:
            return

        t = self._progress
        alpha = max(0, int(255 * (1.0 - t)))
        cx, cy = int(self.x), int(self.y)

        # Expanding ring
        ring_r = int(10 + 26 * t)
        ring_surf = pygame.Surface((ring_r * 2 + 4, ring_r * 2 + 4),
                                   pygame.SRCALPHA)
        rc = ring_r + 2
        ring_width = max(1, int(3 * (1.0 - t)))
        pygame.draw.circle(ring_surf,
                           (*COLOR_ORB_COLLECT_FLASH, alpha),
                           (rc, rc), ring_r, ring_width)
        surface.blit(ring_surf, (cx - rc, cy - rc))

        # Flash burst (very brief, first 30 % of duration)
        if t < 0.3:
            burst_alpha = int(120 * (1.0 - t / 0.3))
            burst_r = int(8 + 14 * (t / 0.3))
            burst_surf = pygame.Surface((burst_r * 2, burst_r * 2),
                                        pygame.SRCALPHA)
            pygame.draw.circle(burst_surf,
                               (*COLOR_ORB_COLLECT_FLASH, burst_alpha),
                               (burst_r, burst_r), burst_r)
            surface.blit(burst_surf, (cx - burst_r, cy - burst_r),
                         special_flags=pygame.BLEND_RGBA_ADD)

        # Floating "+HP" text rising upward
        text_y = cy - int(18 * t) - 12
        label = self._font.render(f"+{self.heal_amount} HP", True,
                                  (*COLOR_ORB_HEAL_TEXT,))
        # Apply alpha via a temporary surface
        text_surf = pygame.Surface(label.get_size(), pygame.SRCALPHA)
        text_surf.blit(label, (0, 0))
        text_surf.set_alpha(alpha)
        tw = text_surf.get_width()
        surface.blit(text_surf, (cx - tw // 2, text_y))
