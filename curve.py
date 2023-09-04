from dataclasses import dataclass

from parameter import Parameterized


@dataclass
class Curve(Parameterized):
    def points(self, dims, dt=0.01):
        pass

    def draw_more(self, ctx):
        pass
