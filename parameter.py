import contextlib
import dataclasses
from dataclasses import dataclass

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


