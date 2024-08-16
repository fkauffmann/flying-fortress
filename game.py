#!/usr/bin/env python
# -*- coding: utf-8 -*-

#################################################################
# "Flying Fortress"
# Another tiny vertical scroller game made with Python and pygame 
#
# History
#
# * 2024.08.12 - initial version
# * 2024.08.14 - difficulty level handling
# * 2024.08.15 - energy bar added
# * 2024.08.16 - parallax scrolling added
#################################################################

import random
import sys

import pygame

X_MAX = 1400
Y_MAX = 900

BACKGROUND_COLOR = (35,138,205)

LEFT, RIGHT, UP, DOWN = 0, 1, 3, 4
START, STOP = 0, 1
MIN_ENEMIES = 5
MAX_ENEMIES = MIN_ENEMIES
LEVEL = 1
LEVEL_TIME = 30
FRAMERATE = 30

everything = pygame.sprite.Group()

class Explosion(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super(Explosion, self).__init__()
        sheet = pygame.image.load("./assets/explosions.png")
        self.images = []
        for i in range(0, 768*2, 48*2):
            rect = pygame.Rect((i, 0, 48*2, 48*2))
            image = pygame.Surface(rect.size, pygame.SRCALPHA, 32)
            image.convert_alpha()
            image.blit(sheet, (0, 0), rect)
            self.images.append(image)

        self.image = self.images[0]
        self.index = 0
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.add(everything)

    def update(self):
        self.image = self.images[self.index]
        self.index += 1
        if self.index >= len(self.images):
            self.kill()


class Island(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super(Island, self).__init__()
        land_type = random.randint(1,4)

        original_image = pygame.image.load("./assets/island" + str(land_type) + ".png").convert_alpha()
        self.image = pygame.transform.scale(original_image.copy(), (128,128))
        self.image.fill((255,255,255,150), None, pygame.BLEND_RGBA_MULT)
        self.rect = self.image.get_rect()
        self.rect.center = (x,y)        
        self.velocity = 1
        self.size = 1
        self.colour = 128

    def update(self):
        x, y = self.rect.center
        if self.rect.center[1] > Y_MAX+64:
            self.rect.center = (x, -64)
        else:
            self.rect.center = (x, y + self.velocity)

class Cloud(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super(Cloud, self).__init__()

        self.image = pygame.image.load("./assets/cloud.png").convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.center = (x,y)        
        self.velocity = 2
        self.size = 1
        self.colour = 128

    def update(self):
        x, y = self.rect.center
        if self.rect.center[1] > Y_MAX+64:
            self.rect.center = (x, -64)
        else:
            self.rect.center = (x, y + self.velocity)


class BulletSprite(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super(BulletSprite, self).__init__()
        self.image = pygame.Surface((10, 10))
        for i in range(5, 0, -1):
            color = 255.0 * float(i)/5
            pygame.draw.circle(self.image,
                               (color, color, 0),
                               (5, 5),
                               i,
                               0)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y-25)

    def update(self):
        x, y = self.rect.center
        y -= 20
        self.rect.center = x, y
        if y <= 0:
            self.kill()


class EnemySprite(pygame.sprite.Sprite):
    def __init__(self, x_pos, groups):
        super(EnemySprite, self).__init__()
        self.image = pygame.image.load("./assets/enemy.png").convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.center = (x_pos, 0)

        self.velocity = random.randint(3, 10)

        self.add(groups)
        self.explosion_sound = pygame.mixer.Sound("./assets/explosion.wav")
        self.explosion_sound.set_volume(0.4)

    def update(self):
        x, y = self.rect.center

        if y > Y_MAX:
            x, y = random.randint(0, X_MAX), 0
            self.velocity = random.randint(3, 10)
        else:
            x, y = x, y + self.velocity

        self.rect.center = x, y

    def kill(self):
        x, y = self.rect.center
        if pygame.mixer.get_init():
            self.explosion_sound.play(maxtime=1000)
            Explosion(x, y)
        super(EnemySprite, self).kill()

class PlayerSprite(pygame.sprite.Sprite):
    def __init__(self, groups, weapon_groups):
        super(PlayerSprite, self).__init__()
        self.image = pygame.image.load("./assets/player.png").convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.center = (X_MAX/2, Y_MAX - (self.rect.height/2) - 100)
        self.dx = self.dy = 0
        self.firing = self.shot = False
        self.health = 100
        self.score = 0

        self.groups = [groups, weapon_groups]

        self.mega = 1

        self.in_position = False
        self.velocity = 2

    def update(self):
        x, y = self.rect.center

        # Handle movement
        if x + self.dx < self.rect.width/4:
            self.dx = 0

        if x + self.dx > X_MAX - (self.rect.width/4):
            self.dx = 0

        if y + self.dy < (self.rect.height/2):
            self.dy = 0

        if y + self.dy > Y_MAX - (self.rect.height/2):
            self.dy = 0

        self.rect.center = x + self.dx, y + self.dy

        # Handle firing
        if self.firing:
            self.shot = BulletSprite(x, y)
            self.shot.add(self.groups)

        if self.health < 0:
            self.kill()

    def steer(self, direction, operation):
        v = 10
        if operation == START:
            if direction in (UP, DOWN):
                self.dy = {UP: -v,
                           DOWN: v}[direction]

            if direction in (LEFT, RIGHT):
                self.dx = {LEFT: -v,
                           RIGHT: v}[direction]

        if operation == STOP:
            if direction in (UP, DOWN):
                self.dy = 0
            if direction in (LEFT, RIGHT):
                self.dx = 0

    def shoot(self, operation):
        if operation == START:
            self.firing = True
        if operation == STOP:
            self.firing = False


def create_islands(group):
    waves = []
    for i in range(10):
        x, y = random.randrange(X_MAX), random.randrange(Y_MAX)
        s = Island(x, y)
        s.add(group)
        waves.append(s)
    return waves

def create_clouds(group):
    clouds = []
    for i in range(10):
        x, y = random.randrange(X_MAX), random.randrange(Y_MAX)
        s = Cloud(x, y)
        s.add(group)
        clouds.append(s)
    return clouds


def main():
    global LEVEL
    global MIN_ENEMIES
    global MAX_ENEMIES

    time = 0
    next_level = False
    game_over = False

    # Init pygame and mixer
    pygame.init()
    pygame.mixer.init()

    # set window title and icon
    pygame.display.set_caption("Flying Fortress")
    icon = pygame.image.load("./assets/icon.png")
    pygame.display.set_icon(icon)

    # set window size
    screen = pygame.display.set_mode((X_MAX, Y_MAX), pygame.DOUBLEBUF)
    
    screen.fill(BACKGROUND_COLOR)
    enemies = pygame.sprite.Group()
    weapon_fire = pygame.sprite.Group()

    empty = pygame.Surface((X_MAX, Y_MAX))
    empty.fill(BACKGROUND_COLOR)
    clock = pygame.time.Clock()

    islands = create_islands(everything)
    clouds = create_clouds(everything)

    player = PlayerSprite(everything, weapon_fire)
    player.add(everything)

    # Get some music
    if pygame.mixer.get_init():
        pygame.mixer.music.load("./assets/soundtrack.mp3")
        pygame.mixer.music.set_volume(0.8)
        pygame.mixer.music.play(-1)

    # create fonts
    game_font_ui = pygame.freetype.Font("./assets/SuperMario256.ttf", 40)
    game_font_large = pygame.freetype.Font("./assets/SuperMario256.ttf", 100)

    while True:
        clock.tick(FRAMERATE)
        time = time + (1/FRAMERATE)
        
        # Check for input
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (
                    event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                sys.exit()
            if not game_over:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_DOWN:
                        player.steer(DOWN, START)
                    if event.key == pygame.K_LEFT:
                        player.steer(LEFT, START)
                    if event.key == pygame.K_RIGHT:
                        player.steer(RIGHT, START)
                    if event.key == pygame.K_UP:
                        player.steer(UP, START)
                    if event.key == pygame.K_LCTRL:
                        player.shoot(START)
                    if event.key == pygame.K_RETURN:
                        if player.mega:
                            player.mega -= 1
                            for i in enemies:
                                i.kill()
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_DOWN:
                        player.steer(DOWN, STOP)
                    if event.key == pygame.K_LEFT:
                        player.steer(LEFT, STOP)
                    if event.key == pygame.K_RIGHT:
                        player.steer(RIGHT, STOP)
                    if event.key == pygame.K_UP:
                        player.steer(UP, STOP)
                    if event.key == pygame.K_LCTRL:
                        player.shoot(STOP)
            if game_over:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        LEVEL = 1
                        MAX_ENEMIES = MIN_ENEMIES
                        player = PlayerSprite(everything, weapon_fire)
                        player.add(everything)
                        player.mega = 1
                        player.score = 0
                        player.health = 100
                        game_over = False
            if next_level:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        LEVEL = LEVEL + 1
                        MAX_ENEMIES = MAX_ENEMIES + 1
                        time = 0
                        player.mega = 1
                        player.score = player.score + 10
                        player.health = 100
                        next_level = False

        # Check for next level reached
        if player.score > 0 and int(time)==LEVEL_TIME:
            for i in enemies:
                i.kill()            
            next_level = True
                    
        # Check for damages
        if not game_over and not next_level:
            hit_ships = pygame.sprite.spritecollide(player, enemies, True)
            for i in hit_ships:
                player.health -= 10

        # Check for death
        if player.health <= 0:
            player.health = 0
            player.kill()
            game_over = True


        # Check for kills
        if not game_over and not next_level:
             # Check for successful attacks
            hit_ships = pygame.sprite.groupcollide(enemies, weapon_fire, True, True)
            for k, v in hit_ships.items():
                k.kill()
                for i in v:
                    i.kill()
                    player.score += 10

        # Spawn new ennemies
        if len(enemies) < MAX_ENEMIES and not game_over and not next_level:
            pos = random.randint(0, X_MAX)
            EnemySprite(pos, [everything, enemies])

        screen.fill(BACKGROUND_COLOR)

        # Update sprites
        everything.clear(screen, empty)
        everything.update()
        everything.draw(screen)

        # Show shortcuts
        game_font_ui.render_to(screen, (X_MAX-260, 20), "CTRL: FIRE", (255,255,0))
        if player.mega == 1:
            game_font_ui.render_to(screen, (X_MAX-290, Y_MAX-50), "ENTER: NUKE", (255,255,0))
        
        # Draw energy bar
        if player.health<=50:
            bar_color = (255,0,0)
        else:
            bar_color = (0,200,0)
        pygame.draw.rect(screen, bar_color, pygame.Rect(250,25,player.health*2,20))
        pygame.draw.rect(screen, (255, 255, 0), pygame.Rect(250,25,200,20), 1)

        # Draw UI
        game_font_ui.render_to(screen, (20,20),"TIME: {}".format(
            LEVEL_TIME - int(time)), (255,255,0))

        game_font_ui.render_to(screen, (20,Y_MAX-50),"LEVEL: {} SCORE: {}".format(
            LEVEL, player.score), (255,255,0))

        # Draw end of levels
        if next_level:
            time = 0
            game_font_large.render_to(screen, ((X_MAX/2)-390,(Y_MAX/2)-80),"LEVEL CLEARED", (255,255,0))
            game_font_ui.render_to(screen, ((X_MAX/2)-280,(Y_MAX/2)+20),"PRESS SPACE TO CONTINUE", (255,255,255))

        if game_over:
            time = 0
            game_font_large.render_to(screen, ((X_MAX/2)-310,(Y_MAX/2)-80),"GAME OVER", (255,255,0))
            game_font_ui.render_to(screen, ((X_MAX/2)-280,(Y_MAX/2)+20),"PRESS SPACE TO CONTINUE", (255,255,255))

        pygame.display.flip()


if __name__ == '__main__':
    main()
