from enum import Enum
from yaml import YAMLError, safe_load


def dictclass(cls):
    class DictClass(cls):
        def __init__(self, yaml: dict):
            for prop, value in yaml.items():
                self.__setattr__(prop, value)
    return DictClass


class Config:
    @dictclass
    class Window:
        width: int
        height: int
        background: str

    @dictclass
    class Paddle():
        width: int
        height: int
        speed: int

    @dictclass
    class Ball:
        radius: int
        speed: int

        @property
        def rect(self):
            return int(self.radius * 2 ** 0.5)

    @dictclass
    class Block:
        pad_w: int
        pad_h: int
        block_w: int
        block_h: int
        n: int
        m: int

    sounds = {
        "brick_hit": "./arkanoid/sounds/brick_hit.mp3",
        "background_music": "./arkanoid/sounds/background_music.mp3"
    }

    def __init__(self, yaml: dict):
        self.window = self.Window(yaml['window'])
        self.paddle = self.Paddle(yaml['paddle'])
        self.ball = self.Ball(yaml['ball'])
        self.block = self.Block(yaml['block'])


class GameLevel(Enum):
    Velocity = 1
    Cascade = 2
    Nexus = 3
    Inferno = 4
    Odyssey = 5


def load_config(level: GameLevel):
    config_path = f"arkanoid/levels/{level.name}.yaml"
    with open(config_path, 'r', encoding='UTF-8') as stream:
        try:
            yaml = safe_load(stream)
            if yaml is None:
                raise TypeError(f"Config '{config_path}' cannot be empty")
            if not isinstance(yaml, dict):
                raise TypeError(
                    f"Invalid config '{config_path}': " +
                    f"{dict} expected, but {type(yaml)} found")
            return Config(yaml)
        except YAMLError as error:
            print(error)
            exit(1)
