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
    teeth = list(range(low, high + 1))
    teeth.remove(t)
    return teeth


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
        adjacent_step=0.5,
    )
    max_cycles = None

    def __init__(self, outer_teeth=144, pen_extra=0.0):
        super().__init__()
        self.outer_teeth = outer_teeth
        self.pen_extra = pen_extra
        self.gears = []
        self.circles = None

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
        curve.gears.append(
            Gear(name="ga", teeth=rnd.randint(10, 40), inside=rnd.choice([0, 1]))
        )
        curve.gears.append(
            Gear(name="gb", teeth=rnd.randint(5, 10), inside=rnd.choice([0, 1]))
        )
        curve.pen_extra = rnd.randint(0, 5) * 0.5
        return curve

    def _make_circles(self):
        if self.circles is not None:
            return self.circles
        self.circles = [Circle(r=1.0, speed=1)]
        last_teeth = self.outer_teeth
        last_radius = 1.0
        for gear in self.gears:
            this_fraction = gear.teeth / last_teeth
            this_radius = last_radius * this_fraction
            if gear.inside:
                speed = -(1 / this_fraction - 1)
                self.circles[-1].r -= this_radius
            else:
                speed = 1 / this_fraction + 1
                self.circles[-1].r += this_radius
            self.circles.append(Circle(r=this_radius, speed=speed))
            last_teeth = gear.teeth
            last_radius = this_radius
        self.circles[-1].r *= 1 + self.pen_extra
        return self.circles

    def _cycles(self):
        last_teeth = self.outer_teeth
        cycles = 1
        for gear in self.gears:
            cycles *= gear.teeth // math.gcd(last_teeth, gear.teeth)
            last_teeth = gear.teeth
        return cycles

    def _scale(self):
        scale = 0
        for circle in self._make_circles():
            scale += circle.r
        scale *= 1.05
        return scale

    def points(self, dims, scale, dt=0.01):
        circles = self._make_circles()
        print(circles)
        cycles = self.max_cycles or self._cycles()
        stop = math.pi * 2 * cycles
        t = np.arange(start=0, stop=stop + dt / 2, step=dt)
        x = y = 0
        for circle in circles:
            cx, cy = circle(t)
            x += cx
            y += cy
        scale /= self._scale()
        x *= scale
        y *= scale
        yield from zip(x, y)

    def draw_more(self, ctx, scale, param):
        scale /= self._scale()
        finalt = math.pi * 2 * (self.max_cycles or 0)

        ctx.set_source_rgba(1, 0, 0, param)
        ctx.set_line_width(1)
        x, y = 0, 0
        last_teeth = self.outer_teeth
        last_radius = 1.0
        draw_gear(ctx, scale, x, y, last_radius, self.outer_teeth, 0)
        circle_dx_dy = [circle(finalt) for circle in self.circles]

        for igear, gear in enumerate(self.gears):
            dx, dy = circle_dx_dy[igear]
            x += dx * scale
            y += dy * scale
            this_fraction = gear.teeth / last_teeth
            this_radius = last_radius * this_fraction
            last_teeth = gear.teeth
            last_radius = this_radius
            draw_gear(ctx, scale, x, y, last_radius, gear.teeth, math.atan2(*circle_dx_dy[igear+1]))
        ctx.move_to(x, y)
        dx, dy = self.circles[-1](finalt)
        x += dx * scale
        y += dy * scale
        ctx.line_to(x, y)
        ctx.stroke()
        ctx.arc(x, y, .02 * scale, 0, 2 * math.pi)
        ctx.fill()


def draw_gear(ctx, scale, cx, cy, radius, nteeth, dθ):
    radius *= scale
    ctx.arc(cx, cy, radius, 0, 2 * math.pi)
    ctx.stroke()
    for itooth in range(nteeth):
        tooth_in = tooth_out = .01 * scale
        if itooth == 0:
            tooth_in *= 5
        tooth_angle = dθ + itooth * (2 * math.pi / nteeth)
        dx = math.sin(tooth_angle)
        dy = math.cos(tooth_angle)
        ctx.move_to(cx + (radius - tooth_in) * dx, cy + (radius - tooth_in) * dy)
        ctx.line_to(cx + (radius + tooth_out) * dx, cy + (radius + tooth_out) * dy)
        ctx.stroke()


@dataclass
class ClockHand(Parameterized):
    radius: Parameter(
        name="radius",
        key="r",
        default=0.5,
        places=2,
        adjacent_step=0.05,
    )
    speed_num: Parameter(
        name="numerator",
        key="n",
        default=1,
        adjacent_step=1,
    )
    speed_denom: Parameter(
        name="denominator",
        key="d",
        default=3,
        adjacent_step=1,
    )


@dataclass
class MultiClock(Curve):
    ALGORITHM = 3

    def __init__(self):
        super().__init__()
        self.hands = []

    def param_things(self):
        yield self, None
        for hand in self.hands:
            yield hand, None

    @classmethod
    def from_params(cls, params, name=""):
        assert name == ""

        nhands = len(set(k[1] for k in params if k.startswith("h")))
        curve = super().from_params(params)
        for i in range(nhands):
            curve.hands.append(ClockHand.from_params(params, f"h{abc(i)}"))
        return curve

    @classmethod
    def make_random(cls, rnd):
        curve = cls()
        num, denom = random_rational(rnd)
        curve.hands.append(
            ClockHand(name="ha", radius=rnd.uniform(.5, 1.5), speed_num=num, speed_denom=denom)
        )
        curve.hands.append(
            ClockHand(name="hb", radius=rnd.uniform(.5, 1.5), speed_num=num, speed_denom=denom)
        )
        return curve

    def points(self, dims, scale, dt=0.01):
        circles = [Circle(r=1.0, speed=1)]
        for hand in self.hands:
            circles.append(Circle(r=hand.radius, speed=hand.speed_num/hand.speed_denom))

        print(circles)
        cycles = 30 # TODO: work this out for real.
        stop = math.pi * 2 * cycles
        t = np.arange(start=0, stop=stop + dt / 2, step=dt)
        x = y = 0
        for circle in circles:
            cx, cy = circle(t)
            x += cx
            y += cy
        x *= scale
        y *= scale
        yield from zip(x, y)


def random_rational(rnd):
    denom = rnd.randint(2, 12)
    num = rnd.randint(1, denom-1)
    #div = math.gcd(num, denom)
    #return num//div, denom//div
    return num, denom
