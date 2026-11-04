import pygame

from tag.arena import EVADER, Arena

CELL = 40


def draw(screen: pygame.Surface, arena: Arena) -> None:
    screen.fill("white")

    h, w = arena.walls.shape
    for r in range(h):
        for c in range(w):
            rect = pygame.Rect(c * CELL, r * CELL, CELL, CELL)
            if arena.walls[r, c]:
                pygame.draw.rect(screen, "black", rect)
            pygame.draw.rect(screen, "gray", rect, 1)

    for (r, c), role in zip(arena.positions, arena.roles):
        center = (c * CELL + CELL // 2, r * CELL + CELL // 2)
        color = "blue" if role == EVADER else "red"
        pygame.draw.circle(screen, color, center, CELL // 3)
