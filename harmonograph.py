import dataclasses
import math
from dataclasses import dataclass

import numpy as np

WIDTH, HEIGHT = 2048, 2048
DRAWW = WIDTH * .9
DRAWH = HEIGHT * .9


@dataclass
class Parameter:
    name: str
    key: str
    default: float
    adjacent: object = lambda v: []
    random: object = None
    to_short: object = str
    from_short: object = int
    repr: object = lambda v: format(v, ".3f")

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
    def make_random(cls, name, rnd):
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
        """
        Produce all your things with parameters, and their extra-name if
        they are extra.
        """
        yield self, None

    def parameters(self):
        for thing, extra_name in self.param_things():
            for field in thing.paramdefs():
                yield (field, thing, extra_name, getattr(thing, field.name))

    def short_parameters(self):
        shorts = {}
        for thing, extra_name in self.param_things():
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
        adjacent=lambda v: [v-2, v-1, v+1, v+2],
        random=lambda rnd: rnd.randint(1, 5),
        repr=repr,
        )
    amp: Parameter(
        name="amplitude",
        key="a",
        default=.5,
        adjacent=lambda v: [v-.4, v-.2, v+.2, v+.4],
        random=lambda rnd: rnd.uniform(0, 1),
        to_short=lambda v: int(v * 1000),
        from_short=lambda s: float(s) / 1000,
        )
    tweq: Parameter(
        name="frequency tweak",
        key="t",
        default=0.0,
        adjacent=lambda v: [v-.0008, v-.0004, v+.0004, v+.0008],
        random=lambda rnd: rnd.gauss(0, .005),
        to_short=lambda v: int(v * 1_000_000),
        from_short=lambda s: float(s) / 1_000_000,
        repr=lambda v: format(v, ".6f")
        )
    phase: Parameter(
        name="phase",
        key="p",
        default=0.0,
        adjacent=lambda v: [v-.4, v-.2, v+.2, v+.4],
        random=lambda rnd: rnd.uniform(0, 2 * math.pi),
        to_short=lambda v: int(v / (2 * math.pi) * 10000),
        from_short=lambda s: float(s) / 10000 * 2 * math.pi,
        )

    def __call__(self, t, speed=1):
        return self.amp * np.sin((self.freq * speed + self.tweq) * t + self.phase)


@dataclass
class Ramp(Parameterized):
    stop: Parameter(
        name="stop",
        key="stop",
        default=500,
        )

    def __call__(self, t):
        return t / self.stop


@dataclass
class TimeSpan(Parameterized):
    center: Parameter(
        name="center",
        key="c",
        default=900,
        adjacent=lambda v: [v-200, v-100, v+100, v+200],
        repr=repr,
        )
    width: Parameter(
        name="width",
        key="w",
        default=200,
        adjacent=lambda v: [v-100, v-50, v+50, v+100],
        repr=repr,
        )

@dataclass
class Harmonograph(Parameterized):
    speed: Parameter(
        name="speed",
        key="sp",
        default=1.0,
        adjacent=lambda v: [v*.6, v*.8, v*1.2, v*1.4],
        to_short=lambda v: int(v * 100),
        from_short=lambda s: float(s) / 100,
        )

    def __init__(self, name="", speed=1.0):
        self.name = name
        self.speed = speed
        self.dimensions = {}
        self.set_time_span(TimeSpan("ts", 900, 200))
        self.extras = set()

    def add_dimension(self, name, waves, extra=False):
        self.dimensions[name] = waves
        if extra:
            self.extras.add(name)

    def set_ramp(self, ramp):
        self.ramp = ramp

    def set_time_span(self, timespan):
        self.timespan = timespan

    def points(self, dims, dt=.01):
        ts_half = self.timespan.width // 2
        t = np.arange(
            start=self.timespan.center - ts_half,
            stop=self.timespan.center + ts_half,
            step=dt,
        )
        pts = []
        for dim_name in dims:
            dim = self.dimensions[dim_name]
            val = 0.0
            for wave in dim:
                val += wave(t, self.speed)
            val *= self.ramp(t)
            pts.append(val)
        for pt in zip(*pts):
            yield pt

    def param_things(self):
        for dim_name, dim in self.dimensions.items():
            for wave in dim:
                yield wave, (dim_name if dim_name in self.extras else None)
        yield self, None
        yield self.timespan, None
        yield self.ramp, None
