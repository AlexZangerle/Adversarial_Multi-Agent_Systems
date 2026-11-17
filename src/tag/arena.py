from itertools import combinations

import numpy as np

EVADER, PURSUER = 0, 1
WALLS, TEAMMATES, OPPONENTS = range(3)
STAY, UP, DOWN, LEFT, RIGHT = range(5)
MOVES = np.array([(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)])

MAP = """
..............
..............
..........#...
..####....#...
..........#...
..........#...
..#...........
..#....#......
..#....#......
.......#......
.......#.###..
.....##.......
..............
..............
"""


class Arena:
    def __init__(self, n_evaders: int = 1, n_pursuers: int = 3, seed: int | None = None):
        self.walls = np.array([[c == "#" for c in row] for row in MAP.split()])
        self.roles = np.array([EVADER] * n_evaders + [PURSUER] * n_pursuers)
        self.n_agents = len(self.roles)
        self.rng = np.random.default_rng(seed)

        free = np.argwhere(~self.walls)
        self.positions = free[self.rng.choice(len(free), size=self.n_agents, replace=False)]

    @property
    def evaders(self) -> np.ndarray:
        return self.positions[self.roles == EVADER]

    @property
    def pursuers(self) -> np.ndarray:
        return self.positions[self.roles == PURSUER]

    def is_free(self, r: int, c: int) -> bool:
        h, w = self.walls.shape
        return 0 <= r < h and 0 <= c < w and not self.walls[r, c]

    def observe(self, agent: int, radius: int | None = None) -> np.ndarray:
        if radius is None:
            radius = max(self.walls.shape) - 1
        size = 2 * radius + 1
        obs = np.zeros((3, size, size), dtype=bool)
        r, c = self.positions[agent]
        obs[WALLS] = np.pad(self.walls, radius, constant_values=True)[r : r + size, c : c + size]
        for j, pos in enumerate(self.positions):
            dr, dc = pos - self.positions[agent]
            if j != agent and max(abs(dr), abs(dc)) <= radius:
                obs[TEAMMATES if self.roles[j] == self.roles[agent] else OPPONENTS, dr + radius, dc + radius] = True
        return obs

    def caught(self) -> bool:
        return any(np.abs(e - p).sum() <= 1 for e in self.evaders for p in self.pursuers)

    def step(self, actions: list[int]) -> None:
        old = self.positions
        new = old + MOVES[actions]

        for i in range(self.n_agents):
            if not self.is_free(*new[i]):
                new[i] = old[i]

        changed = True
        while changed:
            changed = False
            for i, j in combinations(range(self.n_agents), 2):
                same_cell = (new[i] == new[j]).all()
                swap = (new[i] == old[j]).all() and (new[j] == old[i]).all()
                if same_cell or swap:
                    for k in (i, j):
                        if (new[k] != old[k]).any():
                            new[k] = old[k]
                            changed = True

        self.positions = new
