import pygame
from pygame import sprite
from pygame.locals import *
import math
import sys


SCREEN_SIZE = SCREEN_WIDTH, SCREEN_HEIGHT = (800, 600)
PLAYER_SIZE = 60
PLAYER_VERTICES = 3  # a triangle
PLAYER_START_POSITION = (SCREEN_WIDTH//2, SCREEN_HEIGHT-100)


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

    def _keep_on_screen(self, x, y) -> None:
        """Always keep the whole polygon on screen.
        x:  intended next horizontal coordinate
        y:  intended next vertical coordinate"""
        frame_left = frame_top = self.rect.width // 2
        frame_right = SCREEN_WIDTH - frame_left
        frame_bottom = SCREEN_HEIGHT - frame_top
        if x < frame_left:
            x = frame_left
        if x > frame_right:
            x = frame_right
        if y < frame_top:
            y = frame_top
        if y > frame_bottom:
            y = frame_bottom
        self.rect.center = (x, y)


class Player(Polygon):
    """Player is a triangle."""
    def __init__(self):
        """Initialize a triangle, representing a starfighter."""
        super().__init__(PLAYER_SIZE, PLAYER_VERTICES)
        self.image = pygame.transform.rotate(self.image, 180)  # turn upside down so it has tip upward
        self.rect.center = PLAYER_START_POSITION

    def update(self):
        self._keep_on_screen(*pygame.mouse.get_pos())


class Euclides:
    """Main game application."""
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Euclides")
        self._screen = pygame.display.set_mode(SCREEN_SIZE)
        self._main()

    def _main(self) -> None:
        """Execute the application."""
        player = Player()
        pygame.mouse.set_pos(PLAYER_START_POSITION)
        sprites = sprite.RenderPlain((player, ))

        while 1:
            self._screen.fill((0, 0, 0))
            for event in pygame.event.get():
                if event.type == QUIT:  # exit by closing the window
                    self._exit()
                if event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        self._exit()
                # if event.type == MOUSEMOTION:
                #     print(player._is_on_screen())
            sprites.update()
            sprites.draw(self._screen)
            pygame.display.update()
    
    def _exit(self):
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    Euclides()