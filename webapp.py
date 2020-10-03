import functools
import json
import random
import urllib.parse
from dataclasses import dataclass
from io import BytesIO

from flask import (
    Flask, request,
    render_template, render_template_string, send_file, redirect,
)
from PIL import Image, PngImagePlugin

from harmonograph import Harmonograph, Ramp, FullWave, TimeSpan
from render import draw_png, draw_svg, ColorLine, ElegantLine

app = Flask(__name__)

TheRender = functools.partial(ColorLine, linewidth=10, alpha=.5)
TheRender = functools.partial(ElegantLine, linewidth=3, alpha=1)

NPEND = 3

@dataclass
class Thumb:
    harm: Harmonograph
    size: object

    def as_html(self, title=None):
        url = one_url("/one", self.harm)
        sx = self.size[0]
        sy = self.size[1]
        pngurl = one_url("/png", self.harm, sx=sx*2, sy=sy*2)
        return render_template_string(
            '''
            <span>
                <a href="{{url}}" {% if title %}title="{{ title }}"{% endif %}>
                    <div class="thumb">
                        <img src={{pngurl}} width="{{sx}}" height="{{sy}}" />
                    </div>
                </a>
            </span>
            ''',
            url=url,
            pngurl=pngurl,
            sx=sx,
            sy=sy,
            title=title,
        )

@app.route("/")
def many():
    size = (192, 108)
    thumbs = []
    for _ in range(30):
        harm = make_random_harm(random, npend=NPEND)
        thumbs.append(Thumb(harm, size=size))
    return render_template("many.html", thumbs=thumbs)

@app.route("/one")
def one():
    params = dict(request.args)
    harm = make_harm_from_short_params(params, npend=NPEND)
    svg = draw_svg(TheRender(), harm=harm, size=(1920//2, 1080//2))
    params = list(harm.parameters())
    shorts = harm.short_parameters()
    param_display = []
    for paramdef, thing, extra_name, val in params:
        if extra_name is not None and extra_name not in TheRender().extras:
            continue
        name = thing.name + " " + paramdef.type.name
        adj_thumbs = []
        for adj in paramdef.type.adjacent(val):
            adj_params = dict(shorts)
            adj_key = thing.name + paramdef.type.key
            adj_params[adj_key] = paramdef.type.to_short(adj)
            adj_harm = make_harm_from_short_params(adj_params, npend=NPEND)
            adj_repr = paramdef.type.repr(adj)
            adj_thumbs.append((adj_repr, Thumb(adj_harm, size=(192, 108))))
        param_display.append((name, adj_thumbs))
    download_url = one_url("/download", harm, sx=1920, sy=1080)
    return render_template(
        "one.html",
        svg=svg,
        params=params,
        param_display=param_display,
        download_url=download_url,
    )

@app.route("/png")
def png():
    params = dict(request.args)
    harm = make_harm_from_short_params(params, npend=NPEND)
    sx, sy = int(params.get("sx", 1920)), int(params.get("sy", 1080))
    png_bytes = draw_png(TheRender(), harm=harm, size=(sx, sy))
    return send_file(png_bytes, mimetype="image/png")

STATE_KEY = "Flourish State"

@app.route("/download")
def download():
    params = dict(request.args)
    harm = make_harm_from_short_params(params, npend=NPEND)
    sx, sy = int(params.get("sx", 1920)), int(params.get("sy", 1080))
    png_bytes = draw_png(TheRender(), harm=harm, size=(sx, sy))
    im = Image.open(png_bytes)
    info = PngImagePlugin.PngInfo()
    info.add_text("Software", "https://nedbat-flourish.herokuapp.com")
    info.add_text(STATE_KEY, json.dumps(params))
    png_bytes = BytesIO()
    im.save(png_bytes, "PNG", pnginfo=info)
    png_bytes.seek(0)
    return send_file(png_bytes, as_attachment=True, attachment_filename="flourish.png", mimetype="image/png")

@app.route("/upload")
def upload():
    return render_template("upload.html")

@app.route("/upload", methods=["POST"])
def upload_file():
    uploaded_file = request.files["file"]
    if uploaded_file.filename.endswith(".png"):
        try:
            pngio = BytesIO()
            uploaded_file.save(pngio)
            pngio.seek(0)
            im = Image.open(pngio)
            params = im.info.get(STATE_KEY)
            if params:
                q = urllib.parse.urlencode(json.loads(params))
                return redirect(f"/one?{q}")
        except Exception:
            pass
        error = f"Couldn't find Flourish info in {uploaded_file.filename}"
    else:
        error = "Only .png files downloaded from Flourish will work"
    return render_template("upload.html", error=error)

def one_url(route, harm, **kwargs):
    qargs = harm.short_parameters()
    qargs.update(kwargs)
    q = urllib.parse.urlencode(qargs)
    return f"{route}?{q}"

def make_harm_from_short_params(params, npend):
    harm = Harmonograph()
    harm.add_dimension("x", [FullWave.from_short_params(f"x{i}", params) for i in range(npend)])
    harm.add_dimension("y", [FullWave.from_short_params(f"y{i}", params) for i in range(npend)])
    harm.add_dimension("j", [FullWave.from_short_params(f"j{i}", params) for i in range(1)], extra=True)
    harm.set_ramp(Ramp.from_short_params("ramp", params))
    harm.set_time_span(TimeSpan.from_short_params("ts", params))
    return harm

def make_random_harm(rnd, rampstop=500, npend=3):
    harm = Harmonograph()
    harm.add_dimension("x", [FullWave.make_random(f"x{i}", rnd) for i in range(npend)])
    harm.add_dimension("y", [FullWave.make_random(f"y{i}", rnd) for i in range(npend)])
    harm.add_dimension("j", [FullWave.make_random(f"j{i}", rnd) for i in range(1)], extra=True)
    harm.set_ramp(Ramp("ramp", rampstop))
    return harm
