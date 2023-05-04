from math import sin, cos, pi
import pygame
from enum import Enum
from random import randrange as random

from .config import Config, GameLevel, load_config


class GameResult(Enum):
    LOSE = 0
    WIN = 1


class AppState(Enum):
    PLAYING = 0
    GAME_OVER = 1
    LEVEL = 2
    HELP = 3


class Engine:
    dx = cos(pi / 6)
    dy = -sin(pi / 6)
    game_result: GameResult | None = None
    state = AppState.LEVEL
    supermode = False

    def __init__(self):
        pygame.init()
        self.config = load_config(GameLevel.Velocity)
        self.screen = pygame.display.set_mode((
            self.config.window.width,
            self.config.window.height
        ))
        self.clock = pygame.time.Clock()
        self.sound_effects = {name: pygame.mixer.Sound(
            sound) for name, sound in self.config.sounds.items()}
        self.sound_effects["background_music"].play()

    def change_level(self, level: GameLevel):
        self.config = load_config(level)
        self.screen = pygame.display.set_mode((
            self.config.window.width,
            self.config.window.height
        ))

    def start(self):
        self.fps = 60
        self.image = pygame.image.load(self.config.window.background).convert()
        self.paddle = Paddle(self.config)
        self.ball = Ball(self.config)
        self.blocks = Blocks(self.config)
        self.colors = Colors(self.config)
        dialog_shown = False
        selected_level: GameLevel | None = None
        while (True):
            if self.state == AppState.PLAYING:
                self.play()
            elif self.state == AppState.LEVEL:
                self.level_menu_modal(selected_level)
                key = pygame.key.get_pressed()
                if key[pygame.K_1]:
                    selected_level = GameLevel.Velocity
                if key[pygame.K_2]:
                    selected_level = GameLevel.Cascade
                if key[pygame.K_3]:
                    selected_level = GameLevel.Nexus
                if key[pygame.K_4]:
                    selected_level = GameLevel.Inferno
                if key[pygame.K_5]:
                    selected_level = GameLevel.Odyssey
                if key[pygame.K_RETURN]:
                    if selected_level:
                        self.change_level(selected_level)
                        self.state = AppState.PLAYING
                        self.game_result = None
                        self.start()
                        return
                if key[pygame.K_h]:
                    self.state = AppState.HELP
            elif self.state == AppState.GAME_OVER:
                if not dialog_shown:
                    dialog_shown = True
                    self.game_over_modal()
                # control
                key = pygame.key.get_pressed()
                if key[pygame.K_n]:
                    self.state = AppState.PLAYING
                    self.game_result = None
                    self.start()
                    return
                if key[pygame.K_q]:
                    return
                if key[pygame.K_s]:
                    self.state = AppState.LEVEL
                if key[pygame.K_h]:
                    self.state = AppState.HELP
            elif self.state == AppState.HELP:
                self.help_modal()
                key = pygame.key.get_pressed()
                if key[pygame.K_RETURN] or key[pygame.K_ESCAPE]:
                    self.state = AppState.LEVEL
            self.handle_events()
            pygame.display.flip()
            self.clock.tick(self.fps)

    def get_message_printer(self, height=0):
        height += self.config.window.height // 2

        def print_message(message: str, font_size: int, color: str, offset: int | None = None):
            nonlocal height
            height += offset if offset is not None else int(font_size * 1.5)
            font = pygame.font.SysFont('Hack', font_size)
            text = font.render(message, True, pygame.Color(color))
            textRect = text.get_rect()
            textRect.center = (self.config.window.width // 2, height)
            self.screen.blit(text, textRect)
        return print_message

    @staticmethod
    def handle_events():
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit()

    @staticmethod
    def detect_collision(dx, dy, ball, rect):
        if dx > 0:
            delta_x = ball.right - rect.left
        else:
            delta_x = rect.right - ball.left
        if dy > 0:
            delta_y = ball.bottom - rect.top
        else:
            delta_y = rect.bottom - ball.top

        if abs(delta_x - delta_y) < 10:
            dx, dy = -dx, -dy
        elif delta_x > delta_y:
            dy = -dy
        elif delta_y > delta_x:
            dx = -dx
        return dx, dy

    def play(self):
        self.screen.blit(self.image, (0, 0))
        old_dx = self.dx
        old_dy = self.dy

        # drawing world
        for index, block in enumerate(self.blocks):
            pygame.draw.rect(self.screen, self.colors[index], block)
        pygame.draw.rect(self.screen, pygame.Color('darkorange'), self.paddle)
        ball_color = 'red' if self.supermode else 'white'
        pygame.draw.circle(self.screen, pygame.Color(
            ball_color), self.ball.center, self.config.ball.radius)

        # ball movement
        self.ball.x += self.config.ball.speed * \
            self.dx * (8 if self.supermode else 1)
        self.ball.y += self.config.ball.speed * \
            self.dy * (8 if self.supermode else 1)

        # collision left and right
        if self.ball.centerx < self.config.ball.radius or self.ball.centerx > self.config.window.width - self.config.ball.radius:
            self.dx = -self.dx

        # collision top
        if self.ball.centery < self.config.ball.radius:
            self.dy = -self.dy

        # collision paddle
        if self.ball.colliderect(self.paddle) and self.dy > 0:
            self.dx, self.dy = self.detect_collision(
                self.dx, self.dy, self.ball, self.paddle)
            delta = random(2, 6)
            self.dx = cos(pi / delta) * (-1 if self.dx < 0 else 1)
            self.dy = -sin(pi / delta)

        # collision blocks
        hit_index = self.ball.collidelist(self.blocks)
        if hit_index != -1:
            hit_rect = self.blocks.pop(hit_index)
            hit_color = self.colors.pop(hit_index)
            self.dx, self.dy = self.detect_collision(
                self.dx, self.dy, self.ball, hit_rect)
            # special effect
            hit_rect.inflate_ip(self.ball.width * 3, self.ball.height * 3)
            pygame.draw.rect(self.screen, hit_color, hit_rect)
            if self.fps < 100:
                self.fps += 2

        # win, game over
        if self.ball.bottom > self.config.window.height:
            if self.supermode:
                self.dy = -1
            else:
                self.dy = -self.dy
                self.game_result = GameResult.LOSE
                self.state = AppState.GAME_OVER
            return
        elif not len(self.blocks):
            self.game_result = GameResult.WIN
            self.state = AppState.GAME_OVER
            return

        if old_dx != self.dx or old_dy != self.dy:
            self.sound_effects["brick_hit"].play()

        # control
        key = pygame.key.get_pressed()
        if key[pygame.K_LEFT] and self.paddle.left > 0:
            self.paddle.left -= self.config.paddle.speed
        if key[pygame.K_RIGHT] and self.paddle.right < self.config.window.width:
            self.paddle.right += self.config.paddle.speed
        if key[pygame.K_SPACE]:
            self.supermode = True
        if key[pygame.K_ESCAPE]:
            self.supermode = False
        if key[pygame.K_q]:
            exit()
        if key[pygame.K_s]:
            self.state = AppState.LEVEL

    def game_over_modal(self):
        dim = pygame.Surface(
            (self.config.window.width, self.config.window.height), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 200))
        self.screen.blit(dim, (0, 0))

        print_message = self.get_message_printer(-130)

        if self.game_result == GameResult.WIN:
            message = 'Вы победили!'
        else:
            message = 'Вы проиграли!'

        print_message(message, 30, 'White')

        print_message('(q) exit        ', 20, 'White', 60)
        print_message('(n) new game    ', 20, 'White')
        print_message('(s) select level', 20, 'White')
        print_message('(h) help        ', 20, 'White', 50)

    def level_menu_modal(self, selected_level: GameLevel | None):
        self.screen.blit(self.image, (0, 0))

        dim = pygame.Surface(
            (self.config.window.width, self.config.window.height), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 200))
        self.screen.blit(dim, (0, 0))

        print_message = self.get_message_printer(-130)
        print_message('Выберите уровень:', 30, 'White')

        def is_active(
            n): return 'Orange' if selected_level and selected_level.value == n else 'White'

        print_message('(1) Velocity', 20, is_active(1), 60)
        print_message('(2) Cascade ', 20, is_active(2))
        print_message('(3) Nexus   ', 20, is_active(3))
        print_message('(4) Inferno ', 20, is_active(4))
        print_message('(5) Odyssey ', 20, is_active(5))
        print_message('(h) help    ', 20, 'White', 50)

    def help_modal(self):
        self.screen.blit(self.image, (0, 0))

        dim = pygame.Surface(
            (self.config.window.width, self.config.window.height), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 200))
        self.screen.blit(dim, (0, 0))

        print_message = self.get_message_printer(-130)
        print_message('Правила игры:', 30, 'White')

        print_message(
            '  Арканоид - это игра, в которой нужно управлять   ', 20, 'White', 60)
        print_message(
            '  платформой для отбивания мячика в блоки,         ', 20, 'White')
        print_message(
            '  расположенные сверху экрана. Цель - уничтожить   ', 20, 'White')
        print_message(
            '  все блоки, не давая мячику упасть вниз. Если     ', 20, 'White')
        print_message(
            '  мячик упадёт - игрок проигрывает. На выбор       ', 20, 'White')
        print_message(
            '  предоставляются разные уровни, у которых         ', 20, 'White')
        print_message(
            '  различная сложность и размещение блоков.         ', 20, 'White')
        print_message(
            '  Используйте клавиши ← и → для движения платформы.', 20, 'White')
        print_message(
            '                                          [Ok]     ', 20, 'White', 60)

        pass


def Paddle(config: Config):
    return pygame.Rect(
        config.window.width // 2 - config.paddle.width // 2,
        config.window.height - config.paddle.height - 10,
        config.paddle.width,
        config.paddle.height
    )


def Ball(config: Config):
    return pygame.Rect(
        config.window.width // 2 - config.ball.rect,
        config.window.height // 2,
        config.ball.rect,
        config.ball.rect
    )


def Blocks(config: Config):
    return [
        pygame.Rect(
            config.block.pad_w + (config.block.block_w +
                                  config.block.pad_w * 2) * i,
            config.block.pad_h + (config.block.block_h +
                                  config.block.pad_h * 2) * j,
            config.block.block_w,
            config.block.block_h
        )
        for i in range(config.block.n) for j in range(config.block.m)
    ]


def Colors(config: Config):
    return [
        (random(40, 256), random(40, 256), random(40, 256))
        for i in range(config.block.n) for j in range(config.block.m)
    ]
