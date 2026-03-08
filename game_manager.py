"""
game_manager.py — Central orchestrator for the Dungeon Crawler.

Owns the hero, enemy list, dungeon, and HUD.  Handles the spawn timer,
attack input, attack-vs-enemy collision, enemy–hero damage, kill-based
score tracking, game-over state, and restart.
"""

import math
import random

import pygame

from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    HERO_SIZE, ENEMY_SIZE, ENEMY_DAMAGE,
    SPAWN_INTERVAL_MIN, SPAWN_INTERVAL_MAX,
    SPAWN_PER_WAVE_MIN, SPAWN_PER_WAVE_MAX,
    MAX_ENEMIES, FPS, SCORE_PER_KILL,
    ORB_DROP_CHANCE, ORB_HEAL_AMOUNT,
    FIREBALL_SPEED, FIREBALL_RADIUS, FIREBALL_COOLDOWN_MS, FIREBALL_DAMAGE,
    COLOR_FIREBALL_CORE, COLOR_FIREBALL_GLOW, COLOR_FIREBALL_HALO,
    RANGED_ENEMY_SPAWN_CHANCE, ENEMY_PROJECTILE_SPEED,
    ENEMY_PROJECTILE_RADIUS, ENEMY_PROJECTILE_DAMAGE,
    COLOR_ENEMY_PROJECTILE_CORE, COLOR_ENEMY_PROJECTILE_GLOW,
    COLOR_ENEMY_PROJECTILE_HALO,
    ULTIMATE_REQUIRED_MELEE_SWORD_KILLS,
    ULTIMATE_COOLDOWN_AFTER_USE_MS,
    ULTIMATE_DURATION_MS,
    ULTIMATE_RANGE,
)
from sprites import create_hero_sprites, create_enemy_sprites, create_ranged_enemy_sprites
from hero import Hero
from enemy import Enemy, RangedEnemy
from dungeon import Dungeon
from hud import HUD
from health_orb import HealthOrb, OrbCollectVFX


class Fireball:
    """Simple ranged projectile fired toward the cursor."""

    def __init__(self, x: float, y: float, dx: float, dy: float) -> None:
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.alive: bool = True

    def get_hitbox(self) -> pygame.Rect:
        r = FIREBALL_RADIUS
        return pygame.Rect(self.x - r, self.y - r, r * 2, r * 2)

    def update(self, walls: list[pygame.Rect]) -> None:
        if not self.alive:
            return
        self.x += self.dx * FIREBALL_SPEED
        self.y += self.dy * FIREBALL_SPEED

        if (self.x < -FIREBALL_RADIUS or self.x > SCREEN_WIDTH + FIREBALL_RADIUS
                or self.y < -FIREBALL_RADIUS or self.y > SCREEN_HEIGHT + FIREBALL_RADIUS):
            self.alive = False
            return

        hitbox = self.get_hitbox()
        for wall in walls:
            if hitbox.colliderect(wall):
                self.alive = False
                break

    def draw(self, surface: pygame.Surface) -> None:
        if not self.alive:
            return
        cx, cy = int(self.x), int(self.y)
        flicker = 0.7 + 0.3 * math.sin(pygame.time.get_ticks() * 0.02)
        glow_r = int(FIREBALL_RADIUS * 3.2 * flicker)
        glow_surf = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
        for r in range(glow_r, 0, -2):
            alpha = int(55 * (r / glow_r))
            pygame.draw.circle(glow_surf, (*COLOR_FIREBALL_GLOW, alpha),
                               (glow_r, glow_r), r)
        surface.blit(glow_surf, (cx - glow_r, cy - glow_r),
                     special_flags=pygame.BLEND_RGBA_ADD)

        # Flame body (teardrop shape)
        flame_h = FIREBALL_RADIUS * 3
        flame_w = FIREBALL_RADIUS * 2
        flame_surf = pygame.Surface((flame_w * 2, flame_h * 2), pygame.SRCALPHA)
        fx = flame_w
        fy = flame_h
        pygame.draw.polygon(flame_surf, COLOR_FIREBALL_CORE,
                            [(fx, fy - flame_h),
                             (fx - flame_w, fy + flame_h * 0.4),
                             (fx + flame_w, fy + flame_h * 0.4)])
        pygame.draw.circle(flame_surf, COLOR_FIREBALL_CORE,
                           (fx, int(fy + flame_h * 0.2)), flame_w)
        pygame.draw.polygon(flame_surf, COLOR_FIREBALL_HALO,
                            [(fx, fy - flame_h * 0.6),
                             (fx - flame_w * 0.6, fy + flame_h * 0.2),
                             (fx + flame_w * 0.6, fy + flame_h * 0.2)])
        pygame.draw.circle(flame_surf, COLOR_FIREBALL_HALO,
                           (fx, int(fy + flame_h * 0.1)), max(2, flame_w - 2))
        surface.blit(flame_surf, (cx - flame_w, cy - flame_h))


class EnemyProjectile:
    """Projectile fired by ranged enemies."""

    def __init__(self, x: float, y: float, dx: float, dy: float) -> None:
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.alive: bool = True

    def get_hitbox(self) -> pygame.Rect:
        r = ENEMY_PROJECTILE_RADIUS
        return pygame.Rect(self.x - r, self.y - r, r * 2, r * 2)

    def update(self, walls: list[pygame.Rect]) -> None:
        if not self.alive:
            return
        self.x += self.dx * ENEMY_PROJECTILE_SPEED
        self.y += self.dy * ENEMY_PROJECTILE_SPEED

        if (self.x < -ENEMY_PROJECTILE_RADIUS
                or self.x > SCREEN_WIDTH + ENEMY_PROJECTILE_RADIUS
                or self.y < -ENEMY_PROJECTILE_RADIUS
                or self.y > SCREEN_HEIGHT + ENEMY_PROJECTILE_RADIUS):
            self.alive = False
            return

        hitbox = self.get_hitbox()
        for wall in walls:
            if hitbox.colliderect(wall):
                self.alive = False
                break

    def draw(self, surface: pygame.Surface) -> None:
        if not self.alive:
            return
        cx, cy = int(self.x), int(self.y)
        glow_r = ENEMY_PROJECTILE_RADIUS * 3
        glow_surf = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
        for r in range(glow_r, 0, -2):
            alpha = int(70 * (r / glow_r))
            pygame.draw.circle(glow_surf, (*COLOR_ENEMY_PROJECTILE_GLOW, alpha),
                               (glow_r, glow_r), r)
        surface.blit(glow_surf, (cx - glow_r, cy - glow_r),
                     special_flags=pygame.BLEND_RGBA_ADD)

        pygame.draw.circle(surface, COLOR_ENEMY_PROJECTILE_CORE,
                           (cx, cy), ENEMY_PROJECTILE_RADIUS)
        pygame.draw.circle(surface, COLOR_ENEMY_PROJECTILE_HALO,
                           (cx, cy), max(2, ENEMY_PROJECTILE_RADIUS - 2))


class GameManager:
    """Top-level game-state manager.

    Call :meth:`handle_event`, :meth:`update`, and :meth:`draw` once per
    frame from the main loop.
    """

    STATE_MENU = 'MENU'
    STATE_PLAYING = 'PLAYING'
    STATE_GAMEOVER = 'GAMEOVER'

    def __init__(self) -> None:
        # Shared sprite sheets (generated once, reused by all instances)
        self._hero_sprites = create_hero_sprites()
        self._enemy_sprites = create_enemy_sprites()
        self._ranged_enemy_sprites = create_ranged_enemy_sprites()

        # Sub-systems
        self.dungeon = Dungeon()
        self.hud = HUD()

        # Spawn-point pool (floor tiles near the map edges)
        self._spawn_points = self.dungeon.get_edge_floor_tiles()

        # Menu buttons
        self._menu_buttons = [
            pygame.Rect(SCREEN_WIDTH // 2 - 140, 320, 280, 48),
            pygame.Rect(SCREEN_WIDTH // 2 - 140, 380, 280, 48),
        ]
        self._menu_hovered: int | None = None

        # Mutable game state — initialised via reset()
        self.hero: Hero = None  # type: ignore[assignment]
        self.enemies: list[Enemy] = []
        self.health_orbs: list[HealthOrb] = []
        self.collect_vfx: list[OrbCollectVFX] = []
        self.fireballs: list[Fireball] = []
        self.enemy_projectiles: list[EnemyProjectile] = []
        self._last_fireball_ms: int = 0
        self.score: int = 0
        self.melee_kills: int = 0
        self.ranged_kills: int = 0
        self.sword_kills: int = 0
        self.fireball_kills: int = 0
        self.melee_sword_kills_since_ultimate: int = 0
        self.ultimate_ready: bool = False
        self.ultimate_active: bool = False
        self._ultimate_start_ms: int = 0
        self._ultimate_blocked_until: int = 0
        self._spawn_timer: float = 0.0
        self._next_spawn: float = 0.0
        # Track which enemies have already been hit by the *current* swing
        # so a single swing can't score the same enemy twice.
        self._attack_hit_ids: set[int] = set()
        self.running: bool = True
        self.state: str = self.STATE_MENU

        self.reset()

    # ── reset / restart ──────────────────────────────────────────────────

    def reset(self) -> None:
        """(Re)initialise all mutable game state."""
        self.hero = Hero(
            SCREEN_WIDTH / 2 - HERO_SIZE / 2,
            SCREEN_HEIGHT / 2 - HERO_SIZE / 2,
            self._hero_sprites,
        )
        self.enemies.clear()
        self.health_orbs.clear()
        self.collect_vfx.clear()
        self.fireballs.clear()
        self.enemy_projectiles.clear()
        self._last_fireball_ms = 0
        self.score = 0
        self.melee_kills = 0
        self.ranged_kills = 0
        self.sword_kills = 0
        self.fireball_kills = 0
        self.melee_sword_kills_since_ultimate = 0
        self.ultimate_ready = False
        self.ultimate_active = False
        self._ultimate_start_ms = 0
        self._ultimate_blocked_until = 0
        self.hero.ultimate_active = False
        self._spawn_timer = 0.0
        self._next_spawn = self._random_spawn_interval()
        self._attack_hit_ids.clear()
        self._menu_hovered = None

    # ── event handling ───────────────────────────────────────────────────

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Process a single pygame event.

        Returns ``False`` when the game should quit.
        """
        if event.type == pygame.QUIT:
            return False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return False
            if event.key == pygame.K_RETURN:
                if self.state == self.STATE_MENU:
                    self._start_game()
                elif self.state == self.STATE_GAMEOVER:
                    self.state = self.STATE_MENU
            # Attack — spacebar
            if event.key == pygame.K_SPACE and self.state == self.STATE_PLAYING:
                self._try_attack()
            # Ultimate — E key
            if event.key == pygame.K_e and self.state == self.STATE_PLAYING:
                self._try_ultimate()

        if event.type == pygame.MOUSEMOTION:
            if self.state == self.STATE_MENU:
                self._update_menu_hover(event.pos)

        # Fireball — left mouse button or menu selection
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.state == self.STATE_PLAYING:
                self._try_fireball(event.pos)
            elif self.state == self.STATE_MENU:
                if self._menu_buttons[0].collidepoint(event.pos):
                    self._start_game()
                elif self._menu_buttons[1].collidepoint(event.pos):
                    return False

        return True

    # ── per-frame update ─────────────────────────────────────────────────

    def update(self, keys: pygame.key.ScancodeWrapper) -> None:
        # Dungeon ambient (torches)
        self.dungeon.update()

        if self.state != self.STATE_PLAYING:
            return

        if not self.hero.alive:
            self.state = self.STATE_GAMEOVER
            return

        # Hero movement
        self.hero.update(keys, self.dungeon.wall_rects)

        # Enemy spawning
        self._spawn_timer += 1.0 / FPS
        if self._spawn_timer >= self._next_spawn:
            self._spawn_wave()
            self._spawn_timer = 0.0
            self._next_spawn = self._random_spawn_interval()

        # Enemy updates (track hero)
        hero_cx = self.hero.center_x
        hero_cy = self.hero.center_y
        for enemy in self.enemies:
            if isinstance(enemy, RangedEnemy):
                if enemy.update(hero_cx, hero_cy, self.dungeon.wall_rects):
                    self._spawn_enemy_projectile(enemy, hero_cx, hero_cy)
            else:
                enemy.update(hero_cx, hero_cy, self.dungeon.wall_rects)

        # Fireball updates + collisions
        for fireball in self.fireballs:
            fireball.update(self.dungeon.wall_rects)
        self._check_fireball_vs_enemies()
        self.fireballs = [f for f in self.fireballs if f.alive]

        # Enemy projectile updates + collisions
        for projectile in self.enemy_projectiles:
            projectile.update(self.dungeon.wall_rects)
        self._check_enemy_projectile_collisions()
        self.enemy_projectiles = [p for p in self.enemy_projectiles if p.alive]

        # Attack-vs-enemy collision (while swing is active)
        if self.hero.attacking:
            self._check_attack_vs_enemies()
        else:
            # Swing ended — clear the per-swing hit set
            self._attack_hit_ids.clear()

        # Ultimate window handling
        self._update_ultimate_state()

        # Collision: enemy → hero (damage)
        self._check_enemy_hero_collisions()

        # Prune dead enemies — spawn health orbs from freshly killed ones
        for enemy in self.enemies:
            if not enemy.alive:
                self._maybe_spawn_orb(enemy.center_x, enemy.center_y)
        self.enemies = [e for e in self.enemies if e.alive]

        # Health-orb updates + hero pickup
        hero_cx = self.hero.center_x
        hero_cy = self.hero.center_y
        for orb in self.health_orbs:
            orb.update()
            if orb.alive and orb.hero_can_collect(hero_cx, hero_cy):
                healed = self.hero.heal(orb.heal_amount)
                self.collect_vfx.append(
                    OrbCollectVFX(orb.x, orb.y,
                                  orb.heal_amount if healed > 0 else 0))
                orb.alive = False
        self.health_orbs = [o for o in self.health_orbs if o.alive]

        # Collection VFX updates
        for vfx in self.collect_vfx:
            vfx.update()
        self.collect_vfx = [v for v in self.collect_vfx if v.alive]

    # ── drawing ──────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface) -> None:
        # 1. Static dungeon background
        self.dungeon.draw_background(surface)

        # 2. Torch glow
        self.dungeon.draw_torches(surface)

        # 3. Health orbs (on the floor, beneath characters)
        for orb in self.health_orbs:
            orb.draw(surface)

        # 4. Enemies (drawn before hero so hero appears on top)
        for enemy in self.enemies:
            enemy.draw(surface)

        # 5. Enemy projectiles (above enemies)
        for projectile in self.enemy_projectiles:
            projectile.draw(surface)

        # 6. Fireballs (above enemies, below hero)
        for fireball in self.fireballs:
            fireball.draw(surface)

        # 7. Hero (includes attack swing visual)
        self.hero.draw(surface)

        # 8. Collection VFX (above characters)
        for vfx in self.collect_vfx:
            vfx.draw(surface)

        # 9. Atmospheric vignette
        self.dungeon.draw_vignette(surface)

        # 8. HUD + menus (always on top)
        self.hud.draw(surface, self.hero.hp, self.score,
                      len(self.enemies), self.melee_kills,
                      self.ranged_kills, self.sword_kills,
                      self.fireball_kills, self.hero.alive, self.state,
                      self._fireball_cooldown_remaining(), self.ultimate_ready,
                      self.ultimate_active)

        if self.state == self.STATE_MENU:
            self.hud.draw_menu(surface, self._menu_buttons, self._menu_hovered)

    # ── private helpers ──────────────────────────────────────────────────

    def _try_attack(self) -> None:
        """Initiate an attack if the hero is alive and not on cooldown."""
        if self.hero.alive and not self.hero.attacking:
            self.hero.start_attack()
            self._attack_hit_ids.clear()

    def _try_ultimate(self) -> None:
        """Trigger the ultimate skill if it is ready and off cooldown."""
        if not self.hero.alive or self.ultimate_active:
            return
        now = pygame.time.get_ticks()
        if not self.ultimate_ready or now < self._ultimate_blocked_until:
            return
        self.ultimate_active = True
        self.ultimate_ready = False
        self._ultimate_start_ms = now
        self._ultimate_blocked_until = now + ULTIMATE_COOLDOWN_AFTER_USE_MS
        self.melee_sword_kills_since_ultimate = 0
        self.hero.start_ultimate()
        self._apply_ultimate_damage()

    def _try_fireball(self, target: tuple[int, int]) -> None:
        """Fire a ranged projectile toward *target* if off cooldown."""
        if not self.hero.alive:
            return
        now = pygame.time.get_ticks()
        if now - self._last_fireball_ms < FIREBALL_COOLDOWN_MS:
            return

        dx = target[0] - self.hero.center_x
        dy = target[1] - self.hero.center_y
        dist = math.hypot(dx, dy)
        if dist < 1.0:
            return

        dx /= dist
        dy /= dist
        self.fireballs.append(Fireball(self.hero.center_x, self.hero.center_y,
                                       dx, dy))
        self._last_fireball_ms = now

    def _start_game(self) -> None:
        """Transition from menu to active play, resetting state."""
        self.reset()
        self.state = self.STATE_PLAYING

    def _update_menu_hover(self, pos: tuple[int, int]) -> None:
        hovered = None
        for idx, rect in enumerate(self._menu_buttons):
            if rect.collidepoint(pos):
                hovered = idx
                break
        self._menu_hovered = hovered

    def _fireball_cooldown_remaining(self) -> float:
        """Return remaining fireball cooldown in seconds."""
        now = pygame.time.get_ticks()
        remaining_ms = FIREBALL_COOLDOWN_MS - (now - self._last_fireball_ms)
        return max(0.0, remaining_ms / 1000.0)

    @staticmethod
    def _random_spawn_interval() -> float:
        return random.uniform(SPAWN_INTERVAL_MIN, SPAWN_INTERVAL_MAX)

    def _spawn_wave(self) -> None:
        """Spawn a small wave of enemies from random edge floor tiles."""
        if not self._spawn_points:
            return

        count = random.randint(SPAWN_PER_WAVE_MIN, SPAWN_PER_WAVE_MAX)
        for _ in range(count):
            if len(self.enemies) >= MAX_ENEMIES:
                break
            px, py = random.choice(self._spawn_points)
            ex = px - ENEMY_SIZE / 2
            ey = py - ENEMY_SIZE / 2
            ranged_alive = sum(isinstance(e, RangedEnemy) for e in self.enemies)
            can_spawn_ranged = ranged_alive < 2
            if can_spawn_ranged and random.random() < RANGED_ENEMY_SPAWN_CHANCE:
                self.enemies.append(RangedEnemy(ex, ey, self._ranged_enemy_sprites))
            else:
                self.enemies.append(Enemy(ex, ey, self._enemy_sprites))

    def _maybe_spawn_orb(self, x: float, y: float) -> None:
        """Roll the dice and maybe drop a health orb at (*x*, *y*)."""
        if random.random() < ORB_DROP_CHANCE:
            self.health_orbs.append(HealthOrb(x, y))

    def _check_attack_vs_enemies(self) -> None:
        """Kill enemies whose centre falls inside the hero's sword arc."""
        for enemy in self.enemies:
            if not enemy.alive:
                continue
            eid = id(enemy)
            if eid in self._attack_hit_ids:
                continue  # already hit by this swing
            if self.hero.is_point_in_attack(enemy.center_x, enemy.center_y):
                enemy.alive = False
                self._attack_hit_ids.add(eid)
                self.score += SCORE_PER_KILL
                self.sword_kills += 1
                if isinstance(enemy, RangedEnemy):
                    self.ranged_kills += 1
                else:
                    self.melee_kills += 1
                    self._register_melee_sword_kill()

    def _check_fireball_vs_enemies(self) -> None:
        """Destroy enemies hit by fireballs and despawn the projectile."""
        for fireball in self.fireballs:
            if not fireball.alive:
                continue
            fb_hitbox = fireball.get_hitbox()
            for enemy in self.enemies:
                if not enemy.alive:
                    continue
                if fb_hitbox.colliderect(enemy.get_hitbox()):
                    enemy.alive = False
                    fireball.alive = False
                    self.score += SCORE_PER_KILL
                    self.fireball_kills += 1
                    if isinstance(enemy, RangedEnemy):
                        self.ranged_kills += 1
                    else:
                        self.melee_kills += 1
                    break

    def _spawn_enemy_projectile(self, enemy: RangedEnemy,
                                target_x: float, target_y: float) -> None:
        dx = target_x - enemy.center_x
        dy = target_y - enemy.center_y
        dist = math.hypot(dx, dy)
        if dist < 1.0:
            return
        dx /= dist
        dy /= dist
        self.enemy_projectiles.append(
            EnemyProjectile(enemy.center_x, enemy.center_y, dx, dy)
        )

    def _check_enemy_hero_collisions(self) -> None:
        """Damage the hero when an enemy overlaps its hitbox."""
        hero_hb = self.hero.get_hitbox()
        for enemy in self.enemies:
            if not enemy.alive:
                continue
            if hero_hb.colliderect(enemy.get_hitbox()):
                self.hero.take_damage(ENEMY_DAMAGE)
                if self.hero.is_invincible:
                    break

    def _check_enemy_projectile_collisions(self) -> None:
        """Damage the hero when a projectile hits."""
        hero_hb = self.hero.get_hitbox()
        for projectile in self.enemy_projectiles:
            if not projectile.alive:
                continue
            if hero_hb.colliderect(projectile.get_hitbox()):
                self.hero.take_damage(ENEMY_PROJECTILE_DAMAGE)
                projectile.alive = False
                if self.hero.is_invincible:
                    break

    def _update_ultimate_state(self) -> None:
        if not self.ultimate_active:
            return
        now = pygame.time.get_ticks()
        if now - self._ultimate_start_ms >= ULTIMATE_DURATION_MS:
            self.ultimate_active = False
            self.hero.ultimate_active = False

    def _apply_ultimate_damage(self) -> None:
        hero_cx = self.hero.center_x
        hero_cy = self.hero.center_y
        for enemy in self.enemies:
            if not enemy.alive:
                continue
            dx = enemy.center_x - hero_cx
            dy = enemy.center_y - hero_cy
            if math.hypot(dx, dy) <= ULTIMATE_RANGE:
                enemy.alive = False
                self.score += SCORE_PER_KILL
                if isinstance(enemy, RangedEnemy):
                    self.ranged_kills += 1
                else:
                    self.melee_kills += 1

    def _register_melee_sword_kill(self) -> None:
        now = pygame.time.get_ticks()
        if now < self._ultimate_blocked_until:
            return
        self.melee_sword_kills_since_ultimate += 1
        if self.melee_sword_kills_since_ultimate >= ULTIMATE_REQUIRED_MELEE_SWORD_KILLS:
            self.ultimate_ready = True
