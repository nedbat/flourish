"""
A simple CLI for Flourish.
"""

import itertools
import subprocess
import tempfile

import click

from constants import FULLX, FULLY
from curve import Curve
from render import draw_png
from util import slug_to_dict

from harmonograph import Harmonograph
from spirograph import Spirograph


@click.command()
@click.argument("slug")
def main(slug):
    slug = slug.rpartition("/")[-1]
    params = slug_to_dict(slug)
    curve = Curve.any_from_params(params)
    if 0:
        png_bytes = draw_png(curve=curve, size=(FULLX, FULLY), with_metadata=True)
        fname = "flourish.png"
        with open(fname, "wb") as pngf:
            pngf.write(png_bytes.read())
        print(f"Wrote {fname}")
    if 1:
        with tempfile.TemporaryDirectory() as tempdir:
            print(f"In {tempdir}")
            dθ = .5 / 360
            ncycles = curve._cycles()
            print(f"{ncycles = }")
            cycles = dθ
            framenums = itertools.count()
            for cycles in slow_then_faster(ncycles, dθ, 1, dθ * 40):
                if cycles >= ncycles:
                    cycles = ncycles    # So the last frame is aligned right.
                curve.max_cycles = cycles
                if cycles < 2:
                    with_more = 1
                elif cycles < 4:
                    with_more = 2 - (cycles / 2)
                else:
                    with_more = 0
                png_bytes = draw_png(
                    curve=curve,
                    size=(FULLX // 2, FULLY // 2),
                    with_metadata=False,
                    with_more=with_more,
                )
                output = f"{tempdir}/frame_{next(framenums):04d}.png"
                with open(output, "wb") as pngf:
                    pngf.write(png_bytes.read())

            print(f"wrote {output}")
            subprocess.run(
                "convert "
                + f"-delay 2 {tempdir}/frame_*.png "
                + f"-delay 1000 {output} "
                + "-strip -coalesce "
                #+ "-layers Optimize "
                + "flourish_movie.gif",
                shell=True,
            )


def slow_then_faster(limit, dmin, min_time, dmax):
    NRAMP = 3
    v = 0
    d = dmin
    dd = 0
    next_time = min_time
    nramp = 0
    while True:
        while v < next_time:
            v += d
            yield v
            if v >= limit:
                return
            d += dd
            if nramp > 0:
                nramp -= 1
                if nramp == 0:
                    dd = 0
        if d >= dmax:
            break
        next_time += 1
        dd = dmin/NRAMP
        nramp = NRAMP

    while True:
        v += dmax
        yield v
        if v >= limit:
            return


if __name__ == "__main__":
    main()
