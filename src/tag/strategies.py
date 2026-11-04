import numpy as np

from tag.arena import MOVES, Arena


def legal_actions(arena: Arena, agent: int) -> list[int]:
    return [a for a, move in enumerate(MOVES) if arena.is_free(*(arena.positions[agent] + move))]


def nearest_distance(cell: np.ndarray, others: np.ndarray) -> int:
    return int(np.abs(others - cell).sum(axis=1).min())


def random_strategy(arena: Arena, agent: int) -> int:
    return int(arena.rng.choice(legal_actions(arena, agent)))


def greedy(arena: Arena, agent: int, opponents: np.ndarray, sign: int) -> int:
    actions = legal_actions(arena, agent)
    scores = [sign * nearest_distance(arena.positions[agent] + MOVES[a], opponents) for a in actions]
    best = [a for a, s in zip(actions, scores) if s == max(scores)]
    return int(arena.rng.choice(best))


def greedy_pursuer(arena: Arena, agent: int) -> int:
    return greedy(arena, agent, arena.evaders, -1)


def greedy_evader(arena: Arena, agent: int) -> int:
    return greedy(arena, agent, arena.pursuers, 1)


EVADER_STRATEGIES = {"random": random_strategy, "greedy": greedy_evader}
PURSUER_STRATEGIES = {"random": random_strategy, "greedy": greedy_pursuer}
