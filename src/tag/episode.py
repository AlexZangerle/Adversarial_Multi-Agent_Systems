import numpy as np

from tag.arena import EVADER, Arena


def select_actions(arena: Arena, evader_strategy, pursuer_strategy) -> list[int]:
    return [evader_strategy(arena, i) if role == EVADER else pursuer_strategy(arena, i) for i, role in enumerate(arena.roles)]


def run_episode(arena: Arena, evader_strategy, pursuer_strategy, max_steps: int) -> int:
    steps = 0
    while not arena.caught() and steps < max_steps:
        arena.step(select_actions(arena, evader_strategy, pursuer_strategy))
        steps += 1
    return steps


def evaluate(evader_strategy, pursuer_strategy, episodes: int, n_evaders: int, n_pursuers: int, seed: int, max_steps: int) -> tuple[float, float]:
    caught, steps = [], []
    for s in range(seed, seed + episodes):
        arena = Arena(n_evaders, n_pursuers, s)
        steps.append(run_episode(arena, evader_strategy, pursuer_strategy, max_steps))
        caught.append(arena.caught())
    return float(np.mean(caught)), float(np.mean(steps))