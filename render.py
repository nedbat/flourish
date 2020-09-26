import colorsys
from io import BytesIO

import cairo

class Render:
    def draw(self, surface, size, harm):
        pass

class ElegantLine(Render):
    def __init__(self, gray=0, linewidth=.2, alpha=1, bg=1):
        self.gray = gray
        self.linewidth = linewidth
        self.alpha = alpha
        self.bg = bg

    def draw(self, surface, size, harm):
        npend = 3
        width, height = size
        ctx = cairo.Context(surface)
        ctx.rectangle(0, 0, width, height)
        ctx.set_source_rgba(self.bg, self.bg, self.bg, 1)
        ctx.fill()

        ctx.translate(width / 2, height / 2)
        ctx.set_line_width(self.linewidth)
        ctx.set_source_rgba(self.gray, self.gray, self.gray, self.alpha)
        maxx = width / (npend + 1)
        maxy = height / (npend + 1)
        for i, (x, y) in enumerate(harm.points(["x", "y"], dt=.01)):
            if i == 0:
                ctx.move_to(x * maxx, y * maxy)
            else:
                ctx.line_to(x * maxx, y * maxy)
        ctx.stroke()

class ColorLine(Render):
    def __init__(self, linewidth=.2, alpha=1, bg=1):
        self.linewidth = linewidth
        self.alpha = alpha
        self.bg = bg

    def draw(self, surface, size, harm):
        npend = 3
        width, height = size
        ctx = cairo.Context(surface)
        ctx.rectangle(0, 0, width, height)
        ctx.set_source_rgba(self.bg, self.bg, self.bg, 1)
        ctx.fill()

        ctx.translate(width / 2, height / 2)
        ctx.set_line_width(self.linewidth)
        maxx = width / (npend + 1)
        maxy = height / (npend + 1)
        x0 = y0 = None
        for i, (x, y, z) in enumerate(harm.points(["x", "y", "z"], dt=.002)):
            if i > 0:
                r, g, b = colorsys.hls_to_rgb(z, .5, 1)
                ctx.set_source_rgba(r, g, b, self.alpha)
                ctx.move_to(x0 * maxx, y0 * maxy)
                ctx.line_to(x * maxx, y * maxy)
                ctx.stroke()
            x0, y0 = x, y


def draw_svg(render, harm, size):
    width, height = size
    svgio = BytesIO()
    with cairo.SVGSurface(svgio, width, height) as surface:
        surface.set_document_unit(cairo.SVGUnit.PX)
        render.draw(surface, size, harm)
    return svgio.getvalue().decode("ascii")

def draw_png(render, harm, size):
    width, height = size
    with cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height) as surface:
        render.draw(surface, size, harm)
        pngio = BytesIO()
        surface.write_to_png(pngio)
    pngio.seek(0)
    return pngio
