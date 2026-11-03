import argparse

import pygame

from tag.arena import EVADER, Arena
from tag.render import CELL, draw
from tag.strategies import random_strategy


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evaders", type=int, default=1)
    parser.add_argument("--pursuers", type=int, default=3)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--fps", type=int, default=8)
    args = parser.parse_args()

    arena = Arena(args.evaders, args.pursuers, args.seed)
    evader_strategy = random_strategy
    pursuer_strategy = random_strategy

    pygame.init()
    h, w = arena.walls.shape
    screen = pygame.display.set_mode((w * CELL, h * CELL))
    clock = pygame.time.Clock()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        if not arena.caught():
            actions = [evader_strategy(arena, i) if role == EVADER else pursuer_strategy(arena, i) for i, role in enumerate(arena.roles)]
            arena.step(actions)

        draw(screen, arena)
        pygame.display.flip()
        clock.tick(args.fps)

    pygame.quit()
