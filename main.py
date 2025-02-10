import pygame
import os
from pytmx.util_pygame import load_pygame
SCALE = 5
GROUND_LEVEL = 800
GRAVITY = 1
JUMP_V = 13
WALK_V = 8
SPRINT_V = 12
V_MAX = 100
debug_text = []


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
    SCALE = player.rect.height // 2
    for layer in level.visible_layers:
        for x, y, gid in layer:
            image_tile = level.get_tile_image_by_gid(gid)
            if image_tile:
                width = image_tile.get_width()
                image_tile = pygame.transform.scale(image_tile, [SCALE, SCALE])
                tile = Tile(image_tile, (x * SCALE, y * SCALE))
                if layer.name == "collide":
                    tile.add(collide_tiles)
                tile.add(all_sprites)
    return level, SCALE


class Tile(pygame.sprite.Sprite):
    def __init__(self, image, position):
        pygame.sprite.Sprite.__init__(self)
        self.image = image
        self.area = screen.get_rect()
        self.rect = pygame.Rect(position[0], position[1], self.image.get_width(), self.image.get_height())


class Player(pygame.sprite.Sprite):
    def __init__(self, pos):
        pygame.sprite.Sprite.__init__(self)
        self.image, _ = load_image('player.png')
        self.scale = screen.get_height() / 1152
        self.scale_image = SCALE * self.scale

        self.image = pygame.transform.scale(self.image,
                                            [self.image.get_width() * self.scale_image, self.image.get_height() * self.scale_image])
        # screen = pygame.display.get_surface()
        self.src_image = self.image
        self.area = screen.get_rect()
        self.rect = pygame.Rect(pos[0], pos[1], self.image.get_height()//2, self.image.get_height())
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
                self.velocity[1] = -JUMP_V*self.scale

    def update(self):
        # if self.rect.y >= GROUND_LEVEL:
        #     self.onGround = True
        # else:
        #     self.onGround = False
        self.onGround = False
        self.velocity[0] = 0
        if self.right:
            self.image = self.src_image
            self.velocity[0] = SPRINT_V*self.scale if self.sprint else WALK_V*self.scale
        if self.left:
            self.image = pygame.transform.flip(self.src_image, 1, 0)
            self.velocity[0] = -SPRINT_V*self.scale if self.sprint else -WALK_V*self.scale

        # gravity
        if self.velocity[1] < V_MAX*self.scale:
            self.velocity[1] += GRAVITY*self.scale

        #
        if self.onGround:
            self.velocity[1] = 0

        if self.jumping:
            self.velocity[1] -= JUMP_V*self.scale
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


class CameraGroup(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.display_surface = pygame.display.get_surface()
        # print(screen.get_width())

        # camera offset
        self.offset = pygame.math.Vector2()
        self.half_w = self.display_surface.get_size()[0] // 2
        self.half_h = self.display_surface.get_size()[1] // 2

        # box setup
        self.camera_borders = {'left': screen.get_width()*0.4,
                               'right': screen.get_width()*0.4,
                               'top': screen.get_height()*0.2,
                               'bottom': screen.get_height()*0.3}
        l = self.camera_borders['left']
        t = self.camera_borders['top']
        w = self.display_surface.get_size()[0] - (self.camera_borders['left'] + self.camera_borders['right'])
        h = self.display_surface.get_size()[1] - (self.camera_borders['top'] + self.camera_borders['bottom'])
        self.camera_rect = pygame.Rect(l, t, w, h)

        # ground
        self.ground_surf = load_image("bg.jpg")[0]
        self.ground_rect = self.ground_surf.get_rect(topleft=(0, 0))

        # camera speed
        self.keyboard_speed = 5
        self.mouse_speed = 0.2

        # zoom
        self.zoom_scale = 1
        self.internal_surf_size = (2500, 2500)
        self.internal_surf = pygame.Surface(self.internal_surf_size, pygame.SRCALPHA)
        # self.internal_surf = pygame.transform.scale(self.internal_surf, screen.get_size())
        self.internal_rect = self.internal_surf.get_rect(center=(self.half_w, self.half_h))
        self.internal_surface_size_vector = pygame.math.Vector2(self.internal_surf_size)
        self.internal_offset = pygame.math.Vector2()
        self.internal_offset.x = self.internal_surf_size[0] // 2 - self.half_w
        self.internal_offset.y = self.internal_surf_size[1] // 2 - self.half_h

    def center_target_camera(self, target):
        self.offset.x = target.rect.centerx - self.half_w
        self.offset.y = target.rect.centery - self.half_h

    def box_target_camera(self, target):

        if target.rect.left < self.camera_rect.left:
            self.camera_rect.left = target.rect.left
        if target.rect.right > self.camera_rect.right:
            self.camera_rect.right = target.rect.right
        if target.rect.top < self.camera_rect.top:
            self.camera_rect.top = target.rect.top
        if target.rect.bottom > self.camera_rect.bottom:
            self.camera_rect.bottom = target.rect.bottom

        self.offset.x = self.camera_rect.left - self.camera_borders['left']
        self.offset.y = self.camera_rect.top - self.camera_borders['top']

    def custom_draw(self, player):

        # self.center_target_camera(player)
        self.box_target_camera(player)
        # self.keyboard_control()
        # self.mouse_control()
        # self.zoom_keyboard_control()

        self.internal_surf.fill('#71ddee')

        # ground
        ground_offset = self.ground_rect.topleft - self.offset + self.internal_offset
        self.internal_surf.blit(self.ground_surf, ground_offset)

        # active elements
        for sprite in self.sprites():
            offset_pos = sprite.rect.topleft - self.offset + self.internal_offset
            self.internal_surf.blit(sprite.image, offset_pos)

        # scaled_surf = pygame.transform.scale(self.internal_surf, self.internal_surface_size_vector * self.zoom_scale)
        scaled_rect = self.internal_surf.get_rect(center=(self.half_w, self.half_h))

        self.display_surface.blit(self.internal_surf, scaled_rect)


pygame.init()
screen = pygame.display.set_mode((0, 0), flags=pygame.FULLSCREEN)
print(screen.get_size())
clock = pygame.time.Clock()
running = True
dt = 0

all_sprites = CameraGroup()
player_group = pygame.sprite.Group()
collide_tiles = pygame.sprite.Group()

player = Player((518, 0))

player.add(player_group)

level, level_scale = gen_level("levels/test_level.tmx")
player.add(all_sprites)

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
            if event.key == pygame.K_ESCAPE:
                running = False

    # fill the screen with a color to wipe away anything from last frame
    screen.fill("purple")

    all_sprites.update()
    all_sprites.custom_draw(player)

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

    # player.update()

    # # изменяем ракурс камеры
    # camera.update(player)
    # # обновляем положение всех спрайтов
    # for sprite in all_sprites:
    #     camera.apply(sprite)

    if DEBUG_MODE:
        # pygame.draw.circle(screen, "red", (player.rect.x, player.rect.y), 5)
        # for obj in all_sprites.sprites():
        #     pygame.draw.circle(screen, "red", (obj.rect.x, obj.rect.y), 5)
        #     pygame.draw.circle(screen, "green", (obj.rect.centerx, obj.rect.centery), 5)
        #
        #     string_rendered = (pygame.font.Font(None, 20)
        #                        .render(f"{obj.rect.x}, {obj.rect.y}", 1, pygame.Color('red')))
        #     text_rect = string_rendered.get_rect()
        #     text_rect.x = obj.rect.x
        #     text_rect.y = obj.rect.y
        #     screen.blit(string_rendered, text_rect)

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
