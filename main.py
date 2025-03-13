import time

import pygame
import os

import pytmx.pytmx
from pytmx.util_pygame import load_pygame

import random

SCALE = 400  # масштаб игры (1 - виден весь уровень, 5 - виден игрок и по 7-8 тайлов влево и вправо)
GRAVITY = 0.2  # константа графитации
JUMP_V = 2.3  # скорость прыжка
WALK_V = 2  # скорость ходьбы
SPRINT_V = 4  # скорость бега
V_MAX = 100  # ограничение скорости

PLAYER_IMAGE = 'no anim2.png'
PLAYER_IDLE = ('no move anim.png', 4, 6)
PLAYER_RUN = ('run2.png', 6, 30)
PLAYER_WALK = ('walk2.png', 6, 15)

COINS_MAGNET = pygame.USEREVENT + 1
coins = []

FADE_OUT = 0
CURRENT_LEVEL = None
teleport = None


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
    scale = player.rect.width  # высота(ширина) тайла - пол высоты игрока
    tile_width = level.tilewidth  # сколько пикселей тайл в ширину(высоту)
    for layer in level.visible_layers:
        if layer.name == "player":
            player.add(all_sprites)
        if isinstance(layer, pytmx.pytmx.TiledTileLayer):
            for x, y, gid in layer:
                image_tile = level.get_tile_image_by_gid(gid)
                if image_tile:
                    image_tile = pygame.transform.scale(image_tile, [scale, scale])
                    tile_args = image_tile, (x * scale, y * scale)
                    tile = Tile(*tile_args)
                    if layer.name == "collide":
                        tile.solid = True
                    if layer.name == "items":
                        tile = Item(*tile_args)
                        if level.get_tile_properties_by_gid(gid):
                            if level.get_tile_properties_by_gid(gid)["type"] == "coin":
                                tile = Coin(*tile_args)
                                tile.name = "coin"
                            # if level.get_tile_properties_by_gid(gid)["type"] == "key":
                            #     tile = Coin(*tile_args)
                            #     tile.name = "coin"
                    if level.get_tile_properties_by_gid(gid):
                        if level.get_tile_properties_by_gid(gid)["type"] == "spike":
                            tile.killing = True
                        if level.get_tile_properties_by_gid(gid)["type"] == "chest":
                            tile = Chest(*tile_args)
                            img = level.images[1].convert_alpha()
                            tile.opened_image = pygame.transform.scale(img, [scale, scale])
                            tile.name = "chest"
                            tile.can_use = True
                            img = level.images[2]
                            tile.coin_image = pygame.transform.scale(img, [scale, scale])
                    tile.add(all_sprites)
    for obj in level.objects:
        # print(obj.x, obj.y)
        if obj.visible:
            if obj.type == "Player" and obj.name == "Spawn":
                player.rect.x = obj.x / tile_width * scale
                player.rect.y = obj.y / tile_width * scale
            if obj.type == "teleport":
                print("init TLEPORT", obj)
                x = obj.x / tile_width * scale
                y = obj.y / tile_width * scale
                img = pygame.transform.scale(obj.image, [scale, scale * 2])
                t = Teleport(img, (x, y), dest=obj.name)
                t.can_use = True
                t.add(all_sprites)
                print(t)
    all_sprites.level = level  # сообщаем группе об уровне
    return level, scale


def restart(level_name, save_money=True):
    global player
    global level
    global level_scale
    money = []
    if save_money:
        money = player.items

    for sprite in all_sprites.sprites():
        sprite.kill()
    all_sprites.empty()
    player.kill()
    del player
    player = Player((0, 0))
    if save_money:
        player.items = money
    player.add(player_group)
    level, level_scale = gen_level(f"levels/{level_name}")

    # player.add(all_sprites)


class Tile(pygame.sprite.Sprite):
    """Объект Тайла

    image - текстура тайла

    position - кортеж с координатами в пикселях (x, y)"""

    def __init__(self, image, position, mask=True, solid=False, killing=False, gid=None, can_use=False):
        pygame.sprite.Sprite.__init__(self)
        self.image = image  # уставливается текстура
        # self.area = screen.get_rect()  # ?
        self.rect = pygame.Rect(position[0], position[1], self.image.get_width(), self.image.get_height())
        if mask:
            self.mask = pygame.mask.from_surface(self.image)
        self.solid = solid
        self.killing = killing

        self.can_use = can_use

        self.display_text = None
        self.use_text = "Нажмите E, чтобы использовать"

    def update(self):
        if self.solid:
            self.add(collide_tiles)
        else:
            self.remove(collide_tiles)
        if self.killing:
            self.add(killing_group)
        else:
            self.remove(killing_group)

        if not self.solid:
            collision = pygame.sprite.collide_mask(self, player)
            if collision:
                self.on_collision()

        use_collision = self.rect.colliderect(player.use_rect)
        self.display_text = None
        if use_collision and self.can_use:
            self.display_text = self.use_text
            if pygame.key.get_pressed()[pygame.K_e] and not player.paralich:
                self.on_use()

    def on_collision(self):
        pass

    def on_use(self):
        pass


class Item(Tile):

    def __init__(self, image, position, collectable=False, name="None"):
        super().__init__(image, position)

        self.name = name

        self.collected = False
        self.picked_up = False
        self.max_distance = 300 * player.scale
        self.random_acc = random.randint(10, 15)
        self.max_distance *= self.random_acc
        # print(self.random_acc)

    def update(self):
        super().update()

        p_list = player.picked_up_items
        if p_list and self in p_list:
            if p_list.index(self) - 1 >= 0:
                target_rect = p_list[p_list.index(self) - 1].rect
            else:
                target_rect = player.rect
        else:
            target_rect = player.rect

        if self.picked_up:
            a = self.rect.centerx - target_rect.centerx
            b = self.rect.centery - target_rect.centery

            self.rect.centerx -= a / self.random_acc
            self.rect.centery -= b / self.random_acc

            if abs(a) > self.max_distance or abs(b) > self.max_distance:
                self.picked_up = False
                player.picked_up_items.remove(self)

    def on_collision(self):
        self.on_pick_up()
        pass

    def on_pick_up(self):
        if not self.picked_up:
            print("Item", str(self), "picked up!")
            self.picked_up = True
            player.picked_up_items.append(self)

    def on_collect(self):
        print("Item", str(self), "collected!")
        self.collected = True
        player.items.append(self)
        self.kill()
        pass

    def __str__(self):
        return self.name


class Coin(Item):

    def __init__(self, image, pos, magnet=False):
        super().__init__(image, pos)

        self.magnet = magnet
        self.random_acc = random.randint(6, 12)

    def update(self):
        super().update()

        target_rect = player.rect

        if self.magnet:
            a = self.rect.centerx - target_rect.centerx
            b = self.rect.centery - target_rect.centery

            self.rect.centerx -= a / self.random_acc
            self.rect.centery -= b / self.random_acc

    def on_collision(self):
        self.on_collect()

    def on_collect(self):
        super().on_collect()
        # ...
        # звук монетки
        # ...


class Chest(Tile):
    def __init__(self, image, position, key_id=None):
        super().__init__(image, position)

        self.key_id = key_id
        print("init ", self)

        self.opened = False
        self.coin_image = None
        self.opened_image = None
        self.closed_image = self.image
        self.coins = 10
        self.use_text = "Сундук заперт"

    def update(self):
        super().update()
        if self.opened:
            self.use_text = ""
            self.image = self.opened_image
        else:
            self.use_text = "Сундук заперт"
            self.image = self.closed_image
            if player.picked_up_items:
                self.use_text = "Нажмите E, чтобы открыть"

    def on_use(self):
        # opened_chest_image = level.get_tile_image_by_gid()
        # self.image = opened_chest_image
        if not self.opened:
            if len(player.picked_up_items) >= 1:
                key = player.picked_up_items.pop(0)
                for i in range(self.coins):
                    x = self.rect.x + (random.randint(-8, 8)) * self.rect.width / 2
                    y = self.rect.y + (random.randint(-8, 8)) * self.rect.width / 2
                    a = Coin(self.coin_image, (x, y))
                    a.add(all_sprites)
                    coins.append(a)
                    pygame.time.set_timer(COINS_MAGNET, 100)
                key.kill()
                self.opened = True


class Teleport(Tile):

    def __init__(self, image, position, dest="Unknown"):
        super().__init__(image, position)

        self.dest = dest
        self.in_use = False

        if dest.endswith(".tmx"):
            self.dest_level = dest[:-4]
        else:
            self.dest_level = None

        self.use_text = "Нажмите E, чтобы переместиться"

    def update(self):
        super().update()

    def on_use(self):
        global FADE_OUT
        global teleport
        global color_cor_func
        super().on_use()
        if not self.in_use:
            self.in_use = True
            FADE_OUT = 1
            color_cor_func = black_screen_fade
            teleport = self
            player.paralich = True


def black_screen_fade():
    surf = color_cor
    surf.fill((0, 0, 0))
    return surf


def death_screen_fade():
    surf = color_cor
    surf.fill((0, 0, 0))
    image = load_image("death_screen.png")[0]
    surf.blit(image, (0, 0))
    return surf


class Player(pygame.sprite.Sprite):
    """Объект Игрока

        pos - кортеж с координатами в пикселях (x, y)"""

    def __init__(self, pos):
        pygame.sprite.Sprite.__init__(self)
        self.image, _ = load_image(PLAYER_IMAGE)
        self.scale = pxs_in_1px  # получаем коэфицент адаптации
        self.scale_image = self.scale  # домножаем масштаб на него

        self.image_width = self.image.get_width() * self.scale_image
        self.image_height = (self.image.get_height() + 1) * self.scale_image
        # width = round(width)
        self.image_height = round(self.image_height)
        if self.image_height % 2 != 0:
            self.image_height -= 1
            self.image_width -= 1

        # масштабируем маленькую текстуру
        self.image = pygame.transform.scale(self.image, [self.image_width, self.image_height])

        self.idle_anim = self.cut_frames(PLAYER_IDLE)
        self.walk_anim = self.cut_frames(PLAYER_WALK)
        self.run_anim = self.cut_frames(PLAYER_RUN)
        self.cur_frame = 0
        self.cur_fr_anim = 0
        self.reverse = False

        self.src_image = self.image  # запоминаем как было
        # ширина - пол высоты

        w = self.image.get_height() // 2

        self.rect = pygame.Rect(pos[0], pos[1], w, self.image.get_height())
        self.use_radius = 2

        self.use_rect = self.rect.scale_by(self.use_radius, self.use_radius)

        self.mask = pygame.mask.from_surface(pygame.surface.Surface(self.rect.size))
        self.jumping = False  # прыжок
        self.onGround = False  # тег "на земле"
        self.velocity = [.0, .0]  # вектор скорости
        self.left = False  # идём влево
        self.right = False  # идём вправо
        self.sprint = False  # бежим
        self.paralich = False
        # self.gr = None

        self.picked_up_items = []
        self.items = []

    def cut_frames(self, anim):
        image_name, n, _ = anim
        surf = load_image(image_name)[0]
        image_width = surf.get_width() * self.scale_image
        image_height = surf.get_height() * self.scale_image
        # width = round(width)
        image_height = round(image_height)
        if image_height % 2 != 0:
            image_height -= 1
            image_width -= 1
        surf = pygame.transform.scale(surf, (image_width, image_height))
        animation = []
        for i in range(n):
            new_surf = surf.subsurface(surf.get_width() // n * i, 0, surf.get_width() // n, surf.get_height())
            animation.append(new_surf)
        return animation

    def jump(self):
        if self.onGround:  # если на земле
            if not self.jumping:  # если ещё не прыгнули
                self.jumping = True  # прыгаем
                self.velocity[1] = -JUMP_V * self.scale  # ускоряемся (с адаптацией, далее - тоже)

    def update(self):
        self.onGround = False  # сбрасывает тег "на земле"
        self.velocity[0] = 0  # сбрасываем скорость
        if self.right:
            # self.image = self.src_image  # согласны, узнали?
            self.reverse = False
            # ой тут короче лень было многострочные условия делать
            self.velocity[0] = SPRINT_V * self.scale if self.sprint else WALK_V * self.scale
        if self.left:
            # self.image = pygame.transform.flip(self.src_image, 1, 0)  # разворачиваемся и уходим
            self.reverse = True
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

        self.use_rect = self.rect.scale_by(self.use_radius, self.use_radius)

        self.check_touch_danger()

        if self.velocity[0] == 0:
            current_anim = self.idle_anim
            current_anim_conf = PLAYER_IDLE
        else:
            current_anim = self.walk_anim
            current_anim_conf = PLAYER_WALK
            if self.sprint:
                current_anim = self.run_anim
                current_anim_conf = PLAYER_RUN
        self.cur_frame += 1
        if self.cur_frame >= 60 // current_anim_conf[2]:
            self.cur_frame = 0
            self.cur_fr_anim = self.cur_fr_anim + 1
        self.cur_fr_anim = self.cur_fr_anim % len(current_anim)
        self.image = self.check_reverse(current_anim[self.cur_fr_anim])

    def check_reverse(self, frame):
        if self.reverse:
            return pygame.transform.flip(frame, 1, 0)
        else:
            return frame

    def check_touch_danger(self):
        spike_collisions = []
        for spike in killing_group.sprites():
            spike_collisions.append(pygame.sprite.collide_mask(self, spike))
        if any(spike_collisions):
            self.kill()

    def check_x_collisions(self):
        collisions = pygame.sprite.spritecollide(self, collide_tiles, False)

        for tile in collisions:  # для каждого тайла, с которым можно сталкиваться
            if self.velocity[0] > 0:  # если направляемся вправо
                self.rect.right = tile.rect.left  # спотыкаемся
                self.velocity[0] = 0  # лежим
            elif self.velocity[0] < 0:  # если направляемся вправо
                self.rect.left = tile.rect.right  # спотыкаемся
                self.velocity[0] = 0  # лежим

    def check_y_collisions(self):
        collisions = pygame.sprite.spritecollide(self, collide_tiles, False)

        for tile in collisions:  # для каждого тайла, с которым можно сталкиваться
            if self.velocity[1] > 0:  # если летим вниз
                self.rect.bottom = tile.rect.top  # ударёмся ногой
                self.onGround = True  # упали на землю
                self.velocity[1] = 0  # лежим
            elif self.velocity[1] < 0:  # если прягаем вверх
                self.rect.top = tile.rect.bottom  # ударёмся головой
                self.velocity[1] = 0  # не мотаем головой лишний раз


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
                               'bottom': screen.get_height() * 0.2}
        l = self.camera_borders['left']
        t = self.camera_borders['top']
        w = self.display_surface.get_size()[0] - (self.camera_borders['left'] + self.camera_borders['right'])
        h = self.display_surface.get_size()[1] - (self.camera_borders['top'] + self.camera_borders['bottom'])
        self.camera_rect = pygame.Rect(l, t, w, h)

        self.level = None
        self.bg_image = "bg.jpg"

        # ground
        self.background_surf = load_image(self.bg_image)[0]
        # self.background_surf = pygame.transform.scale(self.background_surf, (screen.get_width()*3, self.background_surf.get_height()))
        self.background_rect = self.background_surf.get_rect(topleft=(0, 0))

        # camera speed
        self.keyboard_speed = 5
        self.mouse_speed = 0.2

        # zoom
        self.zoom_scale = 1
        self.internal_surf_size = (screen.get_width(), screen.get_height())
        self.internal_surf = pygame.Surface(self.internal_surf_size, pygame.SRCALPHA)

        self.text_surf_size = (screen.get_width(), screen.get_height())
        self.text_surf = pygame.Surface(self.internal_surf_size, pygame.SRCALPHA)

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
        self.text_surf.fill((0, 0, 0, 0))

        if self.level:
            width = round(self.level.width * self.level.tilewidth * player.scale * pxs_in_1px)
            height = round(self.level.height * self.level.tilewidth * player.scale * pxs_in_1px)
            if self.background_surf.get_width() != width:
                self.background_surf = load_image(self.bg_image)[0]
                self.background_surf = pygame.transform.scale(self.background_surf, (width, height))
                self.background_rect = self.background_surf.get_rect(topleft=(0, 0))

        # self.center_target_camera(player)
        self.box_target_camera(player)
        # self.keyboard_control()
        # self.mouse_control()
        # self.zoom_keyboard_control()

        self.internal_surf.fill('#71ddee')  # льём небо

        # ground
        ground_offset = self.background_rect.topleft - self.offset + self.internal_offset
        self.internal_surf.blit(self.background_surf, ground_offset)

        # active elements
        for sprite in self.sprites():
            offset_pos = sprite.rect.topleft - self.offset + self.internal_offset
            if isinstance(sprite, Player):
                offset_pos.x -= sprite.image.get_width() / 4
                offset_pos.y += (sprite.rect.h - sprite.image.get_height())

                pass

            self.internal_surf.blit(sprite.image, offset_pos)
            if isinstance(sprite, (Chest, Teleport)):
                # pygame.draw.rect(self.internal_surf, "red", (offset_pos, sprite.rect.size))
                if sprite.display_text:
                    font = pygame.font.Font(None, 30)
                    string_rendered = font.render(sprite.display_text, 1, pygame.Color('black'))
                    pos = offset_pos
                    self.text_surf.blit(string_rendered,
                                        ((pos[0] + sprite.rect.w // 2) - string_rendered.get_width() // 2,
                                         pos[1] - string_rendered.get_height()))

        # scaled_surf = pygame.transform.scale(self.internal_surf, self.internal_surface_size_vector * self.zoom_scale)
        scaled_rect = self.internal_surf.get_rect(center=(self.half_w, self.half_h))

        self.display_surface.blit(self.internal_surf, scaled_rect)
        self.display_surface.blit(self.text_surf, self.text_surf.get_rect(center=(self.half_w, self.half_h)))


pygame.init()  # да
screen = pygame.display.set_mode((0, 0), flags=pygame.FULLSCREEN)  # на весь экран, размер окна - автоматически
print("Обнаружен экран с разрешением", screen.get_size())
pxs_in_1px = round((screen.get_width() // 25) * 6 / (1920 // 25))
print(pxs_in_1px)

# лирическое отступление: Если в windows в параметрах экрана установлен масштаб, отличный от 100 процентов, то
# разрешение определяется с учётом этого масштаба, причём в меньшую сторону. Если масштаб 100, то разрешение
# определяется сразу и игра запускается сразу, без кат-сцен в виде мигающего черного экрана. Читы на пропуск кат-сцены
# В общем игра отображется везде одинаково, так что и ладно.

color_cor = pygame.Surface(screen.get_size())

clock = pygame.time.Clock()  # часы
running = True  # куда бежим
dt = 0  # что это воще

# определёем группы спрайтов
all_sprites = CameraGroup()  # группа всех спрайтов, что движимы камерой
player_group = pygame.sprite.Group()  # группа игрока, ладно
collide_tiles = pygame.sprite.Group()  # группа всех спрайтов, что божьей силой не дают провалиться сквозь них
killing_group = pygame.sprite.Group()

player = Player((0, 0))  # первое зарождение игрока, и да, когда-то давно он жил на (0;0), и что?
player.add(player_group)  # инвайтим в группу

level, level_scale = gen_level("levels/level1.tmx")  # да, сначала появился игрок, потом весь мир, и что?

# player.add(all_sprites)  # он такое же существо, как и все эти... камни?

debug_text = []
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
        if event.type == COINS_MAGNET:
            for i in coins:
                i.magnet = True

    screen.fill("purple")  # льём затекстурье. эм... а зачем?...

    all_sprites.update()
    all_sprites.custom_draw(player)  # кастомно применяем алгоритмы камеры

    player.right, player.left, player.sprint = False, False, False  # сбрасываем

    keys = pygame.key.get_pressed()  # какие кнопочки классные!!! (получаем список нажатых кнопок)
    if keys and not player.paralich:
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
        if color_cor_func != death_screen_fade:
            FADE_OUT = 1
            color_cor_func = death_screen_fade
        if keys[pygame.K_r]:
            print("Restarting...")
            restart(CURRENT_LEVEL)
            color_cor_func = black_screen_fade
            FADE_OUT = 256 + 5

    # HUD
    items = {}
    if player.items:
        for item in player.items:

            if items.get(item.name):
                count = items[item.name][0] + 1
                items[item.name] = (count, item)
            else:
                count = 1
                items[item.name] = (count, item)
        # print(items)

        for name, (count, obj) in items.items():
            screen.blit(obj.image, (0, 0))
            font = pygame.font.Font(None, 30)
            string_rendered = font.render(str(count), 1, pygame.Color('black'))
            screen.blit(string_rendered, (obj.image.get_width() + 10, obj.image.get_height() // 2))

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
                      f"SPRINT {player.sprint}",
                      f"CUR_FR_ANIM {player.cur_fr_anim}",
                      f"CUR_FR {player.cur_frame}",
                      f"FADE {FADE_OUT}"]

    if FADE_OUT == 1:
        color_cor_func()

    if FADE_OUT == -1:
        color_cor.set_alpha(255)
        screen.blit(color_cor, (0, 0))

    elif 0 < FADE_OUT < 256:
        # color_cor.fill(pygame.Color(0, 0, 0))
        # color_cor_func()
        color_cor.set_alpha(FADE_OUT)
        screen.blit(color_cor, (0, 0))
        FADE_OUT += 5
    elif 256 <= FADE_OUT <= 256 + 256:
        # color_cor.fill(pygame.Color(0, 0, 0))
        # color_cor_func()
        color_cor.set_alpha(256 * 2 - FADE_OUT)
        screen.blit(color_cor, (0, 0))
        FADE_OUT += 5
    else:
        FADE_OUT = 0

    if FADE_OUT == 256:
        if teleport:
            CURRENT_LEVEL = teleport.dest
            restart(CURRENT_LEVEL)
            teleport = None
        if not player.groups():
            FADE_OUT = -1

    pygame.display.flip()  # обновляем кадр

    # limits FPS to 60
    # dt is delta time in seconds since last frame, used for framerate-
    # independent physics.
    dt = clock.tick(60) / 1000  # считаем кадры

pygame.quit()  # выйдите
