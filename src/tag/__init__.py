import argparse

import pygame

from tag.arena import EVADER, PURSUER, Arena
from tag.episode import evaluate, select_actions
from tag.render import CELL, draw
from tag.strategies import EVADER_STRATEGIES, PURSUER_STRATEGIES


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("-ne", "--evaders", type=int, default=1)
    parser.add_argument("-np", "--pursuers", type=int, default=3)
    parser.add_argument("-e", "--evader", choices=EVADER_STRATEGIES, default="random")
    parser.add_argument("-p", "--pursuer", choices=PURSUER_STRATEGIES, default="random")
    parser.add_argument("-s", "--seed", type=int, default=0)
    parser.add_argument("-f", "--fps", type=int, default=8)
    parser.add_argument("-r", "--radius", type=int)
    parser.add_argument("-m", "--max-steps", type=int, default=200)
    parser.add_argument("-n", "--episodes", type=int)
    args = parser.parse_args()

    strategies = {EVADER: EVADER_STRATEGIES[args.evader], PURSUER: PURSUER_STRATEGIES[args.pursuer]}

    if args.episodes:
        rate, mean_steps = evaluate(strategies, args.episodes, args.evaders, args.pursuers, args.seed, args.max_steps, args.radius)
        print(f"capture rate {rate:.0%}, mean steps {mean_steps:.1f}")
        return

    arena = Arena(args.evaders, args.pursuers, args.seed)

    pygame.init()
    h, w = arena.walls.shape
    screen = pygame.display.set_mode((w * CELL, h * CELL))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 24)

    steps = 0
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        if not arena.caught() and steps < args.max_steps:
            arena.step(select_actions(arena, strategies, args.radius))
            steps += 1

        draw(screen, arena, args.radius)
        screen.blit(font.render(f"{args.evader} vs {args.pursuer}", True, "black", "white"), (4, 4))
        pygame.display.flip()
        clock.tick(args.fps)

    pygame.quit()