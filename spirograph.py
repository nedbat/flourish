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

    @classmethod
    def make_random(cls, rnd):
        curve = cls()
        curve.circles.append(Circle.make_random("ca", rnd))
        curve.circles.append(Circle.make_random("cb", rnd))

    @classmethod
    def make_one(cls):
        curve = cls()
        ratios = [1, 10, 2, 2]
        size = .3
        speed = 1
        for i, ratio in enumerate(ratios):
            size /= ratio
            speed *= (ratio + 1)
            curve.circles.append(Circle(f"c{abc(i)}", r=size, speed=speed, phase=0))
        return curve

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
        ctx.arc(0, 0, self.circles[0].r * 1080, 0, 2*math.pi)
        ctx.stroke()
