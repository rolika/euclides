import pygame
from pygame import sprite
from pygame.locals import *
import math


PLAYER_SIZE = 60
PLAYER_VERTICES = 3  # a triangle


class Polygon(sprite.Sprite):
    """Draw a regular polygon inside a sprite."""
    def __init__(self, size, n) -> None:
        """Prepare a surface containing the polygon.
        size:   size of containing surface (rectangular area as the polygon is regular)
        n:      this will be an n-sided polygon"""
        super().__init__()
        self._size = size
        self._n = n
        self.image = pygame.Surface((size, size))
        pygame.draw.polygon(self.image, pygame.Color("white"), self._calculate_vertices(), n)
        self.rect = self.image.get_rect()
    
    def _calculate_vertices(self):
        """Calculate the vertices of the polygon.
        Returns:    a list of pair of coordinates"""
        r = self._size // 2  # radius of enclosing circle
        angle = math.radians(360 / self._n)  # inner angle of polygon
        # 'r +' means here that origin is in the rect's middle
        return [[int(r + r*math.sin(i*angle)), int(r + r*math.cos(i*angle))] for i in range(0, self._n)]


class Player(Polygon):
    """Player is a type of polygon."""
    def __init__(self):
        """Init a triangle, with an angle upwards, representing a simple starship."""
        super().__init__(PLAYER_SIZE, PLAYER_VERTICES)
        self.image = pygame.transform.rotate(self.image, 180)  # turn upside down so it has an angle upward
    
    def update(self):
        self.rect.center = pygame.mouse.get_pos()  # bind the movement to the mouse pointer


def test_polygon() -> None:
    """Testing the Polygon class"""
    import sys

    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Test Polygon")

    player = Player()
    sprites = sprite.RenderPlain((player, ))

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