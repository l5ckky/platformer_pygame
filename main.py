import pygame
import os

import pytmx.pytmx
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
    """Загружает изображение

    Возвращает кортеж с изображением и прямоугольником"""
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
    """Создаёт экземпляры класса Tile

        Возвращает кортеж с загруженным уровнем и размером тайла в пикселях """
    level = load_pygame(name)  # получаем уровень
    scale = player.rect.height // 2  # высота(ширина) тайла - пол высоты игрока
    # tile_width = level.tilewidth  # сколько пикселей тайл в ширину(высоту)
    for layer in level.visible_layers:
        if isinstance(layer, pytmx.pytmx.TiledTileLayer):
            for x, y, gid in layer:
                image_tile = level.get_tile_image_by_gid(gid)
                if image_tile:
                    image_tile = pygame.transform.scale(image_tile, [scale, scale])
                    tile = Tile(image_tile, (x * scale, y * scale))
                    if layer.name == "collide":
                        tile.add(collide_tiles)
                    if level.get_tile_properties_by_gid(gid):
                        if level.get_tile_properties_by_gid(gid)["type"] == "spikes":
                            tile.add(spikes)
                    tile.add(all_sprites)
    for obj in level.objects:
        # print(obj.x, obj.y)
        if obj.visible:
            if obj.type == "Player" and obj.name == "Spawn":
                player.rect.x = obj.x * SCALE * player.scale
                player.rect.y = obj.y * SCALE * player.scale
    return level, scale


def restart(level_name):
    global player
    global level
    global level_scale
    all_sprites.empty()
    player.kill()
    del player
    player = Player((0, 0))
    level, level_scale = gen_level(level_name)
    player.add(player_group)
    player.add(all_sprites)


class Tile(pygame.sprite.Sprite):
    """Объект Тайла

    image - текстура тайла

    position - кортеж с координатами в пикселях (x, y)"""

    def __init__(self, image, position, mask=True):
        pygame.sprite.Sprite.__init__(self)
        self.image = image  # уставливается текстура
        # self.area = screen.get_rect()  # ?
        self.rect = pygame.Rect(position[0], position[1], self.image.get_width(), self.image.get_height())
        if mask:
            self.mask = pygame.mask.from_surface(self.image)


class Player(pygame.sprite.Sprite):
    """Объект Игрока

        pos - кортеж с координатами в пикселях (x, y)"""

    def __init__(self, pos):
        pygame.sprite.Sprite.__init__(self)
        self.image, _ = load_image('player.png')
        self.scale = screen.get_height() / 1152  # получаем коэфицент адаптации
        self.scale_image = SCALE * self.scale  # домножаем масштаб на него

        # масштабируем маленькую текстуру
        self.image = pygame.transform.scale(self.image,
                                            [self.image.get_width() * self.scale_image,
                                             self.image.get_height() * self.scale_image])

        self.src_image = self.image  # запоминаем как было
        # ширина - пол высоты
        self.rect = pygame.Rect(pos[0], pos[1], self.image.get_height() // 2, self.image.get_height())
        self.jumping = False  # прыжок
        self.onGround = False  # тег "на земле"
        self.velocity = [0, 0]  # вектор скорости
        self.left = False  # идём влево
        self.right = False  # идём вправо
        self.sprint = False  # бежим
        # self.gr = None

    def jump(self):
        if self.onGround:  # если на земле
            if not self.jumping:  # если ещё не прыгнули
                self.jumping = True  # прыгаем
                self.velocity[1] = -JUMP_V * self.scale  # ускоряемся (с адаптацией, далее - тоже)

    def update(self):
        self.onGround = False  # сбрасывает тег "на земле"
        self.velocity[0] = 0  # сбрасываем скорость
        if self.right:
            self.image = self.src_image  # согласны, узнали?
            # ой тут короче лень было многострочные условия делать
            self.velocity[0] = SPRINT_V * self.scale if self.sprint else WALK_V * self.scale
        if self.left:
            self.image = pygame.transform.flip(self.src_image, 1, 0)  # разворачиваемся и уходим
            # если бежим, то скорость соответвующая; если идём, идём размеренным шагом
            self.velocity[0] = -SPRINT_V * self.scale if self.sprint else -WALK_V * self.scale

        # применяем гравитацию
        if self.velocity[1] < V_MAX * self.scale:
            self.velocity[1] += GRAVITY * self.scale

        # если на земле, никуда не дёргаемся
        if self.onGround:
            self.velocity[1] = 0

        # если прыгаем, даём ускорение
        if self.jumping:
            self.velocity[1] -= JUMP_V * self.scale
            self.jumping = False  # не прыгаем уже!

        self.rect.x += self.velocity[0]  # применяем вектор скорости к х оси
        self.check_x_collisions()  # проверяем коллизии

        self.rect.y += self.velocity[1]  # применяем вектор скорости к у оси
        self.check_y_collisions()  # проверяем столкновения

    def check_x_collisions(self):
        collisions = pygame.sprite.spritecollide(self, collide_tiles, False)
        spike_collisions = []
        for spike in spikes.sprites():
            spike_collisions.append(pygame.sprite.collide_mask(self, spike))

        for tile in collisions:  # для каждого тайла, с которым можно сталкиваться
            if self.velocity[0] > 0:  # если направляемся вправо
                self.rect.right = tile.rect.left  # спотыкаемся
                self.velocity[0] = 0  # лежим
            elif self.velocity[0] < 0:  # если направляемся вправо
                self.rect.left = tile.rect.right  # спотыкаемся
                self.velocity[0] = 0  # лежим

        for spike in spike_collisions:
            if spike:
                player.kill()

    def check_y_collisions(self):
        collisions = pygame.sprite.spritecollide(self, collide_tiles, False)
        spike_collisions = []
        for spike in spikes.sprites():
            spike_collisions.append(pygame.sprite.collide_mask(self, spike))

        for tile in collisions:  # для каждого тайла, с которым можно сталкиваться
            if self.velocity[1] > 0:  # если летим вниз
                self.rect.bottom = tile.rect.top  # ударёмся ногой
                self.onGround = True  # упали на землю
                self.velocity[1] = 0  # лежим
            elif self.velocity[1] < 0:  # если прягаем вверх
                self.rect.top = tile.rect.bottom  # ударёмся головой
                self.velocity[1] = 0  # не мотаем головой лишний раз

        for spike in spike_collisions:
            if spike:
                player.kill()


class CameraGroup(pygame.sprite.Group):
    # спасибо Clear Code (YouTube) (иносказитель)
    def __init__(self):
        super().__init__()
        self.display_surface = pygame.display.get_surface()
        # print(screen.get_width())

        # camera offset
        self.offset = pygame.math.Vector2()
        self.half_w = self.display_surface.get_size()[0] // 2
        self.half_h = self.display_surface.get_size()[1] // 2

        # box setup
        self.camera_borders = {'left': screen.get_width() * 0.4,
                               'right': screen.get_width() * 0.4,
                               'top': screen.get_height() * 0.2,
                               'bottom': screen.get_height() * 0.3}
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
        self.internal_surf_size = (screen.get_width(), screen.get_height())
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

        self.internal_surf.fill('#71ddee')  # льём небо

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


pygame.init()  # да
screen = pygame.display.set_mode((0, 0), flags=pygame.FULLSCREEN)  # на весь экран, размер окна - автоматически

# лирическое отступление: Если в windows в параметрах экрана установлен масштаб, отличный от 100 процентов, то
# разрешение определяется с учётом этого масштаба, причём в меньшую сторону. Если масштаб 100, то разрешение
# определяется сразу и игра запускается сразу, без кат-сцен ввиде мигающего черного экрана. Читы на пропуск кат-сцены
# В общем игра отображется везде одинаково, так что и ладно.

# print(screen.get_size())  # пытаемся понять, почему не все одинаковые
clock = pygame.time.Clock()  # часы
running = True  # куда бежим
dt = 0  # что это воще

# определёем группы спрайтов
all_sprites = CameraGroup()  # группа всех спрайтов, что движимы камерой
player_group = pygame.sprite.Group()  # группа игрока, ладно
collide_tiles = pygame.sprite.Group()  # группа всех спрайтов, что божьей силой не дают провалиться сквозь них
spikes = pygame.sprite.Group()

player = Player((0, 0))  # первое зарождение игрока, и да, когда-то давно он жил на (0;0), и что?
player.add(player_group)  # инвайтим в группу

level, level_scale = gen_level("levels/test_level.tmx")  # да, сначала появился игрок, потом весь мир, и что?

player.add(all_sprites)  # он такое же существо, как и все эти... камни?

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
            if event.key == pygame.K_ESCAPE:  # кнопка выхода
                running = False  # не бежим

    # screen.fill("purple")  # льём затекстурье. эм... а зачем?...

    all_sprites.update()
    all_sprites.custom_draw(player)  # кастомно применяем алгоритмы камеры

    player.right, player.left, player.sprint = False, False, False  # сбрасываем

    keys = pygame.key.get_pressed()  # какие кнопочки классные!!! (получаем список нажатых кнопок)
    if keys[pygame.K_w] or keys[pygame.K_SPACE]:  # Ц или Пробел
        player.jump()  # прыжок
    if keys[pygame.K_s]:  # присед
        pass
    if keys[pygame.K_a]:  # влево идти
        player.left = True
    if keys[pygame.K_d]:  # вправо идти
        player.right = True
    if keys[pygame.K_LSHIFT]:  # бежать
        player.sprint = True
    if not player.groups():
        if keys[pygame.K_r]:
            print("Restarting...")
            restart("levels/test_level.tmx")

    # дежукер (отладочный режим)
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

    pygame.display.flip()  # обновляем кадр

    # limits FPS to 60
    # dt is delta time in seconds since last frame, used for framerate-
    # independent physics.
    dt = clock.tick(60) / 1000  # считаем кадры

pygame.quit()  # выйдите
