import argparse

import pygame

from tag.arena import Arena
from tag.episode import evaluate, select_actions
from tag.qlearning import Q_PATH, QPursuer
from tag.render import CELL, draw
from tag.strategies import EVADER_STRATEGIES, PURSUER_STRATEGIES


def main() -> None:
    pursuer_strategies = {**PURSUER_STRATEGIES, "q": QPursuer(Q_PATH)}
    parser = argparse.ArgumentParser()
    parser.add_argument("--evaders", type=int, default=1)
    parser.add_argument("--pursuers", type=int, default=3)
    parser.add_argument("--evader", choices=EVADER_STRATEGIES, default="random")
    parser.add_argument("--pursuer", choices=pursuer_strategies, default="random")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--fps", type=int, default=8)
    parser.add_argument("--max-steps", type=int, default=200)
    parser.add_argument("--episodes", type=int)
    args = parser.parse_args()

    evader_strategy = EVADER_STRATEGIES[args.evader]
    pursuer_strategy = pursuer_strategies[args.pursuer]

    if args.episodes:
        rate, mean_steps = evaluate(evader_strategy, pursuer_strategy, args.episodes, args.evaders, args.pursuers, args.seed, args.max_steps)
        print(f"capture rate {rate:.0%}, mean steps {mean_steps:.1f}")
        return

    arena = Arena(args.evaders, args.pursuers, args.seed)

    pygame.init()
    h, w = arena.walls.shape
    screen = pygame.display.set_mode((w * CELL, h * CELL))
    clock = pygame.time.Clock()

    steps = 0
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        if not arena.caught() and steps < args.max_steps:
            arena.step(select_actions(arena, evader_strategy, pursuer_strategy))
            steps += 1

        draw(screen, arena)
        pygame.display.flip()
        clock.tick(args.fps)

    pygame.quit()