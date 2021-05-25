import pygame
from pygame import sprite
from pygame.locals import *
import math
import sys
import enum


SCREEN_SIZE = SCREEN_WIDTH, SCREEN_HEIGHT = (800, 600)
PLAYER_SIZE = 60
PLAYER_VERTICES = 3  # a triangle
PLAYER_START_POSITION = (SCREEN_WIDTH//2, SCREEN_HEIGHT-100)
PLAYER_PROJECTILE_SPEED = (0, -2)  # player projectiles move only upwards


class Polygon(sprite.Sprite):
    """Draw a regular polygon inside a sprite."""
    def __init__(self, size: int, n: int, width: int=None) -> None:
        """Prepare a surface containing the polygon.
        size:   size of containing surface (rectangular area as the polygon is regular)
        n:      number of vertices
        width:  width of constructing lines"""
        super().__init__()
        self.radius = size // 2
        self._n = n
        self.image = pygame.Surface((size, size))
        if not width:
            width = n
        pygame.draw.polygon(self.image, pygame.Color("white"), self._vertices(), width)
         # turn upside down to look like a starship or its projectile (enemies and their bullets don't really matter)
        self.image = pygame.transform.rotate(self.image, 180)
        self.rect = self.image.get_rect()

    @property
    def n(self) -> int:
        return self._n

    def _vertices(self):
        """Calculate the vertices of the polygon.
        Returns:    a list of pair of coordinates"""
        angle = math.radians(360 / self.n)  # inner angle of polygon
        # 'radius +' means here that origin is in the rect's middle
        return [[int(self.radius + self.radius*math.sin(i*angle)), int(self.radius + self.radius*math.cos(i*angle))] for i in range(0, self.n)]


class Player(Polygon):
    """Player is a triangle."""
    def __init__(self):
        """Initialize a triangle, representing a starfighter."""
        super().__init__(PLAYER_SIZE, PLAYER_VERTICES)
        self.rect.center = PLAYER_START_POSITION

    def update(self):
        self._keep_on_screen(*pygame.mouse.get_pos())

    def _keep_on_screen(self, x, y) -> None:
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
    """The player can shoot projectiles."""
    def __init__(self, owner: Polygon) -> None:
        """The projectile needs to know who fired it off."""
        super().__init__(owner.rect.width // 4, owner.n, 1)
        self._speed = PLAYER_PROJECTILE_SPEED
        self.rect.center = owner.rect.center

    def update(self):
        self.rect.centerx += self._speed[0]
        self.rect.centery += self._speed[1]
        if self.rect.bottom < 0:
            self.kill()


class Enemy(Polygon):
    """Enemies are rectangles, pentagons, hexagons etc."""
    def __init__(self, size: int, n: int) -> None:
        """Initialize an enemy, a size-ed, n-sided polygon."""
        super().__init__(size, n)
        self._hull = n

    def update(self) -> None:
        if self._hull < 1:
            self.kill()
        else:
            self.rect.center = (400, 100)

    def reduce_hull(self) -> None:
        self._hull -= 1


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
        player_sprite = sprite.RenderPlain((self._player, ))
        self._projectile_sprites = sprite.RenderPlain()
        enemy = Enemy(80, 8)
        enemy_sprites = sprite.RenderPlain((enemy, ))
        bullet_sprites = sprite.RenderPlain()

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
                # if event.type == MOUSEMOTION:
                #     print(player._is_on_screen())

            player_sprite.update()
            player_sprite.draw(self._screen)

            self._projectile_sprites.update()
            self._projectile_sprites.draw(self._screen)

            if enemy_sprites:
                if sprite.spritecollide(enemy, self._projectile_sprites, True, sprite.collide_circle):
                    enemy.reduce_hull()
                enemy_sprites.update()
                enemy_sprites.draw(self._screen)

            bullet_sprites.update()
            bullet_sprites.draw(self._screen)

            pygame.display.flip()


    def _open_fire(self):
        self._projectile_sprites.add(Projectile(self._player))

    def _exit(self):
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    Euclides()