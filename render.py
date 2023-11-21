import colorsys
import json
from io import BytesIO

import cairo
from PIL import Image, PngImagePlugin

from constants import PNG_STATE_KEY


class Render:
    extras = []
    DTS = [(400, 0.02), (1000, 0.01), (9999999, 0.001)]

    def __init__(self, linewidth=5, alpha=1, bg=1):
        self.linewidth = linewidth
        self.alpha = alpha
        self.bg = bg

    def draw(self, surface, size, curve, with_more=False):
        self.surface = surface
        self.width, self.height = size
        self.dt = lookup(self.width, self.DTS)
        ctx = cairo.Context(surface)
        ctx.rectangle(0, 0, self.width, self.height)
        ctx.set_source_rgba(self.bg, self.bg, self.bg, 1)
        ctx.fill()
        ctx.translate(self.width / 2, self.height / 2)
        ctx.scale(1, -1)
        self.set_line_width(ctx, 1)

        maxsize = min(self.width, self.height) / 2
        self.draw_curve(ctx, curve, scale=maxsize)
        if with_more:
            curve.draw_more(ctx, scale=maxsize, param=with_more)

    def set_line_width(self, ctx, width_tweak):
        ctx.set_line_width(self.width * self.linewidth * width_tweak / 10000)


def lookup(x, choices):
    """
    Find the value in a lookup table where x < v.
    """
    for limit, choice in choices:
        if x < limit:
            return choice


class ElegantLine(Render):
    def __init__(self, gray=0, **kwargs):
        super().__init__(**kwargs)
        self.gray = gray
        # Cairo won't alpha a line over itself, so we can't use an alpha value
        # for this renderer, which draws the whole image as one line.
        assert self.alpha == 1

    def draw_curve(self, ctx, curve, scale):
        if curve.complexity() < 25_000:
            ctx.set_source_rgb(self.gray, self.gray, self.gray)
            for i, (x, y) in enumerate(curve.points(["x", "y"], scale=scale, dt=self.dt)):
                if i == 0:
                    ctx.move_to(x, y)
                else:
                    ctx.line_to(x, y)
            ctx.stroke()
        else:
            ctx.set_source_rgb(0.75, 0.75, 0.75)
            w = scale * 0.25
            ctx.move_to(-w, -w)
            ctx.line_to(-w, w)
            ctx.line_to(w, w)
            ctx.line_to(w, -w)
            ctx.close_path()
            ctx.fill()



class ColorLine(Render):
    extras = ["j", "k"]

    def __init__(self, lightness=0.5, **kwargs):
        super().__init__(**kwargs)
        self.lightness = lightness

    def draw_curve(self, ctx, curve, scale):
        x0 = y0 = 0
        for i, (x, y, hue, width_tweak) in enumerate(
            curve.points(["x", "y", "j", "k"], scale=scale, dt=self.dt)
        ):
            if i > 0:
                r, g, b = colorsys.hls_to_rgb(hue, self.lightness, 1)
                ctx.set_source_rgba(r, g, b, self.alpha)
                ctx.move_to(x0, y0)
                ctx.line_to(x, y)
                self.set_line_width(ctx, width_tweak/100 + 1.5)
                ctx.stroke()
            x0, y0 = x, y


def draw_svg(curve, size, render=None):
    width, height = size
    if render is None:
        render = curve.render
    svgio = BytesIO()
    with cairo.SVGSurface(svgio, width, height) as surface:
        surface.set_document_unit(cairo.SVGUnit.PX)
        render.draw(surface, size, curve)
    return svgio.getvalue().decode("ascii")


def draw_png(curve, size, render=None, with_metadata=False, with_more=0):
    width, height = size
    if render is None:
        render = curve.render
    with cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height) as surface:
        render.draw(surface, size, curve, with_more=with_more)
        pngio = BytesIO()
        surface.write_to_png(pngio)
    pngio.seek(0)

    if with_metadata:
        im = Image.open(pngio)
        info = PngImagePlugin.PngInfo()
        info.add_text("Software", "https://flourish.nedbat.com")
        info.add_text(PNG_STATE_KEY, json.dumps(curve.short_parameters()))
        pngio = BytesIO()
        im.save(pngio, "PNG", pnginfo=info)
        pngio.seek(0)

    return pngio
