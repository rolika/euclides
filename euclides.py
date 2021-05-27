import pygame
from pygame import sprite
from pygame.time import Clock
from pygame.locals import *
import math
import sys


SCREEN_SIZE = SCREEN_WIDTH, SCREEN_HEIGHT = (800, 600)
PLAYER_SIZE = 60
PLAYER_VERTICES = 3  # a triangle
PLAYER_START_POSITION = (SCREEN_WIDTH//2, SCREEN_HEIGHT-100)
PLAYER_PROJECTILE_SPEED = (0, -2)  # player projectiles move only upwards
PI = math.pi


class Polygon(sprite.Sprite):
    """All game objects in Euclides are regular polygons."""
    def __init__(self, size:int, n:int, pos:tuple, hull:int=1, displacement:int=0, angle:float=0.0) -> None:
        """Prepare a sprite containing the polygon.
        size:           size of containing surface (rectangular area as the polygon is regular)
        n:              number of vertices
        pos:            tuple of x, y coordinates, where the polygon should apper (rect.center)
        hull:           the polygon in the game can take this damage before destroying; projectiles take only one
                        Generally, polygons can take as much damage as their number of vertices.
        displacement:   displacemnet in pixel
        angle:          shooting angle in radians"""
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
        self.rect.center = pos
        self._dx, self._dy = self._calculate_speed(displacement, angle)

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
    
    def _calculate_speed(self, displacement:int, angle:float) -> tuple:
        """Calculate speed as dx and dy coordinates.
        displacement:   displacemnet in pixel
        angle:          shooting angle in radians"""
        return displacement*math.cos(angle), displacement*math.sin(angle)


class Player(Polygon):
    """Player is a regular triangle."""
    def __init__(self, size:int, n:int, pos:tuple) -> None:
        """Initialize a triangle, representing a starfighter.
        size:   size of containing surface (rectangular area as the polygon is regular)
        n:      number of vertices"""
        super().__init__(size, n, pos, n)

    def update(self) -> None:
        """Update the player sprite."""
        self._keep_on_screen(*pygame.mouse.get_pos())

    def _keep_on_screen(self, x:int, y:int) -> None:
        """Always keep the whole player polygon on screen.
        x:  intended next horizontal center coordinate
        y:  intended next vertical center coordinate"""
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
    """The polygon shoots same shaped projectiles."""
    def __init__(self, owner:Polygon, displacement:int, angle:float) -> None:
        """The projectile needs to know who fired it off, to get its size and shape.
        owner:          player on enemy sprite
        displacement:   displacemnet in pixel
        angle:          shooting angle in radians"""
        super().__init__(owner.rect.width // 4, owner.n, owner.rect.center, 1, displacement, angle)

    def update(self) -> None:
        """Update the projectile sprite."""
        self.rect.centerx += self._dx
        self.rect.centery += self._dy
        if self.rect.bottom < 0:  # remove from group if it leaves the screen
            self.kill()


class Enemy(Polygon):
    """Enemies are rectangles, pentagons, hexagons etc."""
    def __init__(self, size:int, n:int, pos:tuple, displacement:int, angle:float) -> None:
        """Initialize an enemy polygon.
        size:           size of containing surface (rectangular area as the polygon is regular)
        n:              number of vertices
        pos:            tuple of x, y coordinates, where the polygon should apper (rect.center)
        displacement:   displacemnet in pixel
        angle:          shooting angle in radians"""
        super().__init__(size, n, pos, hull=n, displacement=displacement, angle=angle)

    def update(self) -> None:
        """Update the enemy sprite."""
        self.rect.centerx += self._dx
        self.rect.centery += self._dy
        self._keep_on_screen(*self.rect.center)

    def _keep_on_screen(self, x:int, y:int) -> None:
        """Always keep the whole enemy polygon on screen, bounce it off.
        x:  intended next horizontal center coordinate
        y:  intended next vertical center coordinate"""
        frame_left = frame_top = self.rect.width // 2
        frame_right = SCREEN_WIDTH - frame_left
        frame_bottom = SCREEN_HEIGHT - frame_top
        if x < frame_left or x > frame_right:
            self._dx *= -1
        if y < frame_top or y > frame_bottom:
            self._dy *= -1


class Wave(sprite.Group):
    """Custom sprite.Group to check on hull damage and convinient sprite update."""
    def __init__(self, *sprites:Polygon) -> None:
        """Uses default initialization.
        sprites:    any number of sprite objects"""
        super().__init__(*sprites)

    def handle(self, screen:pygame.Surface) -> None:
        """Handle sprites within the group.
        screen: game's display Surface"""
        for member in self.sprites():
            if member.is_destroyed:
                member.kill()  # remove from group
                self.clear(member.image, screen)  # overwrite with background
        super().update()
        super().draw(screen)

    def hit(self, hostile:sprite.Group) -> None:
        """Check if a projectile hits a hostile target.
        This should be called on projectile instance, as they'll be destoryed on collision.
        hostile:    wave of target sprite(s), precisely player or enemy"""
        for member in sprite.groupcollide(hostile, self, False, True, sprite.collide_circle):
            member.reduce_hull()
    
    def bounce(self, hostile:sprite.Group) -> None:
        """Check if player and enemy objects collide, reduce their hull and bounce them off of each other.
        This should be called on player instance, as they'll be bounced off.
        hostile:    wave of target sprite(s), precisely player or enemy"""
        for enemy, friendly in sprite.groupcollide(hostile, self, False, False, sprite.collide_circle).items():
            enemy.reduce_hull()
            for player in friendly:
                player.reduce_hull()
                dx = (enemy.rect.centerx - player.rect.centerx)/2 * -1
                dy = (enemy.rect.centery - player.rect.centery)/2 * -1
                pygame.mouse.set_pos(player.rect.centerx + dx, player.rect.centery + dy)


class Euclides:
    """Main game application."""
    def __init__(self) -> None:
        # initialize game objects
        pygame.init()
        pygame.display.set_caption("Euclides")
        self._main()

    def _main(self) -> None:
        """Execute the application."""
        screen = pygame.display.set_mode(SCREEN_SIZE)
        player = Player(PLAYER_SIZE, PLAYER_VERTICES, PLAYER_START_POSITION)
        pygame.mouse.set_pos(PLAYER_START_POSITION)
        friendly = Wave((player, ))
        friendly_fire = Wave()
        enemy = Enemy(80, 8, (400, 100), 8, PI/4)
        hostile = Wave((enemy, ))

        while player.alive():
            screen.fill((0, 0, 0))
            for event in pygame.event.get():
                if event.type == QUIT:  # exit by closing the window
                    self._exit()
                if event.type == KEYDOWN:
                    if event.key == K_ESCAPE:  # exit by pressing escape button
                        self._exit()
                if event.type == MOUSEBUTTONDOWN:  # open fire
                    friendly_fire.add(Projectile(player, 10, PI*1.5))

            # check collisions with hostile objects
            friendly_fire.hit(hostile)
            friendly.bounce(hostile)

            # update sprites
            friendly_fire.handle(screen)
            friendly.handle(screen)
            hostile.handle(screen)

            pygame.display.flip()
            Clock().tick(60)

    def _exit(self) -> None:
        """Nicely exit the game."""
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    Euclides()