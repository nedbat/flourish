import colorsys
from io import BytesIO

import cairo

class Render:
    extras = []
    DTS = [(400, .02), (1000, .01), (9999999, .002)]

    def __init__(self, linewidth=5, alpha=1, bg=1):
        self.linewidth = linewidth
        self.alpha = alpha
        self.bg = bg

    def prep_context(self, surface, size):
        self.surface = surface
        self.width, self.height = size
        ctx = cairo.Context(surface)
        ctx.rectangle(0, 0, self.width, self.height)
        ctx.set_source_rgba(self.bg, self.bg, self.bg, 1)
        ctx.fill()
        ctx.translate(self.width / 2, self.height / 2)
        self.set_line_width(ctx, 1)
        return ctx

    def draw(self, surface, size, harm):
        pass

    def dt(self):
        return lookup(self.width, self.DTS)

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

    def draw(self, surface, size, harm):
        npend = 3
        ctx = self.prep_context(surface, size)
        ctx.set_source_rgb(self.gray, self.gray, self.gray)
        maxx = self.width / (npend + 1)
        maxy = self.height / (npend + 1)
        for i, (x, y) in enumerate(harm.points(["x", "y"], dt=self.dt())):
            if i == 0:
                ctx.move_to(x * maxx, y * maxy)
            else:
                ctx.line_to(x * maxx, y * maxy)
        ctx.stroke()

class ColorLine(Render):
    extras = ["j", "k"]

    def __init__(self, lightness=.5, **kwargs):
        super().__init__(**kwargs)
        self.lightness = lightness

    def draw(self, surface, size, harm):
        npend = 3
        ctx = self.prep_context(surface, size)
        maxx = self.width / (npend + 1)
        maxy = self.height / (npend + 1)
        for i, (x, y, hue, width_tweak) in enumerate(harm.points(["x", "y", "j", "k"], dt=self.dt())):
            if i > 0:
                r, g, b = colorsys.hls_to_rgb(hue, self.lightness, 1)
                ctx.set_source_rgba(r, g, b, self.alpha)
                ctx.move_to(x0 * maxx, y0 * maxy)
                ctx.line_to(x * maxx, y * maxy)
                self.set_line_width(ctx, width_tweak + 1.5)
                ctx.stroke()
            x0, y0 = x, y


def draw_svg(harm, size, render=None):
    width, height = size
    if render is None:
        render = harm.render
    svgio = BytesIO()
    with cairo.SVGSurface(svgio, width, height) as surface:
        surface.set_document_unit(cairo.SVGUnit.PX)
        render.draw(surface, size, harm)
    return svgio.getvalue().decode("ascii")

def draw_png(harm, size, render=None):
    width, height = size
    if render is None:
        render = harm.render
    svgio = BytesIO()
    with cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height) as surface:
        render.draw(surface, size, harm)
        pngio = BytesIO()
        surface.write_to_png(pngio)
    pngio.seek(0)
    return pngio
