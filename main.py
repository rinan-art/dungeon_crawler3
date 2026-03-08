#!/usr/bin/env python3
"""
main.py — Entry point for the Dungeon Crawler game.

Initialises Pygame, creates the GameManager, and runs the main loop.
"""

import sys

import pygame

from settings import SCREEN_WIDTH, SCREEN_HEIGHT, FPS
from game_manager import GameManager


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Dungeon Crawler")
    clock = pygame.time.Clock()

    game = GameManager()

    while True:
        # ── Events ───────────────────────────────────────────────────
        for event in pygame.event.get():
            if not game.handle_event(event):
                pygame.quit()
                sys.exit()

        # ── Update ───────────────────────────────────────────────────
        keys = pygame.key.get_pressed()
        game.update(keys)

        # ── Draw ─────────────────────────────────────────────────────
        game.draw(screen)

        # ── Flip & tick ──────────────────────────────────────────────
        pygame.display.flip()
        clock.tick(FPS)


if __name__ == '__main__':
    main()
