# http://paulbourke.net/geometry/harmonograph/
# https://github.com/tuxar-uk/Harmonumpyplot

import dataclasses
import math
import random
from dataclasses import dataclass

import numpy as np

WIDTH, HEIGHT = 2048, 2048
DRAWW = WIDTH * .9
DRAWH = HEIGHT * .9


def make_random(seed=None):
    consonants = "bcdfghjklmnprstvwz"
    vowels = "aeiou"
    if seed is None:
        rnd = random.Random()
        seed = "".join([
            rnd.choice(consonants),
            rnd.choice(vowels),
            rnd.choice(consonants),
            rnd.choice(vowels),
            rnd.choice(consonants),
            rnd.choice(vowels),
            rnd.choice(consonants),
            rnd.choice(vowels),
            rnd.choice(consonants),
            rnd.choice(vowels),
            rnd.choice(consonants),
            str(rnd.randint(1, 99)),
        ])
    rnd = random.Random()
    rnd.seed(seed)
    return seed, rnd


@dataclass
class Parameter:
    name: str
    key: str
    default: float
    adjacent: object = lambda v: []
    random: object = None
    to_short: object = None
    from_short: object = None

@dataclass
class Parameterized:
    name: str

    @classmethod
    def paramdefs(cls):
        for field in dataclasses.fields(cls):
            if not isinstance(field.type, Parameter):
                continue
            yield field

    @classmethod
    def make_random(cls, name, rnd=random):
        kwargs = {}
        for field in cls.paramdefs():
            if field.type.random:
                val = field.type.random(rnd)
            else:
                val = field.type.default
            kwargs[field.name] = val
        return cls(name=name, **kwargs)

    @classmethod
    def from_params(cls, name, params):
        kwargs = {}
        for field in cls.paramdefs():
            key = name + field.type.key
            if key in params:
                val = params[key]
            else:
                val = field.type.default
            kwargs[field.name] = val
        return cls(name=name, **kwargs)

    @classmethod
    def from_short_params(cls, name, params):
        kwargs = {}
        for field in cls.paramdefs():
            key = name + field.type.key
            if key in params:
                val = params[key]
                val = (field.type.from_short or int)(val)
            else:
                val = field.type.default
            kwargs[field.name] = val
        return cls(name=name, **kwargs)

    def param_things(self):
        return self

    def parameters(self):
        for thing in self.param_things():
            for field in thing.paramdefs():
                key = thing.name + field.type.key
                yield (field, thing, getattr(thing, field.name))

    def short_parameters(self):
        shorts = {}
        for thing in self.param_things():
            for field in thing.paramdefs():
                key = thing.name + field.type.key
                val = getattr(thing, field.name)
                if field.type.to_short:
                    val = field.type.to_short(val)
                shorts[key] = str(val)
        return shorts

@dataclass
class FullWave(Parameterized):
    freq: Parameter(
        name="frequency",
        key="f",
        default=2,
        random=lambda rnd: rnd.randint(1, 5),
        )
    amp: Parameter(
        name="amplitude",
        key="a",
        default=.5,
        adjacent=lambda v: [v-.2, v-.1, v+.1, v+.2],
        random=lambda rnd: rnd.uniform(0, 1),
        to_short=lambda v: int(v * 1000),
        from_short=lambda s: float(s) / 1000,
        )
    tweq: Parameter(
        name="frequency tweak",
        key="t",
        default=0.0,
        adjacent=lambda v: [v-.0005, v-.00025, v+.00025, v+.0005],
        random=lambda rnd: rnd.gauss(0, .005),
        to_short=lambda v: int(v * 1_000_000),
        from_short=lambda s: float(s) / 1_000_000,
        )
    phase: Parameter(
        name="phase",
        key="p",
        default=0.0,
        adjacent=lambda v: [v-.3, v-.15, v+.15, v+.3],
        random=lambda rnd: rnd.uniform(0, 2 * math.pi),
        to_short=lambda v: int(v / (2 * math.pi) * 10000),
        from_short=lambda s: float(s) / 10000 * 2 * math.pi,
        )

    def __post_init__(self):
        self.signal = _Wave(self.amp, self.freq + self.tweq, self.phase)

    def __call__(self, t):
        return self.signal(t)


@dataclass
class _Wave:
    amp: float
    freq: float
    phase: float = 0.0
    offset: float = 0.0

    def __call__(self, t):
        return self.amp * np.sin(self.freq * t + self.phase) + self.offset

def Wave(amp=None, freq=None, phase=0.0, min=None, max=None):
    if amp is None:
        amp = (max - min) / 2
        offset = (min + max) / 2
    else:
        offset = 0.0
    return _Wave(amp, freq, phase, offset)

@dataclass
class Decay:
    signal: object
    decay: float = 0.02

    def __call__(self, t):
        return np.exp(-self.decay * t) * self.signal(t)


@dataclass
class Ramp(Parameterized):
    stop: Parameter(
        name="stop",
        key="stop",
        default=500,
        )

    def __call__(self, t):
        return t / self.stop


def RandWave(rnd, amp, nfreq, sigma, stop):
    wave = Wave(
        amp=rnd.uniform(0, amp),
        freq=rnd.randint(1, nfreq) + rnd.gauss(0, sigma),
        phase=rnd.uniform(0, 2*math.pi)
    )
    return Ramp(wave, stop=stop)

class Harmonograph(Parameterized):
    def __init__(self):
        self.dimensions = []

    def add_dimension(self, waves):
        self.dimensions.append(waves)

    def set_ramp(self, ramp):
        self.ramp = ramp

    def points(self, start=0, stop=100, dt=.01):
        t = np.arange(start=start, stop=stop, step=dt)
        pts = []
        for dim in self.dimensions:
            val = 0.0
            for wave in dim:
                val += wave(t)
            val *= self.ramp(t)
            pts.append(val)
        for pt in zip(*pts):
            yield pt

    def param_things(self):
        for dim in self.dimensions:
            for wave in dim:
                yield wave
        yield self.ramp
