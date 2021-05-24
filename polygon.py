import pygame
from pygame.locals import *
import math


class Polygon(pygame.Surface):
    """Draw and manage a regular polygon."""
    def __init__(self, size, n=3):
        """Prepare a surface containing the polygon.
        size:   size of containing surface (rectangular area as the polygon is regular)
        n:      this will be an n-sided polygon"""
        super().__init__((size, size))
        self._size = size
        self._n = n
        pygame.draw.polygon(self, pygame.Color("white"), self._calculate_vertices(), n)
    
    def _calculate_vertices(self):
        """Calculate the vertices of the polygon.
        Returns:    a list of pair of coordinates"""
        r = self._size // 2  # radius of enclosing circle
        angle = math.radians(360 / self._n)  # inner angle of polygon
        # 'r +' means here that origin is in the rect's middle
        return [[int(r + r*math.sin(i*angle)), int(r + r*math.cos(i*angle))] for i in range(0, self._n)]


def test_polygon() -> None:
    """Testing the Polygon class"""
    import sys

    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Test Polygon")

    poly = Polygon(120, 3)

    while 1:
        screen.fill((0,0,0))
        for event in pygame.event.get():
            if event.type == QUIT:  # exit by closing the window
                sys.exit()
        screen.blit(poly, (400, 300))
        pygame.display.update()
    


if __name__ == "__main__":
    test_polygon()