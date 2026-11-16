import argparse

import numpy as np

from tag.arena import EVADER, MOVES, PURSUER, Arena
from tag.strategies import EVADER_STRATEGIES, legal_actions

REWARD_WEIGHTS = {"capture": 10.0, "step": -1.0}
Q_PATH = "q_pursuer.npy"


def state(arena: Arena, agent: int) -> tuple[int, int, int, int]:
    position = arena.positions[agent]
    target = arena.evaders[np.abs(arena.evaders - position).sum(axis=1).argmin()]
    return int(position[0]), int(position[1]), int(target[0]), int(target[1])


def best_action(q: np.ndarray, arena: Arena, agent: int, rng: np.random.Generator) -> int:
    actions = np.array(legal_actions(arena, agent))
    values = q[state(arena, agent)][actions]
    return int(rng.choice(actions[values == values.max()]))

def reward(captured: bool) -> float:
    components = {"capture": float(captured), "step": 1.0}
    return sum(REWARD_WEIGHTS[name] * value for name, value in components.items())


def train(
    episodes: int,
    evader_strategy,
    n_pursuers: int = 3,
    max_steps: int = 200,
    alpha: float = 0.2,
    gamma: float = 0.95,
    eps_end: float = 0.05,
    seed: int = 10_000,
) -> np.ndarray:
    rng = np.random.default_rng(seed)
    q = np.zeros(Arena(1, n_pursuers, seed).walls.shape * 2 + (len(MOVES),))
    captures = []

    for episode in range(episodes):
        eps = max(eps_end, 1 - episode / (0.6 * episodes))
        arena = Arena(1, n_pursuers, seed + episode)
        pursuers = np.flatnonzero(arena.roles == PURSUER)

        steps = 0
        while not arena.caught() and steps < max_steps:
            states = {i: state(arena, i) for i in pursuers}
            actions = []
            for i, role in enumerate(arena.roles):
                if role == EVADER:
                    actions.append(evader_strategy(arena, i))
                elif rng.random() < eps:
                    actions.append(int(rng.choice(legal_actions(arena, i))))
                else:
                    actions.append(best_action(q, arena, i, rng))

            arena.step(actions)
            steps += 1
            captured = arena.caught()
            r = reward(captured)
            for i in pursuers:
                target = r if captured else r + gamma * q[state(arena, i)].max()
                q[states[i] + (actions[i],)] += alpha * (target - q[states[i] + (actions[i],)])

        captures.append(arena.caught())
        if (episode + 1) % max(1, episodes // 10) == 0:
            print(f"episode {episode + 1}/{episodes}, eps {eps:.2f}, capture rate {np.mean(captures[-episodes // 10 :]):.0%}")

    return q


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--episodes", type=int, default=30_000)
    parser.add_argument("--evader", choices=EVADER_STRATEGIES, default="greedy")
    parser.add_argument("--pursuers", type=int, default=3)
    parser.add_argument("--max-steps", type=int, default=200)
    parser.add_argument("--out", default=Q_PATH)
    args = parser.parse_args()

    q = train(args.episodes, EVADER_STRATEGIES[args.evader], args.pursuers, args.max_steps)
    np.save(args.out, q)
    print(f"saved {args.out}")