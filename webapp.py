import random
import urllib.parse
from dataclasses import dataclass
from io import BytesIO
from pprint import pformat

import cairo
from flask import Flask, request, render_template

from harmonograph import Harmonograph, Ramp, FullWave

app = Flask(__name__)

@dataclass
class Thumb:
    url: str
    svg: str


@app.route("/")
def many():
    size = (192, 108)
    thumbs = []
    for _ in range(30):
        harm = make_random_harm(random)
        thumbs.append(make_harm_thumb(harm, size=size))
    return render_template("many.html", thumbs=thumbs)

def make_harm_thumb(harm, size):
    return Thumb(
        url=one_url(harm),
        svg=draw_svg(harm=harm, width=.1, size=size, start=800, stop=1000),
    )

@app.route("/one")
def one():
    params = dict(request.args)
    harm = make_harm_from_short_params(params, npend=3)
    svg = draw_svg(harm=harm, width=.3, size=(1920/2, 1080/2), start=800, stop=1000)
    params = list(harm.parameters())
    return render_template("one.html", svg=svg, params=params, debug=pformat(params))

def one_url(harm):
    q = urllib.parse.urlencode(list(harm.short_parameters()))
    return "/one?" + q

def make_harm_from_short_params(params, npend):
    harm = Harmonograph()
    harm.add_dimension([FullWave.from_short_params(f"x{i}", params) for i in range(npend)])
    harm.add_dimension([FullWave.from_short_params(f"y{i}", params) for i in range(npend)])
    harm.set_ramp(Ramp.from_short_params("ramp", params))
    return harm

def make_random_harm(rnd, rampstop=500, npend=3):
    harm = Harmonograph()
    harm.add_dimension([FullWave.make_random(f"x{i}", rnd) for i in range(npend)])
    harm.add_dimension([FullWave.make_random(f"y{i}", rnd) for i in range(npend)])
    harm.set_ramp(Ramp("ramp", rampstop))
    return harm

def draw_svg(harm, start=0, stop=400, size=(500,500), gray=0, width=.2, alpha=1, npend=3):
    WIDTH, HEIGHT = size
    maxx = WIDTH / (npend + 1)
    maxy = HEIGHT / (npend + 1)

    svgio = BytesIO()
    with cairo.SVGSurface(svgio, WIDTH, HEIGHT) as surface:
        surface.set_document_unit(cairo.SVGUnit.PX)
        ctx = cairo.Context(surface)
        ctx.translate(WIDTH / 2, HEIGHT / 2)
        ctx.set_line_width(width)
        ctx.set_source_rgba(gray, gray, gray, alpha)
        for i, (x, y) in enumerate(harm.points(start=start, stop=stop, dt=.01)):
            if i == 0:
                ctx.move_to(x * maxx, y * maxy)
            else:
                ctx.line_to(x * maxx, y * maxy)
        ctx.stroke()

    return svgio.getvalue().decode("ascii")
