import contextlib
import contextvars
import dataclasses
import math
from dataclasses import dataclass

import numpy as np

from render import ColorLine, ElegantLine


class Parameter:
    def __init__(self,
        name, key, default,
        places=1, scale=1.0, adjacent_step=None,
        adjacent=None, random=None, to_short=None, from_short=None,
    ):
        self.name = name
        self.key = key
        self.default = default
        self.places = places
        self.scale = scale
        self.adjacent_step = adjacent_step
        self.random = random
        if adjacent is not None:
            self.adjacent = adjacent
        if to_short is not None:
            self.to_short = to_short
        if from_short is not None:
            self.from_short = from_short

    def adjacent(self, v):
        d = self.adjacent_step
        if d is None:
            return []
        else:
            return [v - 2 * d, v - d, v + d, v + 2 * d]

    def to_short(self, v):
        if isinstance(self.default, float):
            return str(int(v / self.scale * 10 ** self.places))
        else:
            return str(v)

    def from_short(self, s):
        if isinstance(self.default, float):
            return float(s) / 10 ** self.places * self.scale
        else:
            return int(s)

    def repr(self, v):
        if isinstance(self.default, float):
            return format(v, f".{self.places}f")
        else:
            return repr(v)


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

@contextlib.contextmanager
def ctx(cvar, val):
    token = cvar.set(val)
    try:
        yield
    finally:
        cvar.reset(token)

amp = contextvars.ContextVar("amp")
freq = contextvars.ContextVar("freq")

@dataclass
class FullWave(Parameterized):
    freq: Parameter(
        name="frequency",
        key="f",
        default=2,
        adjacent_step=1,
        random=lambda rnd: rnd.randrange(*freq.get((1, 6, 1))),
        )
    amp: Parameter(
        name="amplitude",
        key="a",
        default=.5,
        places=3,
        adjacent_step=.2,
        random=lambda rnd: rnd.uniform(0.1, amp.get(1.0)),
        )
    tweq: Parameter(
        name="frequency tweak",
        key="t",
        default=0.0,
        places=6,
        adjacent_step=.0004,
        random=lambda rnd: rnd.gauss(0, .005),
        )
    phase: Parameter(
        name="phase",
        key="p",
        default=0.0,
        places=4,
        scale=2 * math.pi,
        adjacent_step=.2,
        random=lambda rnd: rnd.uniform(0, 2 * math.pi),
        )

    def __call__(self, t, density=1):
        return self.amp * np.sin((self.freq * density + self.tweq) * t + self.phase)

    @classmethod
    def make_random(cls, name, rnd, limit=None):
        freqq = (1, 7, 1)
        if limit == "even":
            freqq = (2, 7, 2)
        elif limit == "odd":
            freqq = (1, 7, 2)

        with ctx(freq, freqq):
            return super().make_random(name, rnd)


@dataclass
class Ramp(Parameterized):
    stop: Parameter(
        name="stop",
        key="z",
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
        adjacent_step=100,
        )
    width: Parameter(
        name="width",
        key="w",
        default=200,
        adjacent_step=50,
        )


STYLES = [
    ElegantLine(linewidth=3, alpha=1),
    ColorLine(lightness=0, linewidth=50, alpha=.1),
    ColorLine(linewidth=10, alpha=.5),
    ColorLine(linewidth=50, alpha=.1),
]

@dataclass
class Harmonograph(Parameterized):
    density: Parameter(
        name="density",
        key="d",
        default=1.0,
        places=2,
        adjacent=lambda v: [v*.8*.8, v*.8, v/.8, v/.8/.8],
        )
    style: Parameter(
        name="style",
        key="s",
        default=0,
        adjacent=lambda _: list(range(len(STYLES))),
        )

    def __init__(self, name="", density=1.0, style=0):
        self.name = name
        self.density = density
        self.style = style
        self.dimensions = {}
        self.set_time_span(TimeSpan("ts", 900, 200))
        self.extras = set()
        self.render = STYLES[style]

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
            step=dt / self.density,
        )
        pts = []
        for dim_name in dims:
            dim = self.dimensions[dim_name]
            val = 0.0
            for wave in dim:
                val += wave(t, self.density)
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

    @classmethod
    def make_from_short_params(cls, params):
        # Deduce the number of pendulums from the parameters
        xs = set(k[1] for k in params if k.startswith("x"))
        npend = len(xs)

        harm = cls.from_short_params("", params)
        harm.add_dimension("x", [FullWave.from_short_params(f"x{abc(i)}", params) for i in range(npend)])
        harm.add_dimension("y", [FullWave.from_short_params(f"y{abc(i)}", params) for i in range(npend)])
        harm.add_dimension("j", [FullWave.from_short_params("j", params)], extra=True)
        harm.set_ramp(Ramp.from_short_params("r", params))
        harm.set_time_span(TimeSpan.from_short_params("ts", params))
        return harm

    @classmethod
    def make_random(cls, rnd, npend, syms, rampstop=500):
        sym = rnd.choice(syms)
        xlimit = ylimit = None
        if sym == "X":
            xlimit = "odd"
            ylimit = "even"
        elif sym == "Y":
            xlimit = "even"
            ylimit = "odd"
        elif sym == "R":
            xlimit = ylimit = "odd"
        harm = Harmonograph()
        harm.add_dimension("x", [FullWave.make_random(f"x{abc(i)}", rnd, limit=xlimit) for i in range(npend)])
        harm.add_dimension("y", [FullWave.make_random(f"y{abc(i)}", rnd, limit=ylimit) for i in range(npend)])
        harm.add_dimension("j", [FullWave.make_random("j", rnd)], extra=True)
        harm.set_ramp(Ramp("r", rampstop))
        return harm

def abc(i):
    return "abcdefghijklmnopqrstuvwxyz"[i]
