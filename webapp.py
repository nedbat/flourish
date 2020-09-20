from flask import Flask, request, redirect, session

from harmonograph import Harmonograph, Wave, Decay, Ramp, make_random, RandWave
from harmonograph import FullWave
import colorsys
import random
import urllib.parse
from io import BytesIO

import cairo

app = Flask(__name__)

@app.route("/")
def main():
    seed = request.args.get("seed")
    seed, rnd = make_random(seed)
    harm = make_random_harm(rnd, npend=3)
    html = "<!DOCTYPE html><head><title>Charismatic Headroom</title><body>"
    html += draw_svg(harm=harm, gray=0, alpha=1, width=.3, size=(1920/2, 1080/2), start=800, stop=1000)
    html += f"<p>seed = <a href='/?seed={seed}'>{seed}</a></p>"
    if 0:
        html += "<ul>"
        for name, value in harm.parameters():
            html += f"<li>{name}: {value}</li>"
        html += "</ul>"
        html += f"<p>{str(list(harm.short_parameters()))}</p>"
    q = urllib.parse.urlencode(list(harm.short_parameters()))
    html += f"<p><a href='/one?{q}'>specific</a></p>"
    return html

@app.route("/one")
def one():
    params = dict(request.args)
    
    npend = 3
    harm = Harmonograph()
    harm.add_dimension([FullWave.from_short_params(f"x{i}", params) for i in range(npend)])
    harm.add_dimension([FullWave.from_short_params(f"y{i}", params) for i in range(npend)])
    harm.set_ramp(Ramp.from_short_params("ramp", params))

    html = "<!DOCTYPE html><head><title>Charismatic Headroom</title><body>"
    html += draw_svg(harm=harm, gray=0, alpha=1, width=.3, size=(1920/2, 1080/2), start=800, stop=1000)
    return html

@app.route("/many")
def many():
    html = "<!DOCTYPE html><head><title>Charismatic Headroom</title>"
    html += "<style>"
    html += "body { max-width: 1000px; margin: 1em auto; } "
    html += "a { text-decoration: none; } "
    html += ".thumb svg {border: 1px solid #eee; } .thumb svg:hover { border: 1px solid #888; } "
    html += "</style>"
    html += "<body>"
    size = (192, 108)
    for _ in range(35):
        harm = make_random_harm(random)
        q = urllib.parse.urlencode(list(harm.short_parameters()))
        html += f"<span class='thumb'><a href='/one?{q}'>"
        html += draw_svg(harm=harm, gray=0, alpha=1, width=.1, size=size, start=800, stop=1000)
        html += "</a></span>"
    return html

def make_random_harm(rnd, rampstop=500, npend=3):
    harm = Harmonograph()
    harm.add_dimension([FullWave.make_random(f"x{i}", rnd) for i in range(npend)])
    harm.add_dimension([FullWave.make_random(f"y{i}", rnd) for i in range(npend)])
    harm.set_ramp(Ramp("ramp", rampstop))
    return harm

def draw_svg(harm, seed=None, start=0, stop=400, size=(500,500), gray=.25, width=.2, alpha=.5, npend=3):
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


if __name__ == "__main__":
    app.run(threaded=True, port=6123)
