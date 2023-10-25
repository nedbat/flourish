from dataclasses import dataclass

from parameter import Parameter, Parameterized
from render import ElegantLine


@dataclass
class Curve(Parameterized):
    subcurves = {}

    algorithm: Parameter(
        name="algorithm",
        key="alg",
        default=1,
    )

    def __init__(self):
        super().__init__(name="")
        self.algorithm = self.ALGORITHM
        self.render = ElegantLine(linewidth=3, alpha=1)

    @classmethod
    def __init_subclass__(cls):
        cls.subcurves[cls.ALGORITHM] = cls

    @classmethod
    def any_from_params(cls, params):
        alg = int(params.pop("alg", 1))
        subcls = cls.subcurves[alg]
        return subcls.from_params(params)

    def complexity(self):
        return 0

    def points(self, dims, dt=0.01):
        pass

    def draw_more(self, ctx):
        pass


class ImpossibleCurve(Exception):
    ...
