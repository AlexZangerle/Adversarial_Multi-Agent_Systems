from tag.arena import MOVES, Arena


def random_strategy(arena: Arena, agent: int) -> int:
    return int(arena.rng.integers(len(MOVES)))
