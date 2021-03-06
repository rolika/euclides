import tkinter
import pygame
from pygame import sprite
from pygame import time
from pygame import font
from pygame import mouse
from pygame import mixer
from pygame.locals import *
import math
import random
import shelve
import enum
import bisect
from tkinter import *
from tkinter import messagebox



PI = math.pi
START_TIME = time.get_ticks()

SCREEN_SIZE = SCREEN_WIDTH, SCREEN_HEIGHT = (800, 600)

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

FPS = 60

PLAYER_SIZE = 40
PLAYER_VERTICES = 3  # a triangle
PLAYER_START_POS = (SCREEN_WIDTH//2, SCREEN_HEIGHT-80)
PLAYER_PROJECTILE_SPEED = 15
WEAPON_COOLDOWN = 50  # player can fire at this rate (milliseconds)

ENEMY_STARTING_SIZE = 105
ENEMY_SIZE_DECREMENT = -5
ENEMY_STARTING_SPEED = 2.5
ENEMY_SPEED_INCREMENT = 0.5
ENEMY_STARTING_VERTICES = 4
ENEMY_PROJECTILE_STARTING_SPEED = 2
ENEMY_PROJECTILE_SPEED_INCREMENT = 1

SCORE_POS = (160, 10)
HISCORE_POS = (610, 10)
TITLE_POS = (400, 150)
SUBTITLE_POS = (400, 200)
GAME_OVER_POS = (400, 300)
NEWHI_POS = (400, 350)
FAME_POS = (400, 280)

SCORE_HULL_DAMAGE = 10  # multiplied by vertices of the enemy
SCORE_DESTROY_ENEMY = 100  # multiplied by vertices of the enemy

HOF_FILE = "halloffame"  # .db extension added by shelve
HOF_CHART = 10  # number of entries in the hall of fames
HOF_DEFAULT_NAME = "ROLI"
HOF_DEFAULT_SCORE = 1000


class State(enum.Enum):
    """Euclides game states"""
    QUIT = enum.auto()
    INTRO = enum.auto()
    PLAY = enum.auto()
    GAME_OVER = enum.auto()


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

        # setup sounds
        self._ship_damage_sound = mixer.Sound("wav/enemy_hull_damage.wav")
        self._ship_damage_sound.set_volume(0.5)
        self._ship_destroyed_sound = mixer.Sound("wav/explosion.wav")
        self._ship_destroyed_sound.set_volume(1)

    def damage(self) -> None:
        """Reduce hull by one."""
        self._hull -= 1
        self._ship_damage_sound.play()
        if self.is_destroyed:
            self._ship_destroyed_sound.play()
            self.kill()

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

    def update(self, *args, **kwargs) -> None:
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
        super().__init__(PLAYER_SIZE, PLAYER_VERTICES, PLAYER_START_POS)
        self._last_fire = START_TIME
        self._fires = False  # player fires continously

    @property
    def fires(self) -> bool:
        """Return true if player fires, otherwise false."""
        return self._fires

    @fires.setter
    def fires(self, state) -> None:
        """Set player's firing state.
        state:  boolean value"""
        self._fires = state

    def update(self, *args, **kwargs) -> None:
        """Update the player sprite. The ship is controlled by mouse movement by its center point."""
        state = kwargs.pop("state", None)
        if state == State.PLAY:
            self._keep_on_screen(*mouse.get_pos())

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

    def set_last_fire(self) -> None:
        """Set timer for weapon cooldown."""
        self._last_fire = time.get_ticks()

    def reset(self) -> None:
        """When player restarts the game."""
        self._hull = PLAYER_VERTICES
        self.rect.center = PLAYER_START_POS

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

    def update(self, *args, **kwargs) -> None:
        """Update the projectile sprite."""
        self.rect.centerx += self._dx
        self.rect.centery += self._dy
        # remove from group if it leaves the screen
        if self.rect.centerx < 0 or self.rect.centerx > SCREEN_WIDTH or\
            self.rect.centery < 0 or self.rect.centery > SCREEN_HEIGHT:
            self.kill()


class PlainText(sprite.Sprite):
    """Handle on-screen texts as sprites."""
    def __init__(self, font_name, font_size, text, font_color, pos) -> None:
        """Initialize a sprite object.
        font_name:  name of font including its path as string
        font_size:  size in pixels
        text:       text to be displayed
        font_color: use this color to render the text
        pos:        center coordinates"""
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
        return self.image.get_rect(center=self._pos)


class Score(PlainText):
    """Handle score as sprite."""
    def __init__(self, font_name, font_size, font_color, pos) -> None:
        """Initialize a sprite object.
        font_name:  name of font including its path as string
        font_size:  size in pixels
        font_color: use this color to render the text
        pos:        center coordinates"""
        super().__init__(font_name, font_size, "", font_color, pos)

    def update(self, *args, **kwargs):
        """Update the text."""
        score = kwargs.get("score", None)
        self._text = self._format("score", score)

    def _format(self, score_text, score) -> str:
        return score_text + " {:07}".format(score if score else 0)


class HiScore(Score):
    """Handle hiscore as sprite."""
    def __init__(self, font_name, font_size, font_color, pos) -> None:
        """Initialize a sprite object.
        font_name:  name of font including its path as string
        font_size:  size in pixels
        font_color: use this color to render the text
        pos:        center coordinates"""
        super().__init__(font_name, font_size, font_color, pos)

    def update(self, *args, **kwargs):
        """Update the text."""
        score = kwargs.get("hiscore", None)
        self._text = self._format("hiscore", score)


class UIButton(PlainText):
    """Button-like user interface."""
    def __init__(self, font_name, font_size, text, font_color, pos, action) -> None:
        self._action = action
        self._mouse_over = False
        highlighted_font = font.Font(font_name, font_size*2)
        self._highlighted_image = highlighted_font.render(text, True, font_color)
        self._highlighted_rect = self._highlighted_image.get_rect(center=pos)
        super().__init__(font_name, font_size, text, font_color, pos)

    @property
    def image(self):
        return self._highlighted_image if self._mouse_over else super().image

    @property
    def rect(self):
        return self._highlighted_rect if self._mouse_over else super().rect

    def update(self, *args, **kwargs):
        mouse_pos = kwargs.pop("mouse_pos", None)
        assert mouse_pos
        if self.rect.collidepoint(mouse_pos):
            self._mouse_over = True
        else:
            self._mouse_over = False


class OnScreen(sprite.RenderUpdates):
    """Container for on-screen sprite objects."""
    def __init__(self, *sprites:Polygon) -> None:
        """Uses default initialization.
        sprites:    any number of sprite objects"""
        super().__init__(*sprites)

    def update(self, *args, **kwargs) -> None:
        """Handle sprites within the group.
        screen: game's display Surface"""
        screen = kwargs.pop("screen", None)
        assert screen
        changed = self.draw(screen)
        super().update(*args, **kwargs)
        return changed


class Wave(OnScreen):
    """Sprite container for enemies."""
    def __init__(self, *sprites:Enemy) -> None:
        """Uses default initialization.
        sprites:    any number of sprite objects"""
        super().__init__(*sprites)
        self.reset()

    @property
    def score(self) -> int:
        """Return the waves calculated score."""
        return self._score

    def increase_score(self, value:int) -> None:
        """Increase enemy wave's score.
        value:  damaged or destoryed score increment"""
        self._score += value

    def contact(self, player:sprite.Sprite):
        """Detect collision between player and enemy polygons and reduce their hull.
        player:     player sprite"""
        for enemy in sprite.spritecollide(player, self, False, sprite.collide_circle):
            player.knockback(enemy)
            enemy.damage()
            player.damage()

    def reset(self):
        """When player restarts the game."""
        self._score = 0
        self.empty()


class Storm(OnScreen):
    """Sprite container for projectiles."""
    def __init__(self, *sprites:Enemy) -> None:
        """Uses default initialization.
        sprites:    any number of sprite objects"""
        super().__init__(*sprites)

    def hit(self, enemies:Wave) -> None:
        """Detect collision between projectiles and enemies.
        Colliding projectiles get killed off (dokill2=True).
        spaceship:  enemies"""
        for member in sprite.groupcollide(enemies, self, False, True, sprite.collide_circle):
            member.damage()
            enemies.increase_score(SCORE_HULL_DAMAGE * member.n)
            if member.is_destroyed:
                enemies.increase_score(SCORE_DESTROY_ENEMY * member.n)


class Pilot:
    """Entry for the hall of fames."""
    def __init__(self, name, score):
        self._name = name.upper()[:4]  # all names 4 uppercased characters
        self._score = score

    def __str__(self):
        """Return a formatted representation of the entry."""
        return "{name:.<10}{score:07}".format(name=self._name, score=self._score)

    def __lt__(self, other):
        """Rich comparison for bisecting.
        other:  other Pilot"""
        return self._score < other.score

    @property
    def score(self) -> int:
        """Return score value."""
        return self._score


class HallOfFame:
    """The hall of fame contains the best hi-scores."""
    def __init__(self, filename:str) -> None:
        """Initialize the hall of fame.
        filename:       path to shelve file"""
        self._filename = filename
        self._hof = []  # list of Pilots

    def __str__(self):
        """Return the string representation, each entry in a new line."""
        return "\n".join(map(str, self._hof[::-1]))

    @property
    def hof(self):
        """Return the hall of fame as an iterable in reversed order."""
        return self._hof[::-1]

    @property
    def hiscore(self) -> int:
        """Return the actual hiscore."""
        return self._hof[HOF_CHART-1].score

    def restore(self) -> None:
        """Restore hall of fame from shelve."""
        with shelve.open(self._filename) as hof:
            for i in range(HOF_CHART):
                entry = hof.get(str(i), None)
                if entry is None:
                    self._hof.append(Pilot(HOF_DEFAULT_NAME, HOF_DEFAULT_SCORE))
                else:
                    self._hof.append(entry)

    def insert(self, entry:Pilot) -> None:
        """Insert a new entry into the hall of fame.
        entry:  Pilot object"""
        bisect.insort_left(self._hof, entry)
        self._hof = self._hof[1:HOF_CHART+1]  # always get rid of the lowest value after insertion
        self._save()

    def is_new_hiscore(self, score:int) -> bool:
        """Return True if this is a new hi-score.
        score:  score to compare"""
        return score > self.hiscore

    def is_eligible(self, score:int) -> bool:
        """Return True if this score is eligible to enter the hall of fame.
        score:  score to compare"""
        return score > self._hof[0].score

    def _save(self) -> None:
        """Write hall of fame to shelve."""
        with shelve.open(self._filename) as hof:
            for i in range(HOF_CHART):
                hof[str(i)] = self._hof[i]


class NameEntryDialog(Frame):
    """Tkinter dialog box to enter a name."""
    def __init__(self, parent=None) -> None:
        """Init wiht a parent widget.
        parent: widget"""
        super().__init__(parent, bg="black")
        self.master.title("Euclides")
        self._pilot_name = StringVar()
        self._validated_name = HOF_DEFAULT_NAME
        self.body()
        self.pack()

    @property
    def pilot_name(self):
        """Return the entered name."""
        return self._validated_name

    def body(self):
        """Display the dialog."""
        Label(self, text="Enter your name, Pilot!", bg="black", fg="white").pack()
        entry = Entry(self, textvariable=self._pilot_name, width=30, bg="black", fg="white")
        entry.bind("<KeyPress-KP_Enter>", self.apply)
        entry.bind("<KeyPress-Return>", self.apply)
        entry.pack()
        Button(self, text="OK", width=12, command=self.apply, bg="black", fg="white").pack(side=LEFT)
        Button(self, text="Cancel", width=12, command=self.quit, bg="black", fg="white").pack()
        entry.focus_set()

    def validate(self):
        """Validate user's entry."""
        name = self._pilot_name.get().upper()[:4]
        if name:
            self._validated_name = name
        return messagebox.askokcancel("Are you sure?", "{} will be shown.".format(self._validated_name), parent=self)

    def apply(self, event=None):
        """Validate and quit."""
        if self.validate():
            self.quit()


class Euclides:
    """Main game application."""
    def __init__(self) -> None:
        # initialize game objects
        random.seed()
        pygame.init()
        mixer.set_num_channels(64)  # continous fire alone needs 20
        pygame.display.set_caption("Euclides")

        # restore hall of fame
        self._hall_of_fame = HallOfFame(HOF_FILE)
        self._hall_of_fame.restore()
        self._hiscore = self._hall_of_fame.hiscore

        # setup player
        self._player = Player()

        # setup scores
        self._score = Score("font/Monofett-Regular.ttf", 40, WHITE, SCORE_POS)
        self._highscore = HiScore("font/Monofett-Regular.ttf", 40, WHITE, HISCORE_POS)

        # setup sprite groups
        self._fire = Storm()  # container for player's projectiles
        self._hostile = Wave()  # container for enemy spacecrafts
        self._onscreen = OnScreen()  # container for sprites on screen

        self._main()

    def _main(self) -> None:
        """Execute the application."""
        # setup display
        screen = pygame.display.set_mode(SCREEN_SIZE)

        #setup initial state
        state = State.INTRO

        while True:
            if state == State.INTRO:
                state = self._intro(screen)

            if state == State.PLAY:
                state = self._play(screen)

            if state == State.GAME_OVER:
                state = self._end(screen)

            if state == State.QUIT:
                pygame.quit()
                return

    def _set_screen(self, *args) -> None:
        """Set game screen, containers etc.
        args:   screen elements (sprites, containers)"""
        self._onscreen.empty()
        self._player.reset()
        self._fire.empty()
        self._hostile.reset()
        self._onscreen.add(*args)

    def _intro(self, screen) -> State:
        """Show game title screen.
        screen: pygame display"""
        title = PlainText("font/RubikMonoOne-Regular.ttf", 60, "EUCLIDES", WHITE, TITLE_POS)
        subtitle = PlainText("font/ShareTechMono-Regular.ttf", 30, "a geometric shooter", WHITE, SUBTITLE_POS)
        fame = PlainText("font/ShareTechMono-Regular.ttf", 24, "Hall of Fame", WHITE, FAME_POS)
        hall = OnScreen()
        for i, entry in enumerate(self._hall_of_fame.hof):
            hall.add(PlainText("font/ShareTechMono-Regular.ttf", 18, str(entry), WHITE, (400, 320+i*18)))
        self._set_screen(self._score, self._highscore, title, subtitle, fame, hall, self._player)

        while True:
            screen.fill(BLACK)

            for event in pygame.event.get():
                if event.type == QUIT:  # exit by closing the window
                    return State.QUIT
                if event.type == KEYDOWN:
                    if event.key == K_ESCAPE:  # exit by pressing escape button
                        return State.QUIT
                if event.type == MOUSEBUTTONUP and self._player.rect.collidepoint(mouse.get_pos()):
                    return State.PLAY

            changed = self._onscreen.update(screen=screen, state=State.INTRO, hiscore=self._hiscore)
            pygame.display.update(changed)

    def _play(self, screen) -> State:
        """Play the game.
        screen: pygame display"""
        self._set_screen(self._score, self._highscore, self._player, self._fire, self._hostile)

        size = ENEMY_STARTING_SIZE
        n = 3
        speed = ENEMY_STARTING_SPEED

        # setup sounds
        shot_sound = mixer.Sound("wav/gunshot.wav")
        shot_sound.set_volume(0.25)

        while True:
            time.Clock().tick(FPS)
            screen.fill(BLACK)

            # listen for user actions
            for event in pygame.event.get():
                if event.type == QUIT:  # exit by closing the window
                    return State.QUIT
                if event.type == KEYDOWN:
                    if event.key == K_ESCAPE:  # exit by pressing escape button
                        return State.QUIT
                if event.type == MOUSEBUTTONDOWN:
                    self._player.fires = True  # open fire
                if event.type == MOUSEBUTTONUP:
                    self._player.fires = False  # cease fire

            # setup enemy wave
            if not bool(self._hostile):
                size += ENEMY_SIZE_DECREMENT
                n += 1
                speed += ENEMY_SPEED_INCREMENT
                for i in range(n):
                    x = random.randrange(0, SCREEN_WIDTH, 1)
                    y = random.randrange(0, SCREEN_HEIGHT // 2, 1)
                    angle = math.radians(random.randrange(315, 345, 1))
                    self._hostile.add(Enemy(size, n, (x, y), speed, angle))
                self._onscreen.add(self._hostile)

            # shoot player projectiles
            if self._player.is_ready_to_fire() and self._player.fires:
                self._fire.add(Projectile(self._player, PLAYER_PROJECTILE_SPEED, PI*1.5))
                self._onscreen.add(self._fire)
                self._player.set_last_fire()
                shot_sound.play()

            # check whether player's projectile hits an enemy
            self._fire.hit(self._hostile)

            # check player collisions with enemy craft
            self._hostile.contact(self._player)

            # check if player is still alive
            if not self._player.alive():
                return State.GAME_OVER

            # update sprites
            changed = self._onscreen.update(screen=screen,
                                            state=State.PLAY,
                                            score=self._hostile.score,
                                            hiscore=max(self._hostile.score, self._hiscore))
            pygame.display.update(changed)

    def _end(self, screen) -> State:
        """Show game over screen.
        screen: pygame display"""
        game_over = UIButton("font/RubikMonoOne-Regular.ttf", 40, "GAME OVER", WHITE, GAME_OVER_POS, State.INTRO)
        score = self._hostile.score
        self._set_screen(self._score, self._highscore, game_over)
        text = None
        if self._hall_of_fame.is_new_hiscore(score):
            text = PlainText("font/ShareTechMono-Regular.ttf", 30, "A new hi-score!", WHITE, NEWHI_POS)
            self._hiscore = score
        elif self._hall_of_fame.is_eligible(score):
            text = PlainText("font/ShareTechMono-Regular.ttf", 30, "A new entry to the hall of fame!", WHITE, NEWHI_POS)
        if text:
            self._onscreen.add(text)

        while True:
            screen.fill(BLACK)

            for event in pygame.event.get():
                if event.type == QUIT:  # exit by closing the window
                    return State.QUIT
                if event.type == KEYDOWN:
                    if event.key == K_ESCAPE:  # exit by pressing escape button
                        return State.QUIT
                if event.type == MOUSEBUTTONUP and game_over.rect.collidepoint(mouse.get_pos()):
                    if text:
                        self._enter_name(score)
                    return State.INTRO

            changed = self._onscreen.update(screen=screen,
                                            score=score,
                                            hiscore=self._hiscore,
                                            mouse_pos=mouse.get_pos())
            pygame.display.update(changed)

    def _enter_name(self, score):
        """Enter a name and save to database.
        score:  player's last score"""
        tk_root = tkinter.Tk()
        entry = NameEntryDialog(tk_root)
        tk_root.mainloop()
        tk_root.destroy()
        self._hall_of_fame.insert(Pilot(entry.pilot_name, score))


if __name__ == "__main__":
    Euclides()
