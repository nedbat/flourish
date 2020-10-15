import functools
import itertools
import json
import os
import random
import re
import urllib.parse
from dataclasses import dataclass
from io import BytesIO

from dataclasses_json import dataclass_json
from flask import (
    Flask, request,
    render_template, render_template_string,
    make_response, redirect, send_file,
)
from flask_wtf import FlaskForm
from PIL import Image, PngImagePlugin
from wtforms import BooleanField, IntegerField, StringField
from wtforms.validators import DataRequired

from harmonograph import Harmonograph
from render import draw_png, draw_svg, ColorLine, ElegantLine

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]

TheRender = functools.partial(ColorLine, linewidth=10, alpha=.5)
TheRender = functools.partial(ElegantLine, linewidth=3, alpha=1)

def dict_to_slug(d):
    return "".join(itertools.chain.from_iterable(d.items()))

def slug_to_dict(s):
    return dict(re.findall(r"([a-z]+)(-?\d+)", s))

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

@dataclass_json
@dataclass
class ManySettings:
    npend: int = 3
    style: str = "foob"
    xy_symmetry: bool = True
    x_symmetry: bool = True
    y_symmetry: bool = True
    no_symmetry: bool = True

MANY_SETTINGS_COOKIE = "manysettings"

class ManySettingsForm(FlaskForm):
    npend = IntegerField("Number of pendulums", validators=[DataRequired()])
    style = StringField("Style")
    xy_symmetry = BooleanField("XY Symmetry")
    x_symmetry = BooleanField("X Symmetry")
    y_symmetry = BooleanField("Y Symmetry")
    no_symmetry = BooleanField("No Symmetry")

@app.route("/", methods=["GET", "POST"])
def many():
    cookie_settings = request.cookies.get(MANY_SETTINGS_COOKIE)
    if cookie_settings is not None:
        settings = ManySettings.from_json(cookie_settings)
    else:
        settings = ManySettings()
    size = (192, 108)
    thumbs = []
    while len(thumbs) < 30:
        harm = Harmonograph.make_random(random, npend=settings.npend)
        keep = False
        if harm.is_xy_symmetric():
            keep = settings.xy_symmetry
        elif harm.is_x_symmetric():
            keep = settings.x_symmetry
        elif harm.is_y_symmetric():
            keep = settings.y_symmetry
        else:
            keep = settings.no_symmetry
        if keep:
            thumbs.append(Thumb(harm, size=size))
    form = ManySettingsForm(obj=settings)
    return render_template("many.html", thumbs=thumbs, form=form)

@app.route("/manysettings", methods=["POST"])
def manysettings():
    form = ManySettingsForm()
    settings = ManySettings()
    form.populate_obj(settings)
    resp = make_response(redirect("/"))
    resp.set_cookie(MANY_SETTINGS_COOKIE, settings.to_json())
    return resp

@app.route("/one/<path:slug>")
def one(slug):
    params = slug_to_dict(slug)
    harm = Harmonograph.make_from_short_params(params)
    render = TheRender()
    svg = draw_svg(render, harm=harm, size=(1920//2, 1080//2))
    params = list(harm.parameters())
    shorts = harm.short_parameters()
    param_display = []
    for paramdef, thing, extra_name, val in params:
        if extra_name is not None and extra_name not in render.extras:
            continue
        name = thing.name + " " + paramdef.type.name
        adj_thumbs = []
        for adj in paramdef.type.adjacent(val):
            adj_params = dict(shorts)
            adj_key = thing.name + paramdef.type.key
            # Experimenting with slug/delta urls...
            one_param = {adj_key: str(paramdef.type.to_short(adj))}
            adj_params.update(one_param)
            adj_harm = Harmonograph.make_from_short_params(adj_params)
            adj_repr = paramdef.type.repr(adj)
            adj_thumbs.append((adj_repr, dict_to_slug(one_param), Thumb(adj_harm, size=(192, 108))))
        param_display.append((name, adj_thumbs))
    download_url = one_url("/download", harm, sx=1920, sy=1080)
    return render_template(
        "one.html",
        svg=svg,
        params=params,
        param_display=param_display,
        download_url=download_url,
    )

@app.route("/png/<slug>")
def png(slug):
    params = slug_to_dict(slug)
    harm = Harmonograph.make_from_short_params(params)
    sx, sy = int(params.get("sx", 1920)), int(params.get("sy", 1080))
    png_bytes = draw_png(TheRender(), harm=harm, size=(sx, sy))
    return send_file(png_bytes, mimetype="image/png")

STATE_KEY = "Flourish State"

@app.route("/download/<slug>")
def download(slug):
    params = slug_to_dict(slug)
    harm = Harmonograph.make_from_short_params(params)
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
    qargs.update({k:str(v) for k, v in kwargs.items()})
    slug = dict_to_slug(qargs)
    return f"{route}/{slug}"
