import numpy as np
import torch
from torch import nn

from tag.arena import MOVES
from tag.strategies import legal_actions


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