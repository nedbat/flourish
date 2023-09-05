import math
from dataclasses import dataclass

import numpy as np

from curve import Curve
from parameter import Parameter, Parameterized
from util import abc


@dataclass
class Circle(Parameterized):
    r: Parameter(
        name="radius",
        key="r",
        default=1,
        adjacent_step=1,
    )
    phase: Parameter(
        name="phase",
        key="p",
        default=0,
        adjacent_step=10,
    )
    speed: Parameter(
        name="speed",
        key="s",
        default=1,
        adjacent_step=1,
    )

    def __call__(self, t):
        """Returns x,y"""
        tt = t * self.speed + self.phase
        return (self.r * np.sin(tt), self.r * np.cos(tt))


@dataclass
class Spirograph(Curve):
    def __init__(self, name=""):
        self.circles = []
        self.main_radius = 0

    def param_things(self):
        for circle in self.circles:
            yield circle, None

    @classmethod
    def make_random(cls, rnd):
        curve = cls()
        curve.circles.append(Circle.make_random("ca", rnd))
        curve.circles.append(Circle.make_random("cb", rnd))

    @classmethod
    def make_one(cls):
        curve = cls()
        curve.main_circle(0.4)
        curve.add_gear(gearr=0.18, penr=0.10, inside=True)
        return curve

    def main_circle(self, radius):
        self.main_radius = radius
        assert len(self.circles) == 0
        self.circles.append(Circle("ca", r=radius, speed=1, phase=0))

    def add_gear(self, gearr, penr, inside=False):
        lastr = self.circles[-1].r
        if inside:
            speed = -(lastr / gearr - 1)
            self.circles[-1].r -= gearr
        else:
            speed = (lastr / gearr + 1)
            self.circles[-1].r += gearr
        ncircles = len(self.circles)
        self.circles.append(Circle(f"c{abc(ncircles)}", r=penr, speed=speed, phase=0))

    def points(self, dims, dt=0.01):
        t = np.arange(start=0, stop=100, step=dt)
        x = y = 0
        for circle in self.circles:
            cx, cy = circle(t)
            x += cx
            y += cy
        yield from zip(x, y)

    def draw_more(self, ctx):
        ctx.set_source_rgba(1, 0, 0, .8)
        ctx.set_line_width(1)
        ctx.arc(0, 0, self.main_radius * 1080, 0, 2*math.pi)
        ctx.stroke()
