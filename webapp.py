import hashlib
import json
import os
import random
import textwrap
from dataclasses import dataclass
from io import BytesIO

from dataclasses_json import dataclass_json
from dotenv import load_dotenv
from flask import (
    Flask,
    request,
    render_template,
    render_template_string,
    make_response,
    redirect,
    send_file,
)
from flask_wtf import FlaskForm
from PIL import Image
from wtforms import BooleanField, IntegerField
from wtforms.widgets import NumberInput
from wtforms.validators import DataRequired

from harmonograph import Harmonograph
from render import STATE_KEY, draw_png, draw_svg
from util import dict_to_slug, slug_to_dict

load_dotenv()
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")


@dataclass
class Thumb:
    harm: Harmonograph
    size: object

    def as_html(self, title=None):
        url = one_url("/one", self.harm)
        sx = self.size[0]
        sy = self.size[1]
        pngurl = one_url("/png", self.harm, sx=sx * 2, sy=sy * 2)
        return render_template_string(
            """
            <span>
                <a href="{{url}}" {% if title %}title="{{ title }}"{% endif %}>
                    <div class="thumb">
                        <img src={{pngurl}} width="{{sx}}" height="{{sy}}" />
                    </div>
                </a>
            </span>
            """,
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
    xy_symmetry: bool = True
    x_symmetry: bool = True
    y_symmetry: bool = True
    no_symmetry: bool = True


MANY_SETTINGS_COOKIE = "manysettings"


class ManySettingsForm(FlaskForm):
    npend = IntegerField(
        "Number of pendulums",
        validators=[DataRequired()],
        widget=NumberInput(min=1, max=9),
    )
    xy_symmetry = BooleanField("XY")
    x_symmetry = BooleanField("X")
    y_symmetry = BooleanField("Y")
    no_symmetry = BooleanField("None")


@app.route("/", methods=["GET", "POST"])
def many():
    cookie_settings = request.cookies.get(MANY_SETTINGS_COOKIE)
    if cookie_settings is not None:
        settings = ManySettings.from_json(cookie_settings)
    else:
        settings = ManySettings()
    syms = ""
    if settings.xy_symmetry:
        syms += "R"
    if settings.x_symmetry:
        syms += "X"
    if settings.y_symmetry:
        syms += "Y"
    if settings.no_symmetry:
        syms += "N"

    size = (192, 108)
    thumbs = []
    if syms:
        while len(thumbs) < 30:
            harm = Harmonograph.make_random(random, npend=settings.npend, syms=syms)
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
    svg = draw_svg(harm=harm, size=(1920 // 2, 1080 // 2))
    params = list(harm.parameters())
    shorts = harm.short_parameters()
    param_display = []
    for paramdef, thing, extra_name, val in params:
        if extra_name is not None and extra_name not in harm.render.extras:
            continue
        name = thing.name + " " + paramdef.type.name
        adj_thumbs = []
        for adj in paramdef.type.adjacent(val):
            adj_params = dict(shorts)
            adj_key = thing.name + paramdef.type.key
            # Experimenting with slug/delta urls...
            one_param = {adj_key: paramdef.type.to_short(adj)}
            adj_params.update(one_param)
            adj_harm = Harmonograph.make_from_short_params(adj_params)
            adj_repr = paramdef.type.repr(adj)
            adj_thumbs.append(
                (adj_repr, dict_to_slug(one_param), Thumb(adj_harm, size=(192, 108)))
            )
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
    png_bytes = draw_png(harm=harm, size=(sx, sy))
    return send_file(png_bytes, mimetype="image/png")


@app.route("/download/<slug>")
def download(slug):
    params = slug_to_dict(slug)
    harm = Harmonograph.make_from_short_params(params)
    sx, sy = int(params.get("sx", 1920)), int(params.get("sy", 1080))
    png_bytes = draw_png(harm=harm, size=(sx, sy), with_metadata=True)
    hash = hashlib.md5(slug.encode("ascii")).hexdigest()[:10]
    filename = f"flourish_{hash}.png"
    return send_file(
        png_bytes, as_attachment=True, download_name=filename, mimetype="image/png"
    )


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
                slug = dict_to_slug(json.loads(params))
                return redirect(f"/one/{slug}")
        except Exception:
            pass
        error = f"Couldn't find Flourish info in {uploaded_file.filename}"
    else:
        error = "Only .png files downloaded from Flourish will work"
    return render_template("upload.html", error=error)


def one_url(route, harm, **kwargs):
    slug = dict_to_slug({**harm.short_parameters(), **kwargs})
    return f"{route}/{slug}"


@app.route("/robots.txt")
def robots_txt():
    return textwrap.dedent(
        """\
        User-agent: *
        Disallow: /
        """
    )
