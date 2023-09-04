"""
A simple CLI for Flourish.
"""

import random

from constants import FULLX, FULLY
from harmonograph import Harmonograph
from render import ElegantLine, draw_png
from spirograph import Spirograph


def main():
    # curve = Harmonograph.make_random(random, npend=3, syms="R")
    curve = Spirograph.make_one()
    curve.render = ElegantLine(linewidth=1, alpha=1)
    png_bytes = draw_png(curve=curve, size=(FULLX, FULLY), with_metadata=True)
    with open("flourish.png", "wb") as pngf:
        pngf.write(png_bytes.read())


if __name__ == "__main__":
    main()
