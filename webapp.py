import random
import urllib.parse
from io import BytesIO

import cairo
from flask import Flask, request, render_template

from harmonograph import Harmonograph, Ramp, FullWave

app = Flask(__name__)

@app.route("/")
def many():
    size = (192, 108)
    thumbs = []
    for _ in range(30):
        harm = make_random_harm(random)
        svg = draw_svg(harm=harm, gray=0, alpha=1, width=.1, size=size, start=800, stop=1000)
        thumbs.append((one_url(harm), svg))
    return render_template("many.html", thumbs=thumbs)

@app.route("/one")
def one():
    params = dict(request.args)

    npend = 3
    harm = Harmonograph()
    harm.add_dimension([FullWave.from_short_params(f"x{i}", params) for i in range(npend)])
    harm.add_dimension([FullWave.from_short_params(f"y{i}", params) for i in range(npend)])
    harm.set_ramp(Ramp.from_short_params("ramp", params))

    svg = draw_svg(harm=harm, gray=0, alpha=1, width=.3, size=(1920/2, 1080/2), start=800, stop=1000)
    return render_template("one.html", svg=svg)

def one_url(harm):
    q = urllib.parse.urlencode(list(harm.short_parameters()))
    return "/one?" + q

def make_random_harm(rnd, rampstop=500, npend=3):
    harm = Harmonograph()
    harm.add_dimension([FullWave.make_random(f"x{i}", rnd) for i in range(npend)])
    harm.add_dimension([FullWave.make_random(f"y{i}", rnd) for i in range(npend)])
    harm.set_ramp(Ramp("ramp", rampstop))
    return harm

def draw_svg(harm, start=0, stop=400, size=(500,500), gray=.25, width=.2, alpha=.5, npend=3):
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
