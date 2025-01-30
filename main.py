# Example file showing a circle moving on screen
import pygame
import os
# import sys

GROUND_LEVEL = 500
GRAVITY = 1
JUMP_V = 20
WALK_V = 5
SPRINT_V = 7


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


class Tile(pygame.sprite.Sprite):
    def __init__(self, pos):
        pygame.sprite.Sprite.__init__(self)
        self.image, _ = load_image('tile.png')
        self.scale = 6
        self.image = pygame.transform.scale(self.image,
                                            [self.image.get_width() * self.scale, self.image.get_height() * self.scale])
        # screen = pygame.display.get_surface()
        self.area = screen.get_rect()
        self.rect = pygame.Rect(pos[0] * 16 * self.scale, pos[1] * 16 * self.scale, self.image.get_width(), self.image.get_height())

    def update(self):
        pass


class Player(pygame.sprite.Sprite):
    def __init__(self, pos):
        pygame.sprite.Sprite.__init__(self)
        self.image, _ = load_image('player.png')
        self.scale = 5
        self.image = pygame.transform.scale(self.image,
                                            [self.image.get_width() * self.scale, self.image.get_height() * self.scale])
        # screen = pygame.display.get_surface()
        self.area = screen.get_rect()
        self.rect = pygame.Rect(pos[0], pos[1], self.image.get_width(), self.image.get_height())
        self.jumping = False
        self.onGround = False
        self.velocity = [0, 0]
        self.left = False
        self.right = False

    def jump(self):
        if self.onGround:
            if not self.jumping:
                self.jumping = True

    def update(self):
        # if self.rect.y + self.rect.height >= GROUND_LEVEL:
        #     self.onGround = True
        # else:
        #     self.onGround = False

        self.velocity[0] = 0
        if self.right:
            self.velocity[0] = WALK_V
        if self.left:
            self.velocity[0] = -WALK_V



        # gravity
        print(self.velocity)
        if self.velocity[1] < 20:
            self.velocity[1] += GRAVITY

        if self.onGround:
            self.velocity[1] = 0

        if self.jumping:
            self.velocity[1] -= JUMP_V
            self.jumping = False

        prev_rect = self.rect

        self.rect = pygame.Rect(self.rect.x + self.velocity[0], self.rect.y + self.velocity[1], self.rect.width,
                                self.rect.height)

        collides = self.check_collides()
        if collides:
            for side, obj in collides:
                # print(side)
                if side == "top":
                    self.rect.y = obj.rect.y - self.rect.height + 1
                    self.onGround = True
                if side == "left":
                    self.rect.x = obj.rect.x - obj.rect.width - 1
                if side == "right":
                    self.rect.x = obj.rect.x + obj.rect.width - 2
                # if side == "left":
                #     self.rect.x = obj.rect.x - self.rect.width
        else:
            self.onGround = False


    def check_collides(self):
        collides = pygame.sprite.spritecollide(self, collide_tiles, False)
        r = []
        for obj in collides:
            collide_side = None
            top = obj.rect.y + obj.rect.height * 0.2 > self.rect.y + self.rect.height
            bottom = obj.rect.centery < self.rect.y
            left = obj.rect.centerx > self.rect.x + self.rect.width
            right = obj.rect.centerx < self.rect.x
            print(top, bottom, left, right)
            if top and not bottom:
                collide_side = "top"
            elif bottom and not top:
                collide_side = "bottom"
            if left and not right and not top and not bottom:
                collide_side = "left"
            elif right and not left and not top and not bottom:
                collide_side = "right"
            print(collide_side)
            r.append((collide_side, obj))
        return r





# pygame setup
pygame.init()
screen = pygame.display.set_mode((1920, 1080))
clock = pygame.time.Clock()
running = True
dt = 0

all_sprites = pygame.sprite.Group()
collide_tiles = pygame.sprite.Group()

player = Player((315, 100))
player.add(all_sprites)

tile = Tile((3, 10.4))
tile.add(collide_tiles)
tile.add(all_sprites)

tile2 = Tile((4.6, 9))
tile2.add(collide_tiles)
tile2.add(all_sprites)

tile3 = Tile((9, 9))
tile3.add(collide_tiles)
tile3.add(all_sprites)


while running:
    # poll for events
    # pygame.QUIT event means the user clicked X to close your window
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # fill the screen with a color to wipe away anything from last frame
    screen.fill("purple")

    all_sprites.draw(screen)
    # pygame.draw.circle(screen, "red", (player.rect.x, player.rect.y), 5)
    # pygame.draw.circle(screen, "red", (tile.rect.x, tile.rect.y), 5)
    # pygame.draw.circle(screen, "red", (tile2.rect.x, tile2.rect.y), 5)
    # pygame.draw.circle(screen, "red", (tile3.rect.x, tile3.rect.y), 5)
    # pygame.draw.circle(screen, "green", (tile.rect.centerx, tile.rect.centery), 5)
    # pygame.draw.circle(screen, "green", (tile2.rect.centerx, tile2.rect.centery), 5)
    # pygame.draw.circle(screen, "green", (tile3.rect.centerx, tile3.rect.centery), 5)

    player.right, player.left = False, False

    keys = pygame.key.get_pressed()
    if keys[pygame.K_w]:
        player.jump()
    if keys[pygame.K_s]:
        # player.crouch()
        pass
    if keys[pygame.K_a]:
        player.left = True

    if keys[pygame.K_d]:
        player.right = True

    # flip() the display to put your work on screen
    pygame.display.flip()

    player.update()


    # limits FPS to 60
    # dt is delta time in seconds since last frame, used for framerate-
    # independent physics.
    dt = clock.tick(60) / 1000

pygame.quit()
