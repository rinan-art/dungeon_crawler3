"""
settings.py — Central configuration for the Dungeon Crawler game.

All constants, colour palettes, gameplay tuning values, and the dungeon
map live here so every other module can ``from settings import *``.
"""

# ---------------------------------------------------------------------------
# Display
# ---------------------------------------------------------------------------
SCREEN_WIDTH = 960
SCREEN_HEIGHT = 720
TILE_SIZE = 48
FPS = 60

# ---------------------------------------------------------------------------
# Hero
# ---------------------------------------------------------------------------
HERO_SIZE = 40
HERO_SPEED = 3.6          # pixels per frame at 60 FPS
HERO_MAX_HP = 100
HERO_HITBOX_SHRINK = 6    # pixels trimmed from each side for tighter collision
HERO_INVINCIBILITY_MS = 800   # milliseconds of invincibility after taking a hit

# Attack
ATTACK_DURATION_MS = 250      # how long the swing animation lasts (ms)
ATTACK_COOLDOWN_MS = 400      # minimum time between attacks (ms)
ATTACK_RANGE = 38             # pixels from hero centre to tip of swing arc
ATTACK_ARC_DEG = 120          # total sweep angle of the sword swing (degrees)
ATTACK_KNOCKBACK = 0          # reserved for future use

# Ultimate attack
ULTIMATE_REQUIRED_MELEE_SWORD_KILLS = 5
ULTIMATE_COOLDOWN_AFTER_USE_MS = 5000
ULTIMATE_DURATION_MS = 420
ULTIMATE_RANGE = 110

# Ranged attack
FIREBALL_SPEED = 7.5          # pixels per frame
FIREBALL_RADIUS = 6           # visual radius in pixels
FIREBALL_COOLDOWN_MS = 320    # time between shots
FIREBALL_DAMAGE = 100         # direct-hit damage to enemies

# Scoring
SCORE_PER_KILL = 10           # points awarded per enemy killed

# Health orbs (dropped by defeated enemies)
ORB_DROP_CHANCE = 0.20        # 20 % chance an enemy drops a health orb on death
ORB_HEAL_AMOUNT = 20          # HP restored when the hero picks up an orb
ORB_RADIUS = 8                # visual radius of the orb sprite (pixels)
ORB_COLLECT_RADIUS = 22       # hero must be within this many pixels to collect
ORB_LIFETIME_MS = 8000        # orb disappears after this many milliseconds
ORB_BOB_SPEED = 0.06          # speed of the idle bob animation
ORB_BOB_AMP = 2.5             # amplitude (pixels) of the idle bob
ORB_PULSE_SPEED = 0.04        # speed of the glow pulse cycle
ORB_COLLECT_VFX_MS = 400      # duration of the collection visual feedback

# ---------------------------------------------------------------------------
# Enemies
# ---------------------------------------------------------------------------
ENEMY_SIZE = 34
ENEMY_SPEED = 1.6
ENEMY_DAMAGE = 10         # HP removed per hit

# Ranged enemies
RANGED_ENEMY_SPEED = 1.4
RANGED_ENEMY_MIN_DISTANCE = 120
RANGED_ENEMY_MAX_DISTANCE = 220
RANGED_ENEMY_SHOOT_COOLDOWN_MS = 1100
RANGED_ENEMY_SPAWN_CHANCE = 0.25

ENEMY_PROJECTILE_SPEED = 5.5
ENEMY_PROJECTILE_RADIUS = 5
ENEMY_PROJECTILE_DAMAGE = 12

# Spawning
SPAWN_INTERVAL_MIN = 1.5  # seconds between spawn waves (minimum)
SPAWN_INTERVAL_MAX = 3.5  # seconds between spawn waves (maximum)
SPAWN_PER_WAVE_MIN = 1    # enemies per wave (minimum)
SPAWN_PER_WAVE_MAX = 3    # enemies per wave (maximum)
MAX_ENEMIES = 15          # hard cap on simultaneous enemies

# ---------------------------------------------------------------------------
# Colour palette — dark atmospheric dungeon
# ---------------------------------------------------------------------------
COLOR_BLACK = (0, 0, 0)
COLOR_WHITE = (255, 255, 255)

# Floor
COLOR_FLOOR_BASE = (28, 24, 22)
COLOR_FLOOR_ACCENT1 = (34, 29, 26)
COLOR_FLOOR_ACCENT2 = (22, 19, 17)
COLOR_FLOOR_CRACK = (18, 15, 13)
COLOR_FLOOR_MOSS = (24, 32, 20)

# Walls
COLOR_WALL_FACE = (52, 46, 42)
COLOR_WALL_TOP = (68, 60, 54)
COLOR_WALL_DARK = (36, 32, 28)
COLOR_WALL_HIGHLIGHT = (78, 70, 62)
COLOR_WALL_MORTAR = (40, 36, 32)

# Hero
COLOR_HERO_BODY = (45, 90, 160)
COLOR_HERO_ARMOR = (60, 110, 185)
COLOR_HERO_ARMOR_LIGHT = (80, 135, 210)
COLOR_HERO_SKIN = (210, 170, 130)
COLOR_HERO_HAIR = (60, 35, 20)
COLOR_HERO_EYES = (220, 220, 240)
COLOR_HERO_CLOAK = (130, 40, 40)
COLOR_HERO_CLOAK_DARK = (95, 28, 28)
COLOR_HERO_SWORD_BLADE = (190, 195, 205)
COLOR_HERO_SWORD_HILT = (140, 100, 30)
COLOR_HERO_BOOTS = (50, 35, 25)

# Enemies
COLOR_ENEMY_BODY = (80, 45, 55)
COLOR_ENEMY_SKIN = (90, 140, 80)
COLOR_ENEMY_SKIN_LIGHT = (110, 165, 95)
COLOR_ENEMY_EYES = (220, 50, 30)
COLOR_ENEMY_HORN = (60, 50, 40)
COLOR_ENEMY_TEETH = (200, 195, 170)
COLOR_ENEMY_CLAWS = (65, 55, 45)

# HUD
COLOR_HUD_HP_BG = (40, 10, 10)
COLOR_HUD_HP_FILL = (180, 30, 30)
COLOR_HUD_HP_FILL_LOW = (220, 60, 20)
COLOR_HUD_HP_BORDER = (120, 100, 90)
COLOR_HUD_TEXT = (190, 175, 160)
COLOR_HUD_TEXT_DIM = (120, 110, 100)

# Attack swing
COLOR_ATTACK_BLADE = (210, 215, 225)
COLOR_ATTACK_TRAIL = (170, 180, 200)
COLOR_ATTACK_GLOW = (255, 255, 240)

# Fireballs
COLOR_FIREBALL_CORE = (240, 120, 40)
COLOR_FIREBALL_GLOW = (255, 170, 90)
COLOR_FIREBALL_HALO = (255, 210, 160)

# Enemy projectiles
COLOR_ENEMY_PROJECTILE_CORE = (80, 160, 255)
COLOR_ENEMY_PROJECTILE_GLOW = (120, 190, 255)
COLOR_ENEMY_PROJECTILE_HALO = (190, 225, 255)

# Health orbs
COLOR_ORB_CORE = (80, 220, 100)
COLOR_ORB_BRIGHT = (140, 255, 160)
COLOR_ORB_GLOW = (60, 200, 80)
COLOR_ORB_COLLECT_FLASH = (180, 255, 200)
COLOR_ORB_HEAL_TEXT = (100, 255, 120)

# Atmosphere
COLOR_VIGNETTE = (0, 0, 0)
COLOR_AMBIENT_LIGHT = (255, 220, 160)

# ---------------------------------------------------------------------------
# Menu UI
# ---------------------------------------------------------------------------
COLOR_MENU_TITLE = (220, 200, 170)
COLOR_MENU_TEXT = (200, 180, 150)
COLOR_MENU_TEXT_DIM = (140, 120, 95)
COLOR_MENU_BUTTON_BG = (40, 32, 28)
COLOR_MENU_BUTTON_BG_HOVER = (70, 55, 45)
COLOR_MENU_BUTTON_BORDER = (110, 90, 70)
COLOR_MENU_BUTTON_TEXT = (230, 210, 180)

# ---------------------------------------------------------------------------
# Dungeon map  (0 = floor, 1 = wall)
# 20 cols × 15 rows  →  960 × 720 px  (exact screen fit)
# ---------------------------------------------------------------------------
DUNGEON_MAP = [
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 1, 1, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 1, 1, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 1, 1, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 1, 1, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
]

MAP_ROWS = len(DUNGEON_MAP)
MAP_COLS = len(DUNGEON_MAP[0])
