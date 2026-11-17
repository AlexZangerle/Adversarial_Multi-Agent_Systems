import heapq
from collections.abc import Callable

import numpy as np

from tag.arena import MOVES, OPPONENTS, STAY, WALLS

type Strategy = Callable[[np.ndarray, np.random.Generator], int]


def center(obs: np.ndarray) -> np.ndarray:
    return np.full(2, obs.shape[1] // 2)


def is_free(obs: np.ndarray, r: int, c: int) -> bool:
    size = obs.shape[1]
    return 0 <= r < size and 0 <= c < size and not obs[WALLS, r, c]


def legal_actions(obs: np.ndarray) -> list[int]:
    return [a for a, move in enumerate(MOVES) if is_free(obs, *(center(obs) + move))]


def nearest_distance(cell: np.ndarray, others: np.ndarray) -> int:
    return int(np.abs(others - cell).sum(axis=1).min())


def random_strategy(obs: np.ndarray, rng: np.random.Generator) -> int:
    """Choose one legal action at random, including staying in place."""
    return int(rng.choice(legal_actions(obs)))


def greedy(obs: np.ndarray, rng: np.random.Generator, sign: int) -> int:
    opponents = np.argwhere(obs[OPPONENTS])
    if len(opponents) == 0:
        return random_strategy(obs, rng)
    actions = legal_actions(obs)
    scores = [sign * nearest_distance(center(obs) + MOVES[a], opponents) for a in actions]
    best = [a for a, s in zip(actions, scores) if s == max(scores)]
    return int(rng.choice(best))


def greedy_pursuer(obs: np.ndarray, rng: np.random.Generator) -> int:
    return greedy(obs, rng, -1)


def greedy_evader(obs: np.ndarray, rng: np.random.Generator) -> int:
    return greedy(obs, rng, 1)


def astar_pursuer(obs: np.ndarray, rng: np.random.Generator) -> int:
    """Find a shortest route within the view to a cell next to a visible evader and return its first action."""
    evaders = np.argwhere(obs[OPPONENTS])
    if len(evaders) == 0:
        return random_strategy(obs, rng)
    start = tuple(center(obs))

    def heuristic(cell):
        # Capture happens at distance <= 1, so stop one cell before the evader.
        return max(0, nearest_distance(np.array(cell), evaders) - 1)

    # Entries contain: estimated total cost, travelled cost, cell, first action.
    frontier = [(heuristic(start), 0, start, STAY)]
    costs = {start: 0}
    while frontier:
        _, cost, cell, first_action = heapq.heappop(frontier)
        if cost != costs[cell]:
            continue
        if heuristic(cell) == 0:
            return first_action
        for action, move in enumerate(MOVES):
            if action == STAY:
                continue
            next_cell = (cell[0] + move[0], cell[1] + move[1])
            if not is_free(obs, *next_cell):
                continue
            new_cost = cost + 1
            if new_cost < costs.get(next_cell, float("inf")):
                costs[next_cell] = new_cost
                first = action if cell == start else first_action
                priority = new_cost + heuristic(next_cell)
                heapq.heappush(frontier, (priority, new_cost, next_cell, first))
    return STAY  # No route to any evader within the view.


EVADER_STRATEGIES: dict[str, Strategy] = {"random": random_strategy, "greedy": greedy_evader}
PURSUER_STRATEGIES: dict[str, Strategy] = {"random": random_strategy, "greedy": greedy_pursuer, "astar": astar_pursuer}
