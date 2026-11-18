import argparse
from pathlib import Path

import numpy as np
import torch
from torch import nn

from tag.arena import EVADER, MOVES, PURSUER, Arena
from tag.strategies import EVADER_STRATEGIES, legal_actions

REWARD_WEIGHTS = {"capture": 10.0, "step": -1.0}
DQN_PATH = "dqn_pursuer.pt"


def downsample(n: int) -> int:
    return (n - 1) // 2 + 1


class QNetwork(nn.Module):
    def __init__(self, size: int):
        super().__init__()
        out = downsample(downsample(size))
        self.net = nn.Sequential(
            nn.Conv2d(3, 16, 3, padding=1),
            nn.ReLU(),
            nn.Conv2d(16, 32, 3, stride=2, padding=1),
            nn.ReLU(),
            nn.Conv2d(32, 32, 3, stride=2, padding=1),
            nn.ReLU(),
            nn.Flatten(),
            nn.Linear(32 * out * out, 128),
            nn.ReLU(),
            nn.Linear(128, len(MOVES)),
        )

    def forward(self, obs: torch.Tensor) -> torch.Tensor:
        return self.net(obs.float())


def legal_mask(obs: np.ndarray) -> np.ndarray:
    mask = np.zeros(len(MOVES), dtype=bool)
    mask[legal_actions(obs)] = True
    return mask


class ReplayBuffer:
    def __init__(self, capacity: int, obs_shape: tuple[int, ...]):
        self.capacity = capacity
        self.index = 0
        self.size = 0
        self.obs = np.zeros((capacity, *obs_shape), dtype=bool)
        self.actions = np.zeros(capacity, dtype=np.int64)
        self.rewards = np.zeros(capacity, dtype=np.float32)
        self.next_obs = np.zeros((capacity, *obs_shape), dtype=bool)
        self.dones = np.zeros(capacity, dtype=bool)
        self.next_legal = np.zeros((capacity, len(MOVES)), dtype=bool)

    def __len__(self) -> int:
        return self.size

    def add(self, obs: np.ndarray, action: int, reward: float, next_obs: np.ndarray, done: bool, next_legal: np.ndarray) -> None:
        i = self.index
        self.obs[i] = obs
        self.actions[i] = action
        self.rewards[i] = reward
        self.next_obs[i] = next_obs
        self.dones[i] = done
        self.next_legal[i] = next_legal
        self.index = (i + 1) % self.capacity
        self.size = min(self.size + 1, self.capacity)

    def sample(self, batch_size: int, rng: np.random.Generator) -> tuple[torch.Tensor, ...]:
        idx = rng.integers(self.size, size=batch_size)
        arrays = (self.obs, self.actions, self.rewards, self.next_obs, self.dones, self.next_legal)
        return tuple(torch.from_numpy(a[idx]) for a in arrays)


def masked_q(net: QNetwork, obs: torch.Tensor, legal: torch.Tensor) -> torch.Tensor:
    return net(obs).masked_fill(~legal, float("-inf"))


class DQNPursuer:
    def __init__(self, path: str = DQN_PATH):
        self.path = Path(path)
        self.net = None

    def __call__(self, obs: np.ndarray, rng: np.random.Generator) -> int:
        if self.net is None:
            if not self.path.exists():
                raise SystemExit(f"{self.path} not found, train first with tag-train")
            checkpoint = torch.load(self.path)
            self.net = QNetwork(obs.shape[1])
            try:
                self.net.load_state_dict(checkpoint["state_dict"])
            except RuntimeError:
                raise SystemExit(f"{self.path} was trained with radius {checkpoint['radius']}, run with the same radius")
            self.net.eval()
        with torch.no_grad():
            q = masked_q(self.net, torch.from_numpy(obs[None]), torch.from_numpy(legal_mask(obs)[None]))
        return int(q.argmax())


def reward(captured: bool) -> float:
    components = {"capture": float(captured), "step": 1.0}
    return sum(REWARD_WEIGHTS[name] * value for name, value in components.items())


def update(net: QNetwork, target: QNetwork, optimizer: torch.optim.Optimizer, batch: tuple[torch.Tensor, ...], gamma: float) -> float:
    obs, actions, rewards, next_obs, dones, next_legal = batch
    predicted = net(obs).gather(1, actions.unsqueeze(1)).squeeze(1)
    with torch.no_grad():
        next_q = masked_q(target, next_obs, next_legal).max(1).values
        targets = rewards + gamma * next_q * (1 - dones.float())
    loss = nn.functional.smooth_l1_loss(predicted, targets)
    optimizer.zero_grad()
    loss.backward()
    nn.utils.clip_grad_norm_(net.parameters(), 10.0)
    optimizer.step()
    return loss.item()


def train(
    episodes: int,
    evader_strategy,
    n_pursuers: int = 3,
    max_steps: int = 200,
    radius: int | None = None,
    lr: float = 1e-3,
    gamma: float = 0.95,
    batch_size: int = 64,
    buffer_size: int = 20_000,
    warmup: int = 1_000,
    train_every: int = 4,
    target_sync: int = 250,
    eps_end: float = 0.05,
    seed: int = 10_000,
) -> QNetwork:
    rng = np.random.default_rng(seed)
    torch.manual_seed(seed)
    obs_shape = Arena(1, n_pursuers, seed).observe(0, radius).shape
    net = QNetwork(obs_shape[1])
    target = QNetwork(obs_shape[1])
    target.load_state_dict(net.state_dict())
    optimizer = torch.optim.Adam(net.parameters(), lr=lr)
    buffer = ReplayBuffer(buffer_size, obs_shape)
    captures, losses, updates, total_steps = [], [], 0, 0

    for episode in range(episodes):
        eps = max(eps_end, 1 - episode / (0.6 * episodes))
        arena = Arena(1, n_pursuers, seed + episode)
        pursuers = np.flatnonzero(arena.roles == PURSUER)

        steps = 0
        while not arena.caught() and steps < max_steps:
            observations = [arena.observe(i, radius) for i in range(arena.n_agents)]
            with torch.no_grad():
                obs = torch.from_numpy(np.stack([observations[i] for i in pursuers]))
                legal = torch.from_numpy(np.stack([legal_mask(observations[i]) for i in pursuers]))
                best = dict(zip(pursuers, masked_q(net, obs, legal).argmax(1).tolist()))

            actions = []
            for i, role in enumerate(arena.roles):
                if role == EVADER:
                    actions.append(evader_strategy(observations[i], arena.rng))
                elif rng.random() < eps:
                    actions.append(int(rng.choice(legal_actions(observations[i]))))
                else:
                    actions.append(best[i])

            arena.step(actions)
            steps += 1
            total_steps += 1
            captured = arena.caught()
            r = reward(captured)
            for i in pursuers:
                next_obs = arena.observe(i, radius)
                buffer.add(observations[i], actions[i], r, next_obs, captured, legal_mask(next_obs))

            if len(buffer) >= warmup and total_steps % train_every == 0:
                losses.append(update(net, target, optimizer, buffer.sample(batch_size, rng), gamma))
                updates += 1
                if updates % target_sync == 0:
                    target.load_state_dict(net.state_dict())

        captures.append(arena.caught())
        if (episode + 1) % max(1, episodes // 10) == 0:
            chunk = max(1, episodes // 10)
            loss = np.mean(losses[-1000:]) if losses else float("nan")
            print(f"episode {episode + 1}/{episodes}, eps {eps:.2f}, capture rate {np.mean(captures[-chunk:]):.0%}, loss {loss:.3f}")

    return net


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--episodes", type=int, default=2_000)
    parser.add_argument("-e", "--evader", choices=EVADER_STRATEGIES, default="greedy")
    parser.add_argument("-np", "--pursuers", type=int, default=3)
    parser.add_argument("-m", "--max-steps", type=int, default=200)
    parser.add_argument("-r", "--radius", type=int)
    parser.add_argument("-o", "--out", default=DQN_PATH)
    args = parser.parse_args()

    net = train(args.episodes, EVADER_STRATEGIES[args.evader], args.pursuers, args.max_steps, args.radius)
    torch.save({"state_dict": net.state_dict(), "radius": args.radius}, args.out)
    print(f"saved {args.out}")