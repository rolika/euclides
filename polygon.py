import pygame
from pygame import sprite
from pygame.locals import *
import math


class Polygon(sprite.Sprite):
    """Draw and manage a regular polygon."""
    def __init__(self, size, n=3) -> None:
        """Prepare a surface containing the polygon.
        size:   size of containing surface (rectangular area as the polygon is regular)
        n:      this will be an n-sided polygon (also represents the hull-thickness)"""
        super().__init__()
        self._size = size
        self._n = n
        self.image = pygame.Surface((size, size))
        pygame.draw.polygon(self.image, pygame.Color("white"), self._calculate_vertices(), n)
        self.rect = self.image.get_rect()
    
    def update(self):
        self.rect.center = 400, 300
    
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

    poly = Polygon(160, 7)
    sprites = sprite.RenderPlain((poly, ))

    while 1:
        screen.fill((0,0,0))
        for event in pygame.event.get():
            if event.type == QUIT:  # exit by closing the window
                sys.exit()
        sprites.update()
        sprites.draw(screen)
        pygame.display.update()
    


if __name__ == "__main__":
    test_polygon()