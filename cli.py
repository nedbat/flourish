"""
A simple CLI for Flourish.
"""

import random

from constants import FULLX, FULLY
from harmonograph import Harmonograph
from render import draw_png


def main():
    harm = Harmonograph.make_random(random, npend=3, syms="R")
    png_bytes = draw_png(harm=harm, size=(FULLX, FULLY), with_metadata=True)
    with open("flourish.png", "wb") as pngf:
        pngf.write(png_bytes.read())


if __name__ == "__main__":
    main()
