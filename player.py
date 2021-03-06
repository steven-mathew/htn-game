import pygame as pg
from renderer import GAME_RESOLUTION
import math
import random
from pygame.math import *
import utils
import sys


global particles
particles = []


global circle_effects
circle_effects = []

global sparks
sparks = []

global BULLET_IMAGE
BULLET_IMAGE = None

global cooldown
cooldown = 0

global LIGHT_IMAGE
LIGHT_IMAGE = pg.transform.scale(
    pg.image.load('resources/light.png'), (80, 80))

global game_end_timer
game_end_timer = -1

class Bullet(pg.sprite.Sprite):
    sound_pew = None
    sound_hit = None
    sound_wall_hit = None
    sound_portal_hit = None
    chan1 = None
    chan2 = None

    def __init__(self, angle, renderer, x, y, player, block_list):
        # Call the parent class (Sprite) constructor
        super().__init__()

        self.image = BULLET_IMAGE
        self.original_image = self.image

        self.angle = angle
        self.renderer = renderer

        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

        self.original_x = x
        self.original_y = y

        self.bullet_shoot_sound()
        self.player = player
        self.block_list = block_list

        self.vx = math.cos(math.radians(self.angle)) * \
            3 * 3
        self.vy = math.sin(math.radians(self.angle)) * \
            3 * 3

        self.bounce = 0
        self.tp_cooldown = 0
        self.tp_count = 0

    def bullet_shoot_sound(self):
        # chan1 = pg.mixer.find_channel()
        # if chan1:
        # chan1.set_volume(1.0, 0.0)
        # chan1.play(Bullet.sound_pew)

        # chan2 = pg.mixer.find_channel()
        # if chan2:
        # chan2.set_volume(
        # 0.0, 1.0)
        # chan2.play(Bullet.sound_pew)
        Bullet.sound_pew.play()

    def bullet_hit_sound(self):
        Bullet.sound_hit.play()

    def bullet_bounce_wall(self):
        Bullet.sound_wall_hit.play()

    def update(self):
        """ Move the bullet. """
        # if self.tp_cooldown == 0:
        self.rect.x += self.vx
        self.rect.y -= self.vy

        if self.tp_cooldown > 0:
            self.tp_cooldown -= 1

        w, h = self.original_image.get_size()

        if self.renderer.night:
            rot_img, rot_origin = self.renderer.rotate(
                self.original_image, (self.rect.x, self.rect.y), (w/2, h/2), self.angle)

            if utils.distance((self.rect.x, self.rect.y), (self.original_x, self.original_y)) > 20:
                self.renderer.filter.blit(
                    LIGHT_IMAGE, (self.rect.x - LIGHT_IMAGE.get_width() / 2, self.rect.y - LIGHT_IMAGE.get_height() / 2))

            self.renderer.base_surface.blit(rot_img, rot_origin)
        else:
            rot_img, rot_origin = self.renderer.rotate(
                self.original_image, (self.rect.x, self.rect.y), (w/2, h/2), self.angle)
            self.renderer.base_surface.blit(rot_img, rot_origin)

        for i, bullet in sorted(enumerate(self.player.bullet_list), reverse=True):
            down = bullet.rect.y > GAME_RESOLUTION[1]
            up = bullet.rect.y < 0
            right = bullet.rect.x > GAME_RESOLUTION[0]
            left = bullet.rect.x < 0

            if right or left or down or up:
                self.player.bullet_list.remove(bullet)
                self.renderer.all.remove(bullet)

                sign_x = 1 if left else -1 if right else 0
                sign_y = 1 if up else -1 if down else 0

                sparks.append([[bullet.rect.x + sign_x*15, bullet.rect.y + sign_y*15], random.randint(
                    0, 359), random.randint(7, 10) / 10, 5 * random.randint(5, 10) / 10, (241, 242, 218)])
                self.renderer.screen_shake = 4
                self.bullet_bounce_wall()

        if self.bounce > 3 or self.tp_count > 5:
            self.player.bullet_list.remove(bullet)
            self.renderer.all.remove(bullet)
            sparks.append([[bullet.rect.x, bullet.rect.y], random.randint(
                    0, 359), random.randint(4, 8) / 10, 5 * random.randint(5, 10) / 10, (241, 242, 218)])

        for block in self.block_list:
            if self.rect.colliderect(block.rect):
                if block.block_type == 'portal' and self.tp_cooldown == 0:
                    candidate_block = random.choice(self.block_list)
                    while candidate_block.block_type != 'portal' or candidate_block == block:
                        candidate_block = random.choice(self.block_list)

                    angle = self.angle % 360
                    # faci+-+-ng_up =
                    facing_right = angle > 315 or angle <= 45
                    facing_down = angle <= 315 and angle > 225
                    facing_left = angle <= 225 and angle > 135
                    facing_up = False
                    # print(facing_right, facing_down, facing_left)
                    # print(angle)
                    mx = 0
                    my = 0

                    if facing_right:
                        mx = candidate_block.rect.x + candidate_block.w
                        my = self.rect.y - block.rect.y + candidate_block.rect.y
                    elif facing_left:
                        mx = candidate_block.rect.x
                        my = self.rect.y - block.rect.y + candidate_block.rect.y
                    elif facing_down:
                        mx = self.rect.x - block.rect.x + candidate_block.rect.x
                        my = candidate_block.rect.y + candidate_block.h
                    else:
                        mx = self.rect.x - block.rect.x + candidate_block.rect.x
                        my = candidate_block.rect.y
                        facing_up = True

                    # print(candidate_block.rect)
                    self.rect.x = mx
                    self.rect.y = my
                    # self.vx *= 2
                    # self.vy *= 2
                    self.tp_cooldown = 10
                    # SPARKS THE COLOR OF THE STICKY NOTE
                    # angle -= 90
                    for _ in range(15):
                        sparks.append([[self.rect.x, self.rect.y], random.randint(0, 359), random.randint(
                                3, 7) / 10 * 1, 9 * random.randint(5, 10) / 10 * 1 * (-1 if facing_up or facing_down else 1), candidate_block.color])
                    self.tp_count += 1
                    Bullet.sound_portal_hit.play()
                elif block.block_type == 'wall':
                    # self.vx *= -1
                    # self.vy *= -1
                    # sound
                    # if self.rect.y + 3 >= block.rect.y or self.rect.y - 3 <= block.rect.y + block.h:
                    # self.vy *= -1
                    # if self.rect.x + 3 >= block.rect.x or self.rect.x - 3 <= block.rect.x + block.w:
                    # self.vx *= -1

                    # down = self.rect.y <= block.rect.y + block.h / 2
                    # up = self.rect.y >= block.rect.y
                    # left = self.rect.x >= block.rect.x
                    # right = self.rect.x <= block.rect.x + block.w / 2

                    # down = self.rect.top > block.rect.bottom
                    # top = self.rect.bottom > block.rect.top
                    # left = self.rect.right > block.rect.left
                    # right = self.rect.left < block.rect.right

                    # print(top, down, left, right)
                    # sign_x = 1 if left else -1 if right else 0
                    # sign_y = 1 if top else -1 if down else 0

                    # if block.rect.+y < self.rect.y or block.
                    xd = (block.rect.x + block.w / 2) - \
                        (self.rect.x)  # this needs work
                    yd = (block.rect.y + block.h / 2) - \
                        (self.rect.y)

                    if xd < 0:
                        xd *= -1
                    if yd < 0:
                        yd *= -1

                    if xd > yd:
                        self.vx *= -1
                    else:
                        self.vy *= -1
                    self.bullet_hit_sound()
                    self.bounce += 1
                    self.angle += 90
                # if self.rect.x + 4 > block.rect.x and \
                        # self.rect.x + self.image.get_width() - 4 < block.rect.x + block.w and \
                            # self.rect.y + 4 > block.rect.y and \
                                # self.rect.y + self.rect.w - 4 < block.rect.y + block.h:
                        # print('sdf')

                # bx = block.rect.x - block.w / 2
                # by = block.rect.y - block.h / 2

                # ix = self.rect.x
                # iy = self.rect.y

                # if bx < ix and by < iy:
                    # if ix + self.image.get_width() < bx + block.w \
                            # and iy + self.image.get_height() < by + block.h:
                        # print('inside')

# this code is bad... don't look


class Player(pg.sprite.Sprite):
    image_orig = pg.Surface([25, 25])
    image_orig.set_colorkey((0, 0, 0))
    image_orig.fill((241, 242, 218))

    image_orig2 = pg.Surface([25, 25])
    image_orig2.set_colorkey((0, 0, 0))
    image_orig2.fill((163, 206, 250))

    box_rand = [image_orig, image_orig2]
    font =None
    def __init__(self, renderer, x, y, block_list, enemy=None):
        super(Player, self).__init__()

        self.image = pg.image.load(
            'resources/player_animations/p1_idle/p1_idle_0.png').convert()
        global BULLET_IMAGE
        BULLET_IMAGE = pg.image.load('resources/p1_bullet.png').convert()
        self.image.set_colorkey((0, 0, 0))
        self.original_image = self.image

        self.rect = self.image.get_rect()
        self.renderer = renderer
        self.speed = 2
        self.position = Vector2(x, y)
        self.angle_speed = 0
        self.angle = 0
        self.accel = 0
        self.rot_accel = 0
        self.rot_max_speed = 7
        self.max_speed = 2.71828183  # for jokes
        self.dx = 0
        self.state = 'p1_idle'
        self.frame = 0

        # pg.mixer.pre_init(44100, -16, 10, 3072)
        pg.mixer.pre_init(44100, -16, 2, 512)
        pg.mixer.set_num_channels(32)

        Bullet.sound_pew = pg.mixer.Sound('resources/shoot_bloop.wav')
        Bullet.sound_pew.set_volume(0.035)
        Bullet.sound_hit = pg.mixer.Sound('resources/bounce6.wav')
        Bullet.sound_hit.set_volume(0.02)
        Bullet.sound_wall_hit = pg.mixer.Sound('resources/hit_projectile.wav')
        Bullet.sound_wall_hit.set_volume(0.02)
        Bullet.sound_portal_hit = pg.mixer.Sound('resources/place.wav')
        Bullet.sound_portal_hit.set_volume(0.02)
        self.hit_sound = pg.mixer.Sound('resources/hit.wav')
        self.hit_sound.set_volume(0.04)

        self.portal_sound = pg.mixer.Sound('resources/portal_sound.wav')
        self.portal_sound.set_volume(0.04)
        self.bullet_list = pg.sprite.Group()
        self.enemy = enemy

        self.health = 100
        self.block_list = block_list
        self.stun = 0
        self.tp_cooldown = 0
        self.dead = False
        Player.font = pg.font.SysFont("freesansbold", 100)
    def update(self):
        w, h = self.original_image.get_size()
        key_pressed = pg.key.get_pressed()

        global cooldown
        cooldown += self.renderer.clock.get_time()

        if cooldown > 165:
            cooldown = 0
        if self.tp_cooldown > 0:
            self.tp_cooldown -= 1
        if self.stun > 0:
            self.stun -= 1

        global game_end_timer
        if game_end_timer > 0:
            game_end_timer -=1
        if game_end_timer <= 0 and self.dead:
            sys.exit()

        if key_pressed[pg.K_LEFT]:
            self.rot_accel = 1.5
        elif key_pressed[pg.K_RIGHT]:
            self.rot_accel = -1.5
        else:
            self.rot_accel = 0

        self.frame += 1
        if self.frame >= len(self.renderer.animation_database[self.state]):
            self.frame = 0
        player_img_id = self.renderer.animation_database[self.state][self.frame]
        player_img = self.renderer.animation_frames[player_img_id]

        rotated_image, origin = self.renderer.rotate(player_img,
                                                     self.position, (w/2, h/2), self.angle)
        # print(game_end_timer)
        if (self.health < 20):
            text = Player.font.render('Player Red Wins', 1, pg.Color((255, 255, 255)))
            text_rect = text.get_rect(center=(GAME_RESOLUTION[0]//2, GAME_RESOLUTION[1] // 2))
            # return text, text_rect

            black_surf = pg.Surface((1600, 900))
            black_surf.fill((0,0,0))
            self.renderer.window.blit(black_surf, (0,0))
            self.renderer.window.blit(text, text_rect)
            if not self.dead:
                game_end_timer = 70
            rotated_image.fill((255, 255, 255, 0), None, pg.BLEND_RGBA_MULT)
            self.dead = True
        else:
            rotated_image.fill((255, 255, 255, 2.55 * self.health),
                               None, pg.BLEND_RGBA_MULT)

        self.renderer.base_surface.blit(
            rotated_image, origin)

        for i, bullet in sorted(enumerate(self.enemy.bullet_list), reverse=True):
            if self.rect.colliderect(bullet.rect):
                self.enemy.bullet_list.remove(bullet)
                self.renderer.all.remove(bullet)

                circle_effects.append([[self.rect.x, self.rect.y], 15, [
                                      3, 0.2], [3, 0.3], (255, 255, 255)])
                sparks.append([[self.rect.x, self.rect.y], random.randint(
                    0, 359), random.randint(13, 18) / 10 * 1.5, 5 * random.randint(5, 10) / 10, (241, 242, 218)])
                self.renderer.screen_shake = 6
                self.health -= 5
                self.hit_sound.play()
        # Circle Effects ----------------------------------------- #
        # loc, radius, border_stats, speed_stats, color
        for i, circle in sorted(enumerate(circle_effects), reverse=True):
            circle[1] += circle[3][0]
            circle[2][0] -= circle[2][1]
            circle[3][0] -= circle[3][1]
            if circle[2][0] < 1:
                circle_effects.pop(i)
            else:
                pg.draw.circle(self.renderer.base_surface, circle[4], [int(circle[0][0]), int(
                    circle[0][1])], int(circle[1]), int(circle[2][0]))

        if key_pressed[pg.K_SPACE] and cooldown == 0 and self.stun == 0:
            self.state, self.frame = self.renderer.change_state(
                self.state, self.frame, 'p1_shoot')

            px = self.position[0] + math.cos(math.radians(self.angle)) * 10
            py = self.position[1] - math.sin(math.radians(self.angle)) * 10

            image = pg.transform.rotate(
                random.choice(Player.box_rand), random.randint(0, 360))
            rect = image.get_rect(center=(px, py))

            b = Bullet(self.angle, self.renderer,
                       self.position[0], self.position[1], self, self.block_list)
            self.bullet_list.add(b)
            self.renderer.add(b)

            self.renderer.base_surface.blit(image, rect)
            if self.renderer.night:
                self.renderer.filter.blit(
                    LIGHT_IMAGE, (self.position[0] - LIGHT_IMAGE.get_width() / 2, self.position[1] - LIGHT_IMAGE.get_height() / 2))
        else:
            self.state, self.frame = self.renderer.change_state(
                self.state, self.frame, 'p1_idle')

        # Sparks ------------------------------------------------- #
        for i, spark in sorted(enumerate(sparks), reverse=True):  # loc, dir, scale, speed
            speed = spark[3]
            scale = spark[2]
            points = [
                utils.advance(spark[0], spark[1], 2 * speed * scale),
                utils.advance(spark[0], spark[1] + 90, 0.3 * speed * scale),
                utils.advance(spark[0], spark[1], -1 * speed * scale),
                utils.advance(spark[0], spark[1] - 90, 0.3 * speed * scale),
            ]
            points = [[v[0], v[1]] for v in points]
            color = (241, 242, 218)
            # color = (255, 0,)
            if len(spark) > 4:
                color = spark[4]

            pg.draw.polygon(self.renderer.base_surface, color, points)

            spark[0] = utils.advance(spark[0], spark[1], speed)
            # spark[3] -= 0.5+-
            if spark[3] < 0.5:
                spark[3] += 0.5
            elif spark[3] > 0.5:
                spark[3] -= 0.5

            if abs(spark[3]) <= 0.5:
                sparks.pop(i)
            if self.renderer.night:
                self.renderer.filter.blit(
                    LIGHT_IMAGE, (spark[0][0] - LIGHT_IMAGE.get_width() / 2, spark[0][1] - LIGHT_IMAGE.get_height() / 2))


        # Handle acceleration
        if key_pressed[pg.K_UP] and not self.stun:
            if self.accel_x == 0:
                self.accel_x = 0.7
        else:
            self.accel_x = 0

        for block in self.block_list:
            if self.rect.colliderect(block.rect) and block.block_type == 'wall':
                self.accel_x = -0.7
                self.stun = 45
                self.renderer.screen_shake = 2

        self.dx += self.accel_x

        if abs(self.dx) >= self.max_speed:
            self.dx = self.dx / abs(self.dx) * self.max_speed
        if self.accel_x == 0:
            self.dx *= 0.87

        newX = self.position[0] + math.cos(math.radians(self.angle)) * self.dx
        newY = self.position[1] - math.sin(math.radians(self.angle)) * self.dx

        self.position[0] = max(0, min(newX, GAME_RESOLUTION[0]))
        self.position[1] = max(0, min(newY, GAME_RESOLUTION[1]))

        self.rect.x = self.position[0]
        self.rect.y = self.position[1]
        # Handle rotational interia
        self.angle_speed += self.rot_accel

        if abs(self.angle_speed) >= self.rot_max_speed:
            self.angle_speed = self.angle_speed / \
                abs(self.angle_speed) * self.rot_max_speed

        if self.rot_accel == 0:
            self.angle_speed *= 0.92

        self.angle += self.angle_speed


        # print(self.angle % 360)
        for block in self.block_list:
            if self.rect.colliderect(block.rect) and block.block_type == 'portal' and self.tp_cooldown == 0:
                candidate_block = random.choice(self.block_list)
                while candidate_block.block_type != 'portal' or candidate_block == block:
                    candidate_block = random.choice(self.block_list)

                angle = self.angle % 360
                # faci+-+-ng_up =
                facing_right = angle > 315 or angle <= 45
                facing_down = angle <= 315 and angle > 225
                facing_left = angle <= 225 and angle > 135
                facing_up = False
                # print(facing_right, facing_down, facing_left)

                mx = 0
                my = 0


                if facing_right:
                    mx = candidate_block.rect.x + candidate_block.w
                    my = self.rect.y - block.rect.y + candidate_block.rect.y
                elif facing_left:
                    mx = candidate_block.rect.x
                    my = self.rect.y - block.rect.y + candidate_block.rect.y
                elif facing_down:
                    mx = self.rect.x - block.rect.x + candidate_block.rect.x
                    my = candidate_block.rect.y + candidate_block.h
                else:
                    mx = self.rect.x - block.rect.x + candidate_block.rect.x
                    my = candidate_block.rect.y
                    facing_up = True


                # if facing_right:
                    # mx = candidate_block.rect.x + candidate_block.w
                    # my = candidate_block.rect.y + candidate_block.h / 2
                # elif facing_left:
                    # mx = candidate_block.rect.x
                    # my = candidate_block.rect.y + candidate_block.h / 2
                # elif facing_down:
                    # mx = candidate_block.rect.x + candidate_block.w / 2
                    # my = candidate_block.rect.y + candidate_block.h
                # else:
                    # mx = candidate_block.rect.x + candidate_block.w / 2
                    # my = candidate_block.rect.y
                    # facing_up = True
                self.position[0] = mx
                self.position[1] = my
                self.accel_x = 2
                self.tp_cooldown = 120
                # SPARKS THE COLOR OF THE STICKY NOTE
                for _ in range(30):
                    sparks.append([[self.position[0], self.position[1]], random.randint(0, 359), random.randint(
                            7, 10) / 10 * 3, 9 * random.randint(5, 10) / 10 * 1 * (-1 if facing_up or facing_down else 1), candidate_block.color])
                self.portal_sound.play()
                # if self.renderer.night:
                    # self.renderer.filter.blit(
                        # LIGHT_IMAGE, (self.position[0] - LIGHT_IMAGE.get_width() / 2, self.position[1] - LIGHT_IMAGE.get_height() / 2))

