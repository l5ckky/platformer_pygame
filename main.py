# Example file showing a circle moving on screen
import pygame
import os
from pytmx.util_pygame import load_pygame
# import sys

GROUND_LEVEL = 800
GRAVITY = 1
JUMP_V = 13
WALK_V = 6
SPRINT_V = 10
V_MAX = 100
debug_text = []
SCALE = 3

def load_image(name):
    """ Load image and return image object"""
    fullname = os.path.join("data", name)
    try:
        image = pygame.image.load(fullname)
        if image.get_alpha is None:
            image = image.convert()
        else:
            image = image.convert_alpha()
    except FileNotFoundError:
        print(f"Cannot load image: {fullname}")
        raise SystemExit
    return image, image.get_rect()

def gen_level(name):
    level = load_pygame(name)
    for layer in level.visible_layers:
        for x, y, gid in layer:
            image_tile = level.get_tile_image_by_gid(gid)
            if image_tile:
                width = image_tile.get_width()
                image_tile = pygame.transform.scale(image_tile, [image_tile.get_width() * SCALE, image_tile.get_height() * SCALE])
                tile = Tile(image_tile, (x*width*SCALE, y*width*SCALE))
                tile.add(collide_tiles)
                tile.add(all_sprites)

class Tile(pygame.sprite.Sprite):
    def __init__(self, image, position):
        pygame.sprite.Sprite.__init__(self)
        self.image = image
        self.area = screen.get_rect()
        self.rect = pygame.Rect(position[0], position[1], self.image.get_width(), self.image.get_height())

    def update(self):
        pass


class Player(pygame.sprite.Sprite):
    def __init__(self, pos):
        pygame.sprite.Sprite.__init__(self)
        self.image, _ = load_image('player.png')
        self.scale = 4

        self.image = pygame.transform.scale(self.image,
                                            [self.image.get_width() * self.scale, self.image.get_height() * self.scale])
        # screen = pygame.display.get_surface()
        self.src_image = self.image
        self.area = screen.get_rect()
        self.rect = pygame.Rect(pos[0], pos[1], self.image.get_width(), self.image.get_height())
        self.jumping = False
        self.onGround = False
        self.velocity = [0, 0]
        self.left = False
        self.right = False
        self.sprint = False
        self.gr = None

    def jump(self):
        if self.onGround:
            if not self.jumping:
                self.jumping = True
                self.velocity[1] = -JUMP_V

    def update(self):
        # if self.rect.y >= GROUND_LEVEL:
        #     self.onGround = True
        # else:
        #     self.onGround = False
        self.onGround = False
        self.velocity[0] = 0
        if self.right:
            self.image = self.src_image
            self.velocity[0] = SPRINT_V if self.sprint else WALK_V
        if self.left:
            self.image = pygame.transform.flip(self.src_image, 1, 0)
            self.velocity[0] = -SPRINT_V if self.sprint else -WALK_V

        # gravity
        if self.velocity[1] < V_MAX:
            self.velocity[1] += GRAVITY

        #
        if self.onGround:
            self.velocity[1] = 0

        if self.jumping:
            self.velocity[1] -= JUMP_V
            self.jumping = False

        self.rect.x += self.velocity[0]
        self.check_x_collisions()

        self.rect.y += self.velocity[1]
        self.check_y_collisions()

    def check_x_collisions(self):
        collisions = pygame.sprite.spritecollide(self, collide_tiles, False)

        for tile in collisions:
            if self.velocity[0] > 0:
                self.rect.right = tile.rect.left
                self.velocity[0] = 0
            elif self.velocity[0] < 0:
                self.rect.left = tile.rect.right
                self.velocity[0] = 0

    def check_y_collisions(self):
        collisions = pygame.sprite.spritecollide(self, collide_tiles, False)

        for tile in collisions:
            if self.velocity[1] > 0:
                self.rect.bottom = tile.rect.top
                self.onGround = True
                self.velocity[1] = 0
            elif self.velocity[1] < 0:
                self.rect.top = tile.rect.bottom
                self.velocity[1] = 0


# pygame setup
pygame.init()
screen = pygame.display.set_mode((1920, 1080))
clock = pygame.time.Clock()
running = True
dt = 0

all_sprites = pygame.sprite.Group()
collide_tiles = pygame.sprite.Group()

player = Player((518, 0))
player.add(all_sprites)

gen_level("test_level.tmx")

# tile = Tile((6, 10))
# tile.add(collide_tiles)
# tile.add(all_sprites)
#
# tile2 = Tile((4.5, 8))
# tile2.add(collide_tiles)
# tile2.add(all_sprites)
#
# tile3 = Tile((4.5, 9))
# tile3.add(collide_tiles)
# tile3.add(all_sprites)
#
# tile4 = Tile((3, 10))
# tile4.add(collide_tiles)
# tile4.add(all_sprites)
#
# tile5 = Tile((5, 4))
# tile5.add(collide_tiles)
# tile5.add(all_sprites)

DEBUG_MODE = False

while running:
    # poll for events
    # pygame.QUIT event means the user clicked X to close your window
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F1:
                DEBUG_MODE = not DEBUG_MODE

    # fill the screen with a color to wipe away anything from last frame
    screen.fill("purple")

    all_sprites.draw(screen)

    player.right, player.left, player.sprint = False, False, False

    keys = pygame.key.get_pressed()
    if keys[pygame.K_w] or keys[pygame.K_SPACE]:  # jump
        player.jump()
    if keys[pygame.K_s]:  # crouch
        pass
    if keys[pygame.K_a]:  # left
        player.left = True
    if keys[pygame.K_d]:  # right
        player.right = True
    if keys[pygame.K_LSHIFT]:
        player.sprint = True

    # flip() the display to put your work on screen

    player.update()

    if DEBUG_MODE:
        # pygame.draw.circle(screen, "red", (player.rect.x, player.rect.y), 5)
        for obj in all_sprites.sprites():
            pygame.draw.circle(screen, "red", (obj.rect.x, obj.rect.y), 5)
            pygame.draw.circle(screen, "green", (obj.rect.centerx, obj.rect.centery), 5)

            string_rendered = (pygame.font.Font(None, 20)
                               .render(f"{obj.rect.x}, {obj.rect.y}", 1, pygame.Color('red')))
            text_rect = string_rendered.get_rect()
            text_rect.x = obj.rect.x
            text_rect.y = obj.rect.y
            screen.blit(string_rendered, text_rect)

        font = pygame.font.Font(None, 30)
        text_coord = 50
        for line in debug_text:
            string_rendered = font.render(line, 1, pygame.Color('black'))
            intro_rect = string_rendered.get_rect()
            text_coord += 5
            intro_rect.top = text_coord
            intro_rect.x = 10
            text_coord += intro_rect.height
            screen.blit(string_rendered, intro_rect)

        debug_text = [f"VEL {player.velocity[0]} {player.velocity[1]}",
                      f"POS {player.rect.x} {player.rect.y}",
                      f"GR {player.onGround}",
                      f"SPRINT {player.sprint}"]

    pygame.display.flip()
    # limits FPS to 60
    # dt is delta time in seconds since last frame, used for framerate-
    # independent physics.
    dt = clock.tick(60) / 1000

pygame.quit()
