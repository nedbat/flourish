import colorsys
import random
import urllib.parse
from dataclasses import dataclass
from io import BytesIO
from pprint import pformat

import cairo
from flask import Flask, request, render_template, render_template_string

from harmonograph import Harmonograph, Ramp, FullWave

app = Flask(__name__)

@dataclass
class Thumb:
    harm: Harmonograph
    size: object

    def as_html(self):
        url = one_url(self.harm)
        svg = draw_svg(harm=self.harm, width=.1, size=self.size, start=800, stop=1000)
        return render_template_string(
            '''<span><a href="{{url}}"><div class="thumb">{{svg|safe}}</div></a></span>''',
            url=url,
            svg=svg
        )

@app.route("/")
def many():
    size = (192, 108)
    thumbs = []
    for _ in range(30):
        harm = make_random_harm(random)
        thumbs.append(Thumb(harm, size=size))
    return render_template("many.html", thumbs=thumbs)

def first_last(seq):
    l = list(seq)
    if l:
        return [seq[0], seq[-1]]
    else:
        return []

@app.route("/one")
def one():
    params = dict(request.args)
    harm = make_harm_from_short_params(params, npend=3)
    svg = draw_svg(harm=harm, width=.3, size=(1920/2, 1080/2), start=800, stop=1000)
    params = list(harm.parameters())
    shorts = harm.short_parameters()
    param_display = []
    for paramdef, thing, val in params:
        name = thing.name + " " + paramdef.type.name
        adj_thumbs = []
        for adj in paramdef.type.adjacent(val):
            adj_params = dict(shorts)
            adj_key = thing.name + paramdef.type.key
            adj_params[adj_key] = paramdef.type.to_short(adj)
            adj_harm = make_harm_from_short_params(adj_params, npend=3)
            adj_thumbs.append(Thumb(adj_harm, size=(192, 108)))
        param_display.append((name, adj_thumbs))
    return render_template("one.html", svg=svg, params=params, param_display=param_display)

@app.route("/color")
def color():
    params = dict(request.args)
    harm = make_harm_from_short_params(params, npend=3)
    svg = draw_color_svg(harm=harm, width=.3, size=(1920/2, 1080/2), start=800, stop=1000, gray=1, bg=0)
    return render_template("one.html", svg=svg)

def one_url(harm):
    q = urllib.parse.urlencode(harm.short_parameters())
    return "/one?" + q

def make_harm_from_short_params(params, npend):
    harm = Harmonograph()
    harm.add_dimension("x", [FullWave.from_short_params(f"x{i}", params) for i in range(npend)])
    harm.add_dimension("y", [FullWave.from_short_params(f"y{i}", params) for i in range(npend)])
    harm.add_dimension("z", [FullWave.from_short_params(f"z{i}", params) for i in range(npend)])
    harm.set_ramp(Ramp.from_short_params("ramp", params))
    return harm

def make_random_harm(rnd, rampstop=500, npend=3):
    harm = Harmonograph()
    harm.add_dimension("x", [FullWave.make_random(f"x{i}", rnd) for i in range(npend)])
    harm.add_dimension("y", [FullWave.make_random(f"y{i}", rnd) for i in range(npend)])
    harm.add_dimension("z", [FullWave.make_random(f"z{i}", rnd) for i in range(npend)])
    harm.set_ramp(Ramp("ramp", rampstop))
    return harm

def draw_svg(harm, start=0, stop=400, size=(500,500), gray=0, width=.2, alpha=1, bg=1, npend=3):
    WIDTH, HEIGHT = size
    maxx = WIDTH / (npend + 1)
    maxy = HEIGHT / (npend + 1)

    svgio = BytesIO()
    with cairo.SVGSurface(svgio, WIDTH, HEIGHT) as surface:
        surface.set_document_unit(cairo.SVGUnit.PX)
        ctx = cairo.Context(surface)
        ctx.rectangle(0, 0, WIDTH, HEIGHT)
        ctx.set_source_rgba(bg, bg, bg, 1)
        ctx.fill()

        ctx.translate(WIDTH / 2, HEIGHT / 2)
        ctx.set_line_width(width)
        ctx.set_source_rgba(gray, gray, gray, alpha)
        for i, (x, y) in enumerate(harm.points(["x", "y"], start=start, stop=stop, dt=.01)):
            if i == 0:
                ctx.move_to(x * maxx, y * maxy)
            else:
                ctx.line_to(x * maxx, y * maxy)
        ctx.stroke()

    return svgio.getvalue().decode("ascii")

def draw_color_svg(harm, start=0, stop=400, size=(500,500), gray=0, width=.2, alpha=1, bg=1, npend=3):
    WIDTH, HEIGHT = size
    maxx = WIDTH / (npend + 1)
    maxy = HEIGHT / (npend + 1)

    svgio = BytesIO()
    with cairo.SVGSurface(svgio, WIDTH, HEIGHT) as surface:
        surface.set_document_unit(cairo.SVGUnit.PX)
        ctx = cairo.Context(surface)
        ctx.rectangle(0, 0, WIDTH, HEIGHT)
        ctx.set_source_rgba(bg, bg, bg, 1)
        ctx.fill()

        ctx.translate(WIDTH / 2, HEIGHT / 2)
        ctx.set_line_width(width)
        x0 = y0 = None
        for i, (x, y, z) in enumerate(harm.points(["x", "y", "z"], start=start, stop=stop, dt=.01)):
            if i > 0:
                r, g, b = colorsys.hls_to_rgb(z, .5, 1)
                ctx.set_source_rgba(r, g, b, alpha)
                ctx.move_to(x0 * maxx, y0 * maxy)
                ctx.line_to(x * maxx, y * maxy)
                ctx.stroke()
            x0, y0 = x, y

    return svgio.getvalue().decode("ascii")
