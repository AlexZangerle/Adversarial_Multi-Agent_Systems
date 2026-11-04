from tag.arena import MOVES, Arena

def legal_actions(arena: Arena, agent: int) -> list[int]:
    return [a for a, move in enumerate(MOVES) if arena.is_free(*(arena.positions[agent] + move))]

def random_strategy(arena: Arena, agent: int) -> int:
    return int(arena.rng.choice(legal_actions(arena, agent)))