import math
from dataclasses import dataclass

import numpy as np

from curve import Curve
from parameter import Parameter, Parameterized
from util import abc


@dataclass
class Circle:
    r: float
    speed: float

    def __call__(self, t):
        """Returns x,y"""
        tt = t * self.speed
        return (self.r * np.sin(tt), self.r * np.cos(tt))


def adjacent_teeth(t):
    """Calculate adjacent teeth values.

    Four values, not less than 1, not including the current value.
    """
    low = max(t - 2, 1)
    high = t + 2
    l = list(range(low, high + 1))
    l.remove(t)
    return l

@dataclass
class Gear(Parameterized):
    teeth: Parameter(
        name="teeth",
        key="t",
        default=12,
        adjacent=adjacent_teeth,
    )
    inside: Parameter(
        name="inside",
        key="i",
        default=1,
        adjacent=lambda i: [1 - i],
        random=lambda rnd: rnd.choice([0, 1]),
    )


@dataclass
class Spirograph(Curve):
    ALGORITHM = 2

    outer_teeth: Parameter(
        name="outer_teeth",
        key="o",
        default=144,
        adjacent_step=1,
    )
    # Gears are in self.gears
    pen_extra: Parameter(
        name="pen_extra",
        key="p",
        default=0.0,
        places=2,
        adjacent_step=.5,
    )

    def __init__(self, outer_teeth=144, pen_extra=0.0):
        super().__init__()
        self.outer_teeth = outer_teeth
        self.pen_extra = pen_extra
        self.gears = []

    def param_things(self):
        yield self, None
        for gear in self.gears:
            yield gear, None

    @classmethod
    def from_params(cls, params, name=""):
        assert name == ""

        ngears = len(set(k[1] for k in params if k.startswith("g")))
        curve = super().from_params(params)
        for gi in range(ngears):
            curve.gears.append(Gear.from_params(params, f"g{abc(gi)}"))
        return curve

    @classmethod
    def make_random(cls, rnd):
        curve = cls()
        curve.outer_teeth = 144
        curve.gears.append(Gear(name="ga", teeth=rnd.randint(10,40), inside=rnd.choice([0,1])))
        curve.gears.append(Gear(name="gb", teeth=rnd.randint(5,10), inside=rnd.choice([0,1])))
        curve.pen_extra = rnd.randint(0, 5) * .5
        return curve

    @classmethod
    def make_one(cls):
        curve = cls()
        curve.outer_teeth = 144
        curve.gears.append(Gear(name="ga", teeth=42, inside=1))
        curve.gears.append(Gear(name="gb", teeth=6, inside=0))
        curve.pen_extra = 10.25
        return curve

    def _make_circles(self):
        circles = [Circle(r=1.0, speed=1)]
        last_teeth = self.outer_teeth
        last_radius = 1.0
        cycles = 1
        for gear in self.gears:
            this_fraction = gear.teeth / last_teeth
            cycles *= gear.teeth // math.gcd(last_teeth, gear.teeth)
            this_radius = last_radius * this_fraction
            if gear.inside:
                speed = -(1 / this_fraction - 1)
                circles[-1].r -= this_radius
            else:
                speed = 1 / this_fraction + 1
                circles[-1].r += this_radius
            ncircles = len(circles)
            circles.append(Circle(r=this_radius, speed=speed))
            last_teeth = gear.teeth
            last_radius = this_radius
        circles[-1].r *= 1 + self.pen_extra
        return circles, cycles

    def points(self, dims, dt=0.01):
        circles, cycles = self._make_circles()
        stop = math.pi * 2 * cycles
        t = np.arange(start=0, stop=stop + dt/2, step=dt)
        x = y = 0
        scale = 0
        for circle in circles:
            cx, cy = circle(t)
            x += cx
            y += cy
            scale += circle.r
        scale *= 1.05
        x /= scale
        y /= scale
        yield from zip(x, y)

    def draw_more(self, ctx):
        return
        ctx.set_source_rgba(1, 0, 0, 0.8)
        ctx.set_line_width(1)
        ctx.arc(0, 0, 1.0 * 1080, 0, 2 * math.pi)
        ctx.stroke()
