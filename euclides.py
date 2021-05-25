import pygame
from pygame import sprite
from pygame.locals import *
import math
import sys


SCREEN_SIZE = SCREEN_WIDTH, SCREEN_HEIGHT = (800, 600)
PLAYER_SIZE = 60
PLAYER_VERTICES = 3  # a triangle
PLAYER_START_POSITION = (SCREEN_WIDTH//2, SCREEN_HEIGHT-100)
PLAYER_PROJECTILE_SPEED = (0, -2)  # player projectiles move only upwards


class Polygon(sprite.Sprite):
    """All game objects in Euclides are regular polygons."""
    def __init__(self, size: int, n: int, hull: int=1) -> None:
        """Prepare a sprite containing the polygon.
        size:   size of containing surface (rectangular area as the polygon is regular)
        n:      number of vertices
        hull:   the polygon in the game can take this damage before destroying; projectiles take only one damage.
                Generally, polygons can take as much damage as their number of vertices."""
        super().__init__()
        self.radius = size // 2 # used by sprite.collide_circle as well
        self._n = n
        self._hull = hull
        self.image = pygame.Surface((size, size))
        pygame.draw.polygon(self.image, pygame.Color("white"), self._vertices(), 1)
         # to look like a starship or its projectile, turn upside down, so the triangle's tip shows upwards
         # this doesn't really matter in case of enemies and their bullets
        self.image = pygame.transform.rotate(self.image, 180)
        self.rect = self.image.get_rect()

    @property
    def n(self) -> int:
        """Return the number of vertices."""
        return self._n

    @property
    def is_destroyed(self) -> bool:
        """Return True if hull reduced below 1, otherwise False - the game object is still alive."""
        return self._hull < 1

    def reduce_hull(self) -> None:
        """Reduce the game object's hull by one."""
        self._hull -= 1

    def _vertices(self):
        """Calculate the vertices of the polygon.
        Returns:    a list of pair of coordinates"""
        angle = math.radians(360 / self.n)  # inner angle of polygon
        # 'radius +' means here that origin is in the rect's middle
        return [[int(self.radius + self.radius*math.sin(i*angle)), int(self.radius + self.radius*math.cos(i*angle))]\
            for i in range(0, self.n)]


class Player(Polygon):
    """Player is a regular triangle."""
    def __init__(self):
        """Initialize a triangle, representing a starfighter."""
        super().__init__(PLAYER_SIZE, PLAYER_VERTICES, hull=PLAYER_SIZE)
        self.rect.center = PLAYER_START_POSITION

    def update(self) -> None:
        """Update the player sprite."""
        self._keep_on_screen(*pygame.mouse.get_pos())

    def _keep_on_screen(self, x: int, y: int) -> None:
        """Always keep the whole player polygon on screen.
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


class Projectile(Polygon):
    """The player shoots triangle shaped projectiles."""
    def __init__(self, player: Polygon) -> None:
        """The projectile needs to know who fired it off, to get its size and shape.
        player: Player sprite"""
        super().__init__(player.rect.width // 4, player.n, 1)
        self._speed = PLAYER_PROJECTILE_SPEED
        self.rect.midbottom = player.rect.midtop  # projectile is fired off from tip of the triangle

    def update(self):
        self.rect.centerx += self._speed[0]
        self.rect.centery += self._speed[1]
        if self.rect.bottom < 0:  # kill projectile if it leaves the screen
            self.kill()


class Enemy(Polygon):
    """Enemies are rectangles, pentagons, hexagons etc."""
    def __init__(self, size: int, n: int) -> None:
        """Initialize an enemy, a size-ed, n-sided polygon."""
        super().__init__(size, n, hull=n)

    def update(self) -> None:
        self.rect.center = (400, 100)


class HullDamage(sprite.Group):
    """Custom sprite.Group to handle hull damage."""
    def __init__(self, *sprites: Polygon) -> None:
        """Uses default initialization.
        sprites:    any number of sprite objects"""
        super().__init__(*sprites)

    def update(self, *args, **kwargs) -> None:
        """Overriding default update to handle hull damage."""
        screen = kwargs.pop("screen", None)
        assert screen
        for poly in self.sprites():
            if poly.is_destroyed:
                poly.kill()
                self.clear(poly.image, screen)
        super().update()
        super().draw(screen)


class Euclides:
    """Main game application."""
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Euclides")
        self._screen = pygame.display.set_mode(SCREEN_SIZE)
        self._main()

    def _main(self) -> None:
        """Execute the application."""
        self._player = Player()
        pygame.mouse.set_pos(PLAYER_START_POSITION)
        player = HullDamage((self._player, ))
        self._projectiles = HullDamage()
        enemy = Enemy(80, 8)
        enemies = HullDamage((enemy, ))

        while self._player.alive():
            self._screen.fill((0, 0, 0))
            for event in pygame.event.get():
                if event.type == QUIT:  # exit by closing the window
                    self._exit()
                if event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        self._exit()
                if event.type == MOUSEBUTTONDOWN:
                    self._open_fire()

            player.update(screen=self._screen)

            for enemy_ in sprite.groupcollide(enemies, self._projectiles, False, True, sprite.collide_circle):
                enemy_.reduce_hull()
            self._projectiles.update(screen=self._screen)
            enemies.update(screen=self._screen)

            pygame.display.flip()

    def _open_fire(self):
        self._projectiles.add(Projectile(self._player))

    def _exit(self):
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    Euclides()