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
    speed: float = 0.0



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
        cum_speed = 0
        for gear in self.gears:
            this_fraction = gear.teeth / last_teeth
            this_radius = last_radius * this_fraction
            if gear.inside:
                speed = cum_speed - (1 / this_fraction - 1)
                self.circles[-1].r -= this_radius
            else:
                speed = cum_speed + (1 / this_fraction + 1)
                self.circles[-1].r += this_radius
            self.circles.append(Circle(r=this_radius, speed=speed))
            last_teeth = gear.teeth
            last_radius = this_radius
            cum_speed += speed
        self.circles[-1].r *= 1 + self.pen_extra
        print(self.circles)
        return self.circles

    def _make_circles(self):
        if self.circles is not None:
            return self.circles

        # In/out
        io1 = -1 if self.gears[0].inside else 1
        io2 = -1 if self.gears[1].inside else 1

        # Gear radii
        gr0 = 1
        gr1 = gr0 * (self.gears[0].teeth / self.outer_teeth)
        gr2 = gr1 * (self.gears[1].teeth / self.gears[0].teeth)
        print(f"{gr0 = }, {gr1 = }, {gr2 = }")

        # Circle radii
        cr0 = gr0 + io1 * gr1
        cr1 = gr1 + io2 * gr2
        cr2 = gr2 * (1 + self.pen_extra)

        # Gear local speeds
        gs0 = 0
        gs1 = io1 * 1
        gs2 = io2 * 1   # FOR NOW, will be a param
        print(f"{gs0 = }, {gs1 = }, {gs2 = }")

        # Circle speeds
        cs0 = gs0 + gs1 / (1 + io1 * gr0 / gr1)
        cs1 = gs0 + gs1 + gs2 / (1 + io2 * gr1 / gr2)
        cs2 = gs0 + gs1 + gs2
        print(f"{cs0 = }, {cs1 = }, {cs2 = }")

        self.circles = [
            Circle(r=cr0, speed=cs0),
            Circle(r=cr1, speed=cs1),
            Circle(r=cr2, speed=cs2),
        ]
        self.gears[0].speed = gs0 + gs1
        self.gears[1].speed = gs0 + gs1 + gs2
        print(f"{self.gears[0].speed = }, {self.gears[1].speed = }")
        return self.circles

    def _cycles(self):
        if 0:
            rots = [1/c.speed for c in self._make_circles() if c.speed != 0]
            cycles = lcm_float(rots)
            print(f"{rots = }, {cycles = }")
            return cycles
        last_teeth = self.outer_teeth
        cycles = 1
        for gear in self.gears:
            cycles *= gear.teeth // math.gcd(last_teeth, gear.teeth)
            last_teeth = gear.teeth
        print(f"{self.outer_teeth = }, {self.gears = }, {cycles = }")
        print(f"{self._make_circles() = }")
        return cycles

    def _scale(self):
        scale = 0
        for circle in self._make_circles():
            scale += circle.r
        scale *= 1.05
        return scale

    def points(self, dims, scale, dt=0.01):
        circles = self._make_circles()
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
            draw_gear(ctx, scale, x, y, last_radius, gear.teeth, gear.speed * finalt)
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


def lcm_float(nums):
    precision = 2
    numints = [int(abs(round(n, precision)) * 10**precision) for n in nums]
    return math.lcm(*numints) / 10**precision
