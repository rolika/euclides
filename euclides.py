import pygame
from pygame import sprite
from pygame import time
from pygame import font
from pygame.locals import *
import math
import sys
import random
import shelve


PI = math.pi
START_TIME = time.get_ticks()

SCREEN_SIZE = SCREEN_WIDTH, SCREEN_HEIGHT = (800, 600)

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

FPS = 60

PLAYER_SIZE = 40
PLAYER_VERTICES = 3  # a triangle
PLAYER_START_POSITION = (SCREEN_WIDTH//2, SCREEN_HEIGHT-100)
PLAYER_PROJECTILE_SPEED = 15
WEAPON_COOLDOWN = 50  # player can fire at this rate (milliseconds)

ENEMY_STARTING_SIZE = 100
ENEMY_SIZE_INCREMENT = -5
ENEMY_STARTING_SPEED = 3
ENEMY_SPEED_INCREMENT = 0.5
ENEMY_STARTING_VERTICES = 4
ENEMY_PROJECTILE_STARTING_SPEED = 2
ENEMY_PROJECTILE_SPEED_INCREMENT = 1

SCORE_COORDS = (10, 10)
HISCORE_COORDS = (440, 10)
SCORE_HULL_DAMAGE = 10  # multiplied by vertices of the enemy
SCORE_DESTROY_ENEMY = 100  # multiplied by vertices of the enemy


class Trig:
    """Collection of trigonometric methods."""

    def vertices(n, r) -> list:
        """Calculate the vertices of the polygon.
        n:  number of vertices
        r:  radius of circle inside the rectangle"""
        angle = math.radians(360 / n)  # inner angle of polygon
        # 'r +' means here that origin is the rectangle's middlepoint
        return [[int(r + r*math.sin(i*angle)), int(r + r*math.cos(i*angle))] for i in range(0, n)]

    def offset(displacement:int, angle:float) -> tuple:
        """Calculate delta x and delta y offset coordinates.
        displacement:   displacement in pixel
        angle:          angle in radians"""
        return math.ceil(displacement*math.cos(angle)), math.ceil(displacement*math.sin(angle))


class Polygon(sprite.Sprite):
    """All game objects in Euclides are regular polygons.
    This class has nothing else to do as to draw a certain sized and verticed regular polygon."""
    def __init__(self, size:int, n:int, pos:tuple) -> None:
        """Prepare a sprite containing the polygon.
        size:           size of containing surface (rectangular area as the polygon is regular)
        n:              number of vertices
        pos:            tuple of x, y coordinates, where the polygon should apper (rect.center)"""
        super().__init__()
        self.radius = size // 2 # used by sprite.collide_circle as well
        self._n = n
        self.image = pygame.Surface((size, size))
        pygame.draw.polygon(self.image, WHITE, Trig.vertices(n, self.radius), 1)
         # to look like a starship or its projectile, turn upside down, so the player's triangle's tip shows upwards
         # this doesn't really matter in case of enemies and their bullets
        self.image = pygame.transform.rotate(self.image, 180)
        self.image.set_colorkey(self.image.get_at((0, 0)))
        self.rect = self.image.get_rect()
        self.rect.center = pos

    @property
    def n(self) -> int:
        """Return the number of vertices."""
        return self._n


class Spaceship(Polygon):
    """Spaceships represent the player and its enemies in the game.
    Ships have a hull attribute, which can be degraded through collision with an other spaceship or by having shot
    with a projectile. Generally, the spaceship's hull value is the same as its polygon's vertices."""
    def __init__(self, size: int, n: int, pos:tuple) -> None:
        """Prepare a sprite containing the polygon.
        size:           size of containing surface (rectangular area as the polygon is regular)
        n:              number of vertices
        pos:            tuple of x, y coordinates, where the polygon should apper (rect.center)"""
        super().__init__(size, n, pos)
        self._hull = n

    def damage(self) -> None:
        """Reduce hull by one."""
        self._hull -= 1

    @property
    def is_destroyed(self) -> bool:
        """Return True if hull reduced below 1 (ship is destroyed), otherwise False (ship is still alive)."""
        return self._hull < 1


class Enemy(Spaceship):
    """Enemies are regular polygons above triangles: rectangles, pentagons, hexagons etc."""
    def __init__(self, size:int, n:int, pos:tuple, displacement:int, angle:float) -> None:
        """Initialize an enemy polygon.
        size:           size of containing surface (rectangular area as the polygon is regular)
        n:              number of vertices
        pos:            tuple of x, y coordinates, where the polygon should apper (rect.center)
        displacement:   displacement in pixel
        angle:          beginning moving angle in radians"""
        super().__init__(size, n, pos)
        self._dx, self._dy = Trig.offset(displacement, angle)  # enemies move right away after spawning

    def update(self) -> None:
        """Update the enemy sprite."""
        self._keep_on_screen()
        self.rect.centerx += self._dx
        self.rect.centery += self._dy

    def turn_dx(self) -> None:
        """Turn around horizontal movement."""
        self._dx = -self._dx

    def turn_dy(self) -> None:
        """Turn around vertical movement."""
        self._dy = -self._dy

    def _keep_on_screen(self) -> None:
        """Always keep the whole enemy polygon on screen, by bouncing it off at screen edges."""
        if self.rect.left < 0:
            self.rect.left = 0
            self.turn_dx()
        if self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH - 1
            self.turn_dx()
        if self.rect.top < 0:
            self.rect.top = 0
            self.turn_dy()
        if self.rect.bottom > SCREEN_HEIGHT:
            self.rect.bottom = SCREEN_HEIGHT - 1
            self.turn_dy()


class Player(Spaceship):
    """Player is represented by a regular triangle-shaped spaceship."""
    def __init__(self) -> None:
        """Initialize a triangle, representing the player."""
        super().__init__(PLAYER_SIZE, PLAYER_VERTICES, PLAYER_START_POSITION)
        # make sure player is vulnerable (invulnerability is always cooled down, since start time is almost 0)
        self._last_fire = START_TIME
        self._fires = False  # player fires continously

    @property
    def fires(self) -> bool:
        return self._fires

    @fires.setter
    def fires(self, state) -> None:
        self._fires = state

    def update(self) -> None:
        """Update the player sprite. The ship is controlled by mouse movement by its center point."""
        self._keep_on_screen(*pygame.mouse.get_pos())

    def set_last_fire(self) -> None:
        """Set timestamp of last hit."""
        self._last_fire = time.get_ticks()

    def knockback(self, enemy:Enemy):
        """Player and enemies shouldn't overlap each other, because their hull gets too fast exhausted from collision.
        This method knocks back the enemy sprite avoiding overlapping.
        enemy: Enemy sprite"""
        overlap = None
        if self.rect.top < enemy.rect.bottom:  # player is below
            overlap = enemy.rect.bottom - self.rect.top
            enemy.rect.bottom += overlap
        if self.rect.left < enemy.rect.right:  # player is on right
            overlap = enemy.rect.right - self.rect.left
            enemy.rect.right += overlap
        if self.rect.bottom > enemy.rect.top:  # player is above
            overlap = self.rect.bottom - enemy.rect.top
            enemy.rect.top -= overlap
        if self.rect.right > enemy.rect.left:  # player is on left
            overlap = self.rect.right - enemy.rect.left
            enemy.rect.left -= overlap
        if overlap:
            enemy.turn_dy()
            enemy.turn_dx()

    def is_ready_to_fire(self) -> bool:
        """Check player's ability to fire."""
        now = time.get_ticks()
        time_since_last_fire = now - self._last_fire
        return time_since_last_fire >= WEAPON_COOLDOWN

    def _keep_on_screen(self, x:int, y:int) -> None:
        """Always keep the whole player polygon on screen.
        x:  intended next horizontal center coordinate
        y:  intended next vertical center coordinate"""
        edge_left = edge_top = self.rect.width // 2
        edge_right = SCREEN_WIDTH - edge_left
        edge_bottom = SCREEN_HEIGHT - edge_top
        if x < edge_left:
            x = edge_left
        if x > edge_right:
            x = edge_right
        if y < edge_top:
            y = edge_top
        if y > edge_bottom:
            y = edge_bottom
        self.rect.center = (x, y)


class Projectile(Polygon):
    """The polygon shoots same shaped projectiles."""
    def __init__(self, owner:Polygon, speed:int, angle:float) -> None:
        """The projectile needs to know who fired it off, to get its size and shape.
        owner:  player on enemy sprite
        speed:  displacement in pixel
        angle:  shooting angle in radians"""
        super().__init__(owner.rect.width // 4, owner.n, owner.rect.center)
        self._dx, self._dy = Trig.offset(speed, angle)  # projectiles move right away after spawning

    def update(self) -> None:
        """Update the projectile sprite."""
        self.rect.centerx += self._dx
        self.rect.centery += self._dy
        # remove from group if it leaves the screen
        if self.rect.centerx < 0 or self.rect.centerx > SCREEN_WIDTH or\
            self.rect.centery < 0 or self.rect.centery > SCREEN_HEIGHT:
            self.kill()


class Wave(sprite.RenderUpdates):
    """Custom sprite.RenderUpdates to check on player and enemy hull damage and convinient sprite update."""
    def __init__(self, *sprites:Polygon) -> None:
        """Uses default initialization.
        sprites:    any number of sprite objects"""
        super().__init__(*sprites)
        self._score = 0

    @property
    def score(self) -> int:
        """For simplicity, score is calculated for every wave, but only that of enemies will be evaulated."""
        return self._score

    def handle(self, screen:pygame.Surface) -> None:
        """Handle sprites within the group.
        screen: game's display Surface"""
        for member in self.sprites():
            # getattr is needed, because Projectile doesn't have the is_destroyed() method.
            if getattr(member, "is_destroyed", None):
                self._score += SCORE_DESTROY_ENEMY * member.n
                member.kill()  # remove from group
        changed = self.draw(screen)
        self.update()
        return changed

    def contact(self, hostile:sprite.RenderUpdates):
        """Detect collision between player and enemy polygons and reduce their hull.
        This method should be called on the player instance with the enemy wave as argument.
        hostile:    wave of enemy sprites"""
        detected = sprite.RenderUpdates()
        for player, enemies in sprite.groupcollide(self, hostile, False, False, sprite.collide_circle).items():
            for enemy in enemies:
                player.knockback(enemy)
            detected.add(player)
            detected.add(*enemies)
        for member in detected.sprites():
            member.damage()

    def hit_by(self, projectiles:sprite.RenderUpdates) -> None:
        """Detect collision between projectiles and their spaceship target.
        This method should be called on the enemy instance with projectiles as argument.
        Colliding projectiles get killed off (dokill2=True).
        projectile: wave of projectiles"""
        for member in sprite.groupcollide(self, projectiles, False, True, sprite.collide_circle):
            member.damage()
            self._score += SCORE_HULL_DAMAGE * member.n


class Text(sprite.Sprite):
    """Handle on-screen texts as sprites."""
    def __init__(self, font_name, font_size, text, font_color, pos) -> None:
        """Initialize a sprite object.
        font_name:  name of font including its path as string
        font_size:  size in pixels
        text:       text to be displayed
        font_color: use this color to render the text
        pos:        topleft coordinates"""
        self._font = font.Font(font_name, font_size)
        self._text = text
        self._font_color = font_color
        self._pos = pos
        super().__init__()

    @property
    def image(self) -> pygame.Surface:
        """Return the text's surface."""
        return self._font.render(self._text, True, self._font_color)

    @property
    def rect(self) -> pygame.Rect:
        """Return the text's rect."""
        return self.image.get_rect(topleft=self._pos)

    def update(self, text):
        """Update the text.
        text:   text as string"""
        self._text = text

    def draw(self, screen):
        """Draw text on screen.
        screen: display surface"""
        screen.blit(self.image, self.rect)


class Euclides:
    """Main game application."""
    def __init__(self) -> None:
        # initialize game objects
        random.seed()
        pygame.init()
        pygame.display.set_caption("Euclides")

        with shelve.open("hiscore") as hsc:
            self._hiscore = hsc.get("hiscore", 0)

        self._main()

    def _main(self) -> None:
        """Execute the application."""

        # setup display
        screen = pygame.display.set_mode(SCREEN_SIZE)

        # setup player
        player = Player()
        pygame.mouse.set_pos(PLAYER_START_POSITION)

        # setup scores
        score = Text("font/Monofett-Regular.ttf", 40, "score: {:07}".format(0), WHITE, SCORE_COORDS)
        hiscore = Text("font/Monofett-Regular.ttf", 40, "hiscore: {:07}".format(self._hiscore), WHITE, HISCORE_COORDS)
        scores = sprite.RenderUpdates(score, hiscore)

        # setup sprite groups
        friendly = Wave((player, ))
        friendly_fire = Wave()
        hostile = Wave()

        # setup first enemy wave
        size = ENEMY_STARTING_SIZE
        n = 4  # enemy wave (number of enemies & number of vertices)
        speed = ENEMY_STARTING_SPEED
        self._spawn_enemy_wave(hostile, size, n, speed)

        # main game loop
        while player.alive():

            time.Clock().tick(FPS)
            screen.fill(BLACK)

            # listen for user actions
            for event in pygame.event.get():
                if event.type == QUIT:  # exit by closing the window
                    self._exit(hostile.score)
                if event.type == KEYDOWN:
                    if event.key == K_ESCAPE:  # exit by pressing escape button
                        self._exit(hostile.score)
                if event.type == MOUSEBUTTONDOWN:  # open fire
                    player.fires = True
                if event.type == MOUSEBUTTONUP:  # cease fire
                    player.fires = False

            # shoot player projectiles
            if player.is_ready_to_fire() and player.fires:
                friendly_fire.add(Projectile(player, PLAYER_PROJECTILE_SPEED, PI*1.5))
                player.set_last_fire()

            # spawn new enemy wave when the former is destroyed
            if not bool(hostile):
                size += ENEMY_SIZE_INCREMENT
                n += 1
                speed += ENEMY_SPEED_INCREMENT
                self._spawn_enemy_wave(hostile, size, n, speed)

            # check whether player's projectile hits an enemy
            hostile.hit_by(friendly_fire)
            # check player collisions with enemy craft
            friendly.contact(hostile)

            # update score
            score.update("score: {:07}".format(hostile.score))

            # update hi-score
            actual_hiscore = self._hiscore if hostile.score <= self._hiscore else hostile.score
            hiscore.update("hiscore: {:07}".format(actual_hiscore))

            # update sprites
            changed = friendly.handle(screen) + friendly_fire.handle(screen) + hostile.handle(screen)\
                + scores.draw(screen)

            pygame.display.update(changed)

        self._exit(hostile.score)

    def _spawn_enemy_wave(self, wave:Wave, size: int, n:int, speed:int) -> None:
        """Spawn a new enemy wave.
        wave:   sprite container for enemies
        size:   enemy size in pixels
        n:      number of vertices
        speed:  displacement in pixels"""
        for i in range(n):
            x = random.randrange(0, SCREEN_WIDTH, 1)
            y = random.randrange(0, SCREEN_HEIGHT // 2, 1)
            angle = math.radians(random.randrange(315, 345, 1))
            wave.add(Enemy(size, n, (x, y), speed, angle))

    def _exit(self, score:int) -> None:
        """Nicely exit the game.
        score:  last achieved score"""
        print("Last Euclides score:", score)
        # save new hi-score
        if score > self._hiscore:
            print("It's a new hi-score!")
            with shelve.open("hiscore") as hsc:
                hsc["hiscore"] = score
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    Euclides()
