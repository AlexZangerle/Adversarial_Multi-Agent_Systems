import numpy as np

from tag.arena import Arena


def select_actions(arena: Arena, strategies: dict, radius: int | None = None) -> list[int]:
    return [strategies[role](arena.observe(i, radius), arena.rng) for i, role in enumerate(arena.roles)]


def run_episode(arena: Arena, strategies: dict, max_steps: int, radius: int | None = None) -> int:
    steps = 0
    while not arena.caught() and steps < max_steps:
        arena.step(select_actions(arena, strategies, radius))
        steps += 1
    return steps


def evaluate(
    strategies: dict, episodes: int, n_evaders: int, n_pursuers: int, seed: int, max_steps: int, radius: int | None = None
) -> tuple[float, float]:
    caught, steps = [], []
    for s in range(seed, seed + episodes):
        arena = Arena(n_evaders, n_pursuers, s)
        steps.append(run_episode(arena, strategies, max_steps, radius))
        caught.append(arena.caught())
    return float(np.mean(caught)), float(np.mean(steps))