"""Miscellaneous stuff."""

import itertools
import re


def dict_to_slug(d):
    """
    Turn a dict into a single string by concatenating the keys and stringed values.

    For use with slug_to_dict, so the values must be integers (ironically).
    """
    return "".join(itertools.chain.from_iterable((k, str(v)) for k, v in d.items()))


def slug_to_dict(s):
    """
    A slug becomes a dict.

    abc123def456x-76y99 becomes {"abc": "123", "def": "456", "x": "-76", "y": "99"}
    """
    return dict(re.findall(r"([a-z]+)(-?\d+)", s))
