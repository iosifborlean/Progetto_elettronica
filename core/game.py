import pygame
import random
import serial
import time

special = 0
normal = 1
pygame.init()
clock = pygame.time.Clock()
fps = 60

screen_width = 600
screen_height = 800

screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Space Invaders")

font30 = pygame.font.SysFont("Constantia", 30)
font40 = pygame.font.SysFont("Constantia", 40)

rows = 7
cols = 5

x_distance_btwn_aliens = 100
y_distance_btwn_aliens = 60
max_alien_x_movement = 76  # relative to center

countdown = 3

red = (255, 0, 0)
green = (0, 255, 0)
white = (255, 255, 255)

bg = pygame.image.load("Img/bg.png")


def draw_bg():
    screen.blit(bg, (0, 0))


def draw_text(text, font, text_col, x, y):
    img = font.render(text, True, text_col)
    screen.blit(img, (x, y))


class Game:
    def __init__(self):
        self.game_start = pygame.time.get_ticks()
        self.game_over = 0
        self.last_alien_shot = pygame.time.get_ticks()
        self.last_alien_special_shot = pygame.time.get_ticks()
        self.last_count = pygame.time.get_ticks()
        self.points = 0


class Rules:
    def __init__(self):
        self.alien_bullets_cooldown = 1000
        self.alien_special_bullets_cooldown = 2000
        self.max_alien_bullets = 6
        self.y_alien_speed = 20
        self.alien_speed = 1
        self.special_attack_cooldown = 10
        self.special_attack_charge_time = 60 # 1 sec is 60 frames
        self.trapping_cooldown = 5
        self.player_bullets_cooldown = 500
        self.up_difficulty_treshold = 10
        self.difficulty_count = 0

    def up_difficulty(self):
        self.alien_bullets_cooldown -= 100
        self.alien_special_bullets_cooldown -= 200
        self.player_bullets_cooldown -= 5
        self.difficulty_count += 1
        self.y_alien_speed += 2
        if self.difficulty_count == 3:
            self.difficulty_count = 0
            self.max_alien_bullets += 1


class Spaceship(pygame.sprite.Sprite):
    def __init__(self, x, y, health):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load("Img/spaceship.png")
        self.rect = self.image.get_rect()
        self.rect.center = [x, y]
        self.health_start = health
        self.health_remaining = health
        self.last_shot = pygame.time.get_ticks()
        self.special_attack = 0
        self.special_attack_available = False
        self.special_attack_charge = 0
        self.immobilized = False
        self.last_pressed = pygame.K_LEFT
        self.break_free_count = 0
        self.trap = None

    def update(self):
        speed = 5
        scheda = serial.Serial('COM6', 115200, timeout=1)

        scheda.write('1'.encode())

        line = scheda.read(2)
        scheda.reset_input_buffer()
        line = list(line.decode("utf"))
        direction = line[0]
        button_pressed = line[1]

        cooldown = rules.player_bullets_cooldown
        key = pygame.key.get_pressed()
        if not self.immobilized:
            if direction == "S" and self.rect.left > 0:
                self.rect.x -= speed
            if direction == "D" and self.rect.right < screen_width:
                self.rect.x += speed

            time_now = pygame.time.get_ticks()
            if button_pressed == "1" and time_now - self.last_shot > cooldown:
                bullet = Bullets(self.rect.centerx, self.rect.top)
                bullet_group.add(bullet)
                self.last_shot = time_now
            if self.special_attack_available == True and button_pressed == "Y":
                self.special_attack_charge += 1
                if self.special_attack_charge == rules.special_attack_charge_time:
                    bullet = Special_Bullets(self.rect.centerx, self.rect.top)
                    bullet_group.add(bullet)
                    self.last_shot = time_now
                    self.special_attack_available = False
                    self.special_attack = 0
                    self.special_attack_charge = 0
            else:
                self.special_attack_charge = 0
        else:
            if self.last_pressed == pygame.K_LEFT and key[pygame.K_RIGHT]:
                self.break_free_count += 1
                self.last_pressed = pygame.K_RIGHT
            elif self.last_pressed == pygame.K_RIGHT and key[pygame.K_LEFT]:
                self.break_free_count += 1
                self.last_pressed = pygame.K_LEFT
            if self.break_free_count > rules.trapping_cooldown:
                self.immobilized = False
                self.trap.kill()
                self.break_free_count = 0



        self.mask = pygame.mask.from_surface(self.image)

        pygame.draw.rect(screen, red, (self.rect.x, (self.rect.bottom + 10), self.rect.width, 15))
        if self.health_remaining > 0:
            pygame.draw.rect(screen, green, (
            self.rect.x, (self.rect.bottom + 10), int(self.rect.width * (self.health_remaining / self.health_start)),
            15))
        elif self.health_remaining <= 0:
            explosion = Explosion(self.rect.centerx, self.rect.centery, 3)
            explosion_group.add(explosion)
            self.kill()
            current_game.game_over = -1

        if pygame.sprite.spritecollide(self, alien_group, False):
            explosion = Explosion(self.rect.centerx, self.rect.centery, 3)
            explosion_group.add(explosion)
            self.kill()
            current_game.game_over = -1
    time.sleep(0.1)

    def get_blocked(self):
        self.immobilized = True
        trap = Barrier(self.rect.centerx, self.rect.centery)
        traps_group.add(trap)
        self.trap = trap


class Bullets(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load("Img/bullet.png")
        self.rect = self.image.get_rect()
        self.rect.center = [x, y]

    def update(self):
        hit = False
        self.rect.y -= 10
        if self.rect.bottom < 0:
            self.kill()
        if pygame.sprite.spritecollide(self, alien_group, True):
            hit = True
            explosion = Explosion(self.rect.centerx, self.rect.centery, 2)
            explosion_group.add(explosion)
            self.kill()
            return hit


class Special_Bullets(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.images = []
        for num in range(1, 6):
            img = pygame.image.load(f"Img/spec_bullet_{num}.png")
            img = pygame.transform.scale(img, (25, 28))
            self.images.append(img)
        self.index = 0
        self.image = self.images[self.index]
        self.rect = self.image.get_rect()
        self.rect.center = [x, y]
        self.counter = 0
        self.hits = 0
        self.max_hits = 3

    def update(self):
        hit = False
        self.rect.y -= 10
        if self.rect.bottom < 0:
            self.kill()
        if pygame.sprite.spritecollide(self, alien_group, True):
            hit = True
            explosion = Explosion(self.rect.centerx, self.rect.centery, 2)
            explosion_group.add(explosion)
            self.hits += 1
            if self.hits == self.max_hits:
                self.kill()

        animation_speed = 5
        self.counter += 1

        if self.counter >= animation_speed and self.index < len(self.images) - 1:
            self.counter = 0
            self.index = (self.index + 1) % 5
            self.image = self.images[self.index]

        return hit
class Enemies_group(pygame.sprite.Group):
    def __init__(self):
        pygame.sprite.Group.__init__(self)
        self.move_counter = 0
        self.move_direction = 1
        self.first_enemy_pos = [100, 20]
        self.y_movement = 0

    def update(self):
        moved_y = False
        for enemy in self.sprites():
            enemy.rect.x += (self.move_direction * rules.alien_speed)
            if abs(self.move_counter) > max_alien_x_movement:
                enemy.rect.y += rules.y_alien_speed
                moved_y = True
        self.move_counter += rules.alien_speed
        self.first_enemy_pos[0] += (self.move_direction * rules.alien_speed)
        if moved_y:
            self.first_enemy_pos[1] += rules.y_alien_speed
            self.y_movement += rules.y_alien_speed
            self.move_direction *= -1
            self.move_counter = -max_alien_x_movement + 1


class Alien(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load("img/alien" + str(random.randint(1, 5)) + ".png")
        self.rect = self.image.get_rect()
        self.rect.center = [x, y]

    def draw(self):
        screen.blit(self.image, (self.rect.centerx, self.rect.centery))


class Alien_Bullets(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load("Img/alien_bullet.png")
        self.rect = self.image.get_rect()
        self.rect.center = [x, y]

    def update(self):
        self.rect.y += 2
        if self.rect.top > screen_height:
            self.kill()
        if pygame.sprite.spritecollide(self, spaceship_group, False, pygame.sprite.collide_mask):
            self.kill()
            spaceship.health_remaining -= 1
            explosion = Explosion(self.rect.centerx, self.rect.centery, 1)
            explosion_group.add(explosion)

class Alien_Special_Bullets(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load("Img/special_alien_bullet.png")
        self.rect = self.image.get_rect()
        self.rect.center = [x, y]

    def update(self):
        self.rect.y += 2
        if self.rect.top > screen_height:
            self.kill()
        if pygame.sprite.spritecollide(self, spaceship_group, False, pygame.sprite.collide_mask):
            self.kill()
            spaceship.get_blocked()

class Barrier(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.images = []
        for num in range(1, 5):
            img = pygame.image.load(f"Img/barr_{num}.png")
            img = pygame.transform.scale(img, (94, 69))
            self.images.append(img)
        self.index = 0
        self.image = self.images[self.index]
        self.rect = self.image.get_rect()
        self.rect.center = [x, y]
        self.counter = 0

    def update(self):
        animation_speed = 7
        self.counter += 1
        if self.counter >= animation_speed:
            self.counter = 0
            self.index = (self.index + 1) % 4
            self.image = self.images[self.index]




class Explosion(pygame.sprite.Sprite):
    def __init__(self, x, y, size):
        pygame.sprite.Sprite.__init__(self)
        self.images = []
        for num in range(1, 6):
            img = pygame.image.load(f"Img/exp{num}.png")
            if size == 1:
                img = pygame.transform.scale(img, (20, 20))
            if size == 2:
                img = pygame.transform.scale(img, (40, 40))
            if size == 3:
                img = pygame.transform.scale(img, (160, 160))
            self.images.append(img)
        self.index = 0
        self.image = self.images[self.index]
        self.rect = self.image.get_rect()
        self.rect.center = [x, y]
        self.counter = 0

    def update(self):
        explosion_speed = 3
        self.counter += 1

        if self.counter >= explosion_speed and self.index < len(self.images) - 1:
            self.counter = 0
            self.index += 1
            self.image = self.images[self.index]
        if self.index >= len(self.images) - 1 and self.counter >= explosion_speed:
            self.kill()


rules = Rules()
points = 0

spaceship_group = pygame.sprite.Group()
bullet_group = pygame.sprite.Group()
alien_group = Enemies_group()
alien_bullet_group = pygame.sprite.Group()
explosion_group = pygame.sprite.Group()
traps_group = pygame.sprite.Group()


def create_aliens(rows, cols):
    for row in range(rows):
        for item in range(cols):
            alien = Alien(100 + item * x_distance_btwn_aliens, 20 + row * y_distance_btwn_aliens)
            alien_group.add(alien)


create_aliens(rows, cols)


def spawn_aliens(cols):
    x = alien_group.first_enemy_pos[0]
    y = alien_group.first_enemy_pos[1] - y_distance_btwn_aliens
    for cols in range(cols):
        alien = Alien(x + cols * x_distance_btwn_aliens, y)
        alien_group.add(alien)
    alien_group.first_enemy_pos = [x, y]


spaceship = Spaceship(int(screen_width / 2), screen_height - 100, 3)
spaceship_group.add(spaceship)


def move_game_forward():
    time_now = pygame.time.get_ticks()

    if time_now - current_game.last_alien_shot > rules.alien_bullets_cooldown \
            and len(alien_bullet_group) < rules.max_alien_bullets and len(alien_group) > 0:
        attacking_alien = random.choice(alien_group.sprites())
        alien_bullet = Alien_Bullets(attacking_alien.rect.centerx, attacking_alien.rect.bottom)
        alien_bullet_group.add(alien_bullet)
        current_game.last_alien_shot = time_now

    if time_now - current_game.last_alien_special_shot > rules.alien_special_bullets_cooldown \
            and len(alien_bullet_group) < rules.max_alien_bullets and len(alien_group) > 0:
        attacking_alien = random.choice(alien_group.sprites())
        alien_bullet = Alien_Special_Bullets(attacking_alien.rect.centerx, attacking_alien.rect.bottom)
        alien_bullet_group.add(alien_bullet)
        current_game.last_alien_special_shot = time_now



    for bullet in bullet_group.__iter__():
        if bullet.update():
            current_game.points += 1
            if (current_game.points + 1) % rules.up_difficulty_treshold == 0:
                rules.up_difficulty()
            spaceship.special_attack += 1
            if spaceship.special_attack == rules.special_attack_cooldown:
                spaceship.special_attack_available = True

    spaceship.update()
    alien_group.update()
    alien_bullet_group.update()
    if alien_group.first_enemy_pos[1] > 30:
        spawn_aliens(5)
    explosion_group.update()
    traps_group.update()


current_game = Game()

run = True
while run:

    clock.tick(fps)

    draw_bg()
    if countdown == 0:
        a = current_game.game_over
        if len(alien_group) == 0:
            current_game.game_over = 1

        if current_game.game_over == 0:
            move_game_forward()
        else:
            if current_game.game_over == -1:
                draw_text("GAME OVER", font40, white, int(screen_width / 2 - 100), int(screen_height / 2 + 50))
            elif current_game.game_over == 1:
                draw_text("YOU WIN", font40, white, int(screen_width / 2 - 100), int(screen_height / 2 + 50))

    if countdown > 0:
        draw_text("GET READY", font40, white, int(screen_width / 2 - 110), int(screen_height / 2 + 50))
        draw_text(str(countdown), font40, white, int(screen_width / 2 - 10), int(screen_height / 2 + 100))
        count_timer = pygame.time.get_ticks()
        if count_timer - current_game.last_count > 1000:
            countdown -= 1
            current_game.last_count = count_timer

    spaceship_group.draw(screen)
    bullet_group.draw(screen)
    alien_group.draw(screen)
    alien_bullet_group.draw(screen)
    explosion_group.draw(screen)
    traps_group.draw(screen)
    draw_text(str(current_game.points), font30, white, 20, screen_height - 40)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

    pygame.display.update()

pygame.quit()