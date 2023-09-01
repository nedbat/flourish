"""
Parameterized curves
"""

import contextlib
import contextvars
import dataclasses
from dataclasses import dataclass

class Parameter:
    """
    A parameter for a curve.

    All values must be int or float.
    """
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
        """
        Return a list of adjacent values for this parameter.
        """
        d = self.adjacent_step
        if d is None:
            return []
        else:
            return [v - 2 * d, v - d, v + d, v + 2 * d]

    def to_short(self, v):
        """
        Convert the value to a short representation, which must be a string of an int.
        """
        if isinstance(self.default, float):
            return str(int(v / self.scale * 10 ** self.places))
        else:
            return str(v)

    def from_short(self, s):
        """
        Convert from a short representation, once produced by `to_short`.
        """
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
    """
    A parameterized thing (probably a function).
    """
    # The name will be used to differentiate between multiple instances used
    # together, like an x wave and a y wave.
    name: str

    @classmethod
    def paramdefs(cls):
        """
        Get the fields that are Parameters.
        """
        for field in dataclasses.fields(cls):
            if isinstance(field.type, Parameter):
                yield field

    @classmethod
    def make_random(cls, name, rnd):
        """
        Use the Random object `rnd` to make an instance with randomized Parameters.
        """
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
        """
        Make an instance using the params dict for Parameter values.
        """
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
        """
        Make an instance using the params dict for Parameter short values.
        """
        kwargs = {}
        for field in cls.paramdefs():
            key = name + field.type.key
            if key in params:
                val = field.type.from_short(params[key])
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
        """
        Return a dict of short parameters for all of the Parameters.
        """
        shorts = {}
        for thing, _ in self.param_things():
            for field in thing.paramdefs():
                key = thing.name + field.type.key
                val = getattr(thing, field.name)
                if field.type.to_short:
                    val = field.type.to_short(val)
                shorts[key] = str(val)
        return shorts


## Pseudo-global parameters, like thread locals.

GlobalParameter = contextvars.ContextVar

@contextlib.contextmanager
def global_value(cvar, val):
    token = cvar.set(val)
    try:
        yield
    finally:
        cvar.reset(token)
