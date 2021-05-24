import pygame
from pygame import sprite
from pygame.locals import *
import math
import sys


SCREEN_SIZE = (800, 600)
PLAYER_SIZE = 60
PLAYER_VERTICES = 3  # a triangle


class Polygon(sprite.Sprite):
    """Draw a regular polygon inside a sprite."""
    def __init__(self, size, n) -> None:
        """Prepare a surface containing the polygon.
        size:   size of containing surface (rectangular area as the polygon is regular)
        n:      this will be an n-sided polygon"""
        super().__init__()
        self.image = pygame.Surface((size, size))
        pygame.draw.polygon(self.image, pygame.Color("white"), self._vertices(size, n), n)
        self.rect = self.image.get_rect()

    def _vertices(self, size, n):
        """Calculate the vertices of the polygon.
        Returns:    a list of pair of coordinates"""
        r = size // 2  # radius of enclosing circle
        angle = math.radians(360 / n)  # inner angle of polygon
        # 'r +' means here that origin is in the rect's middle
        return [[int(r + r*math.sin(i*angle)), int(r + r*math.cos(i*angle))] for i in range(0, n)]


class Player(Polygon):
    """Player is a triangle."""
    def __init__(self):
        """Initialize a triangle, representing a starfighter."""
        super().__init__(PLAYER_SIZE, PLAYER_VERTICES)
        self.image = pygame.transform.rotate(self.image, 180)  # turn upside down so it has tip upward

    def update(self):
        self.rect.center = pygame.mouse.get_pos()  # bind the movement to the mouse pointer


class Euclides:
    """Main game application."""
    def __init__(self) -> None:
        pygame.init()
        self._screen = pygame.display.set_mode(SCREEN_SIZE)
        pygame.display.set_caption("Euclides")
        self._main()

    def _main(self) -> None:
        """Execute the application."""
        player = Player()
        sprites = sprite.RenderPlain((player, ))

        while 1:
            self._screen.fill((0, 0, 0))
            for event in pygame.event.get():
                if event.type == QUIT:  # exit by closing the window
                    sys.exit()
            sprites.update()
            sprites.draw(self._screen)
            pygame.display.update()


if __name__ == "__main__":
    Euclides()