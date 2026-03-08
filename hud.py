"""
hud.py — Heads-Up Display: health bar, score, enemy count, and
game-over / controls overlay.
"""

import pygame

from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, HERO_MAX_HP,
    COLOR_BLACK, COLOR_WHITE,
    COLOR_HUD_HP_BG, COLOR_HUD_HP_FILL, COLOR_HUD_HP_FILL_LOW,
    COLOR_HUD_HP_BORDER, COLOR_HUD_TEXT, COLOR_HUD_TEXT_DIM,
    COLOR_MENU_TITLE, COLOR_MENU_TEXT, COLOR_MENU_TEXT_DIM,
    COLOR_MENU_BUTTON_BG, COLOR_MENU_BUTTON_BG_HOVER,
    COLOR_MENU_BUTTON_BORDER, COLOR_MENU_BUTTON_TEXT,
)


class HUD:
    """Draws all on-screen UI elements."""

    # Health bar geometry
    HP_BAR_X = 16
    HP_BAR_Y = 16
    HP_BAR_W = 200
    HP_BAR_H = 18

    def __init__(self) -> None:
        self._font = pygame.font.SysFont('monospace', 14, bold=True)
        self._font_big = pygame.font.SysFont('monospace', 40, bold=True)
        self._font_med = pygame.font.SysFont('monospace', 18, bold=True)
        self._font_title = pygame.font.SysFont('cinzel', 64, bold=True)
        self._font_menu = pygame.font.SysFont('cinzel', 22, bold=True)
        self._font_menu_small = pygame.font.SysFont('monospace', 16, bold=True)

    # ── drawing ──────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface, hp: int, score: int,
             enemy_count: int, melee_kills: int, ranged_kills: int,
             sword_kills: int, fireball_kills: int, alive: bool,
             state: str, fireball_cooldown: float,
             ultimate_ready: bool, ultimate_active: bool) -> None:
        """Draw the full HUD layer."""
        if state == 'PLAYING':
            self._draw_health_bar(surface, hp)
            self._draw_stats(surface, score, enemy_count,
                             melee_kills, ranged_kills,
                             sword_kills, fireball_kills)
            self._draw_controls(surface)
            self._draw_fireball_cooldown(surface, fireball_cooldown)
            self._draw_ultimate_status(surface, ultimate_ready, ultimate_active)
        elif state == 'GAMEOVER':
            self._draw_game_over(surface, score, melee_kills, ranged_kills,
                                 sword_kills, fireball_kills)

    # ── health bar ───────────────────────────────────────────────────────

    def _draw_health_bar(self, surface: pygame.Surface, hp: int) -> None:
        x, y = self.HP_BAR_X, self.HP_BAR_Y
        w, h = self.HP_BAR_W, self.HP_BAR_H

        # Background
        pygame.draw.rect(surface, COLOR_HUD_HP_BG, (x, y, w, h))

        # Fill (colour shifts when low)
        ratio = max(0, hp / HERO_MAX_HP)
        fill_w = int(w * ratio)
        fill_colour = COLOR_HUD_HP_FILL if ratio > 0.3 else COLOR_HUD_HP_FILL_LOW
        if fill_w > 0:
            pygame.draw.rect(surface, fill_colour, (x, y, fill_w, h))

        # Border
        pygame.draw.rect(surface, COLOR_HUD_HP_BORDER, (x, y, w, h), 2)

        # Label
        label = self._font.render(f"HP  {hp}/{HERO_MAX_HP}", True, COLOR_HUD_TEXT)
        surface.blit(label, (x + w + 10, y + 1))

    # ── stats (score + enemies) ──────────────────────────────────────────

    def _draw_stats(self, surface: pygame.Surface, score: int,
                    enemy_count: int, melee_kills: int,
                    ranged_kills: int, sword_kills: int,
                    fireball_kills: int) -> None:
        score_txt = self._font.render(f"Score: {score}", True, COLOR_HUD_TEXT)
        enemy_txt = self._font.render(f"Enemies: {enemy_count}", True,
                                      COLOR_HUD_TEXT)
        melee_txt = self._font.render(f"Melee Enemies Killed: {melee_kills}", True,
                                      COLOR_HUD_TEXT)
        ranged_txt = self._font.render(f"Ranged Enemies Killed: {ranged_kills}", True,
                                       COLOR_HUD_TEXT)
        sword_txt = self._font.render(f"Sword Kills: {sword_kills}", True,
                                      COLOR_HUD_TEXT)
        fireball_txt = self._font.render(f"Fireball Kills: {fireball_kills}", True,
                                         COLOR_HUD_TEXT)
        surface.blit(score_txt, (SCREEN_WIDTH - 260, 16))
        surface.blit(enemy_txt, (SCREEN_WIDTH - 260, 34))
        surface.blit(melee_txt, (SCREEN_WIDTH - 260, 52))
        surface.blit(ranged_txt, (SCREEN_WIDTH - 260, 70))
        surface.blit(sword_txt, (SCREEN_WIDTH - 260, 88))
        surface.blit(fireball_txt, (SCREEN_WIDTH - 260, 106))

    # ── controls hint ────────────────────────────────────────────────────

    def _draw_controls(self, surface: pygame.Surface) -> None:
        hint = self._font.render(
            "WASD / Arrows: move  |  Space: sword  |  LClick: fireball  |  ESC: quit",
            True, COLOR_HUD_TEXT_DIM)
        surface.blit(hint, (10, SCREEN_HEIGHT - 22))

    def _draw_fireball_cooldown(self, surface: pygame.Surface,
                               remaining: float) -> None:
        label = ("Fireball Ready"
                 if remaining <= 0 else f"Fireball Ready In: {remaining:.1f}s")
        color = COLOR_HUD_TEXT if remaining <= 0 else COLOR_HUD_TEXT_DIM
        text = self._font.render(label, True, color)
        surface.blit(text, (16, 44))

    def _draw_ultimate_status(self, surface: pygame.Surface,
                              ready: bool, active: bool) -> None:
        if active:
            label = "Ultimate Active!"
            color = COLOR_HUD_TEXT
        elif ready:
            label = "Ultimate Ready (E)"
            color = COLOR_HUD_TEXT
        else:
            label = "Ultimate: build 5 sword melee kills"
            color = COLOR_HUD_TEXT_DIM
        text = self._font.render(label, True, color)
        x = SCREEN_WIDTH - text.get_width() - 16
        y = 124
        surface.blit(text, (x, y))

    # ── game-over overlay ────────────────────────────────────────────────

    def _draw_game_over(self, surface: pygame.Surface, score: int,
                        melee_kills: int, ranged_kills: int,
                        sword_kills: int, fireball_kills: int) -> None:
        # Dim the screen
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        # Title
        title = self._font_big.render("GAME  OVER", True, (200, 40, 40))
        tw = title.get_width()
        surface.blit(title, ((SCREEN_WIDTH - tw) // 2, SCREEN_HEIGHT // 2 - 120))

        # Final score
        sc = self._font_med.render(f"Final Score: {score}", True, COLOR_HUD_TEXT)
        sw = sc.get_width()
        surface.blit(sc, ((SCREEN_WIDTH - sw) // 2, SCREEN_HEIGHT // 2 - 50))

        stats = [
            f"Melee Enemies Killed: {melee_kills}",
            f"Ranged Enemies Killed: {ranged_kills}",
            f"Sword Kills: {sword_kills}",
            f"Fireball Kills: {fireball_kills}",
        ]
        start_y = SCREEN_HEIGHT // 2 - 10
        line_height = 24
        for idx, line in enumerate(stats):
            text = self._font_med.render(line, True, COLOR_HUD_TEXT)
            tw = text.get_width()
            surface.blit(text, ((SCREEN_WIDTH - tw) // 2, start_y + idx * line_height))

        # Restart hint
        hint = self._font.render("Press  ENTER  to return to menu  |  ESC  to quit",
                                 True, COLOR_HUD_TEXT_DIM)
        hw = hint.get_width()
        surface.blit(hint, ((SCREEN_WIDTH - hw) // 2, start_y + len(stats) * line_height + 24))

    # ── main menu overlay ────────────────────────────────────────────────

    def draw_menu(self, surface: pygame.Surface,
                  button_rects: list[pygame.Rect],
                  hovered: int | None) -> None:
        """Draw the title screen menu with buttons."""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        surface.blit(overlay, (0, 0))

        title = self._font_title.render("DUNGEON  CRAWLER", True, COLOR_MENU_TITLE)
        tw = title.get_width()
        surface.blit(title, ((SCREEN_WIDTH - tw) // 2, 140))

        subtitle = self._font_menu_small.render("A descent into the forgotten halls",
                                                 True, COLOR_MENU_TEXT_DIM)
        sw = subtitle.get_width()
        surface.blit(subtitle, ((SCREEN_WIDTH - sw) // 2, 210))

        button_labels = ["Start Game", "Quit"]
        for idx, rect in enumerate(button_rects):
            is_hover = hovered == idx
            bg = COLOR_MENU_BUTTON_BG_HOVER if is_hover else COLOR_MENU_BUTTON_BG
            pygame.draw.rect(surface, bg, rect, border_radius=8)
            pygame.draw.rect(surface, COLOR_MENU_BUTTON_BORDER, rect, 2,
                             border_radius=8)

            text = self._font_menu.render(button_labels[idx], True,
                                          COLOR_MENU_BUTTON_TEXT)
            tx = rect.centerx - text.get_width() // 2
            ty = rect.centery - text.get_height() // 2
            surface.blit(text, (tx, ty))

        hint = self._font_menu_small.render("Click or press ENTER to begin",
                                            True, COLOR_MENU_TEXT)
        hw = hint.get_width()
        surface.blit(hint, ((SCREEN_WIDTH - hw) // 2, 520))
