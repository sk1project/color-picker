# -*- coding: utf-8 -*-
#
# 	Copyright (C) 2019 by Igor E. Novikov
#
# 	This program is free software: you can redistribute it and/or modify
# 	it under the terms of the GNU General Public License as published by
# 	the Free Software Foundation, either version 3 of the License, or
# 	(at your option) any later version.
#
# 	This program is distributed in the hope that it will be useful,
# 	but WITHOUT ANY WARRANTY; without even the implied warranty of
# 	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# 	GNU General Public License for more details.
#
# 	You should have received a copy of the GNU General Public License
# 	along with this program.  If not, see <https://www.gnu.org/licenses/>.

import colorsys
import math
import os

import cairo

from cp2 import config
from cp2.rend import CairoRenderer
from uc2.utils.mixutils import Decomposable

CAIRO_WHITE = (1.0, 1.0, 1.0)
CAIRO_BLACK = (0.0, 0.0, 0.0)
NO_TRAFO = cairo.Matrix(1.0, 0.0, 0.0, 1.0, 0.0, 0.0)


def in_bbox(bbox, point):
    return bbox[0] < point[0] < bbox[2] and bbox[1] < point[1] < bbox[3]


# Color processing functions
def color_to_hex(color):
    hexcolor = '#'
    for value in color:
        hexval = hex(round(value * 255))[2:]
        if len(hexval) < 2:
            hexval = '0' + hexval
        hexcolor += hexval
    return hexcolor.upper()


def rgb_to_hsv(color):
    h, s, v = colorsys.rgb_to_hsv(*color)
    return h * 360, s * 100, v * 100


def text_color(color):
    h, s, v = rgb_to_hsv(color)
    if v < 55:
        return CAIRO_WHITE
    if s > 80 and (h > 210 or h < 20):
        return CAIRO_WHITE
    return CAIRO_BLACK


def check_brightness(color):
    h, s, v = rgb_to_hsv(color)
    return s < 10 and v > 90


# Cairo functions
def draw_rounded_rect(ctx, rect, radius):
    pi = math.pi
    x, y, w, h = rect
    ctx.move_to(x, y)
    ctx.new_path()
    ctx.arc(x + w - radius, y + radius, radius, -pi / 2, 0)
    ctx.arc(x + w - radius, y + h - radius, radius, 0, pi / 2)
    ctx.arc(x + radius, y + h - radius, radius, pi / 2, pi)
    ctx.arc(x + radius, y + radius, radius, pi, 3 * pi / 2)
    ctx.close_path()


class CanvasObj(Decomposable):
    canvas = None
    bbox = (0, 0, 0, 0)
    cursor = 'arrow'
    active = True
    hover = False

    def __init__(self, canvas):
        self.canvas = canvas

    def paint(self, ctx):
        pass

    def is_over(self, point):
        return in_bbox(self.bbox, point)

    def on_move(self, point):
        if self.active:
            if self.is_over(point):
                self.canvas.set_cursor(self.cursor)
                if not self.hover:
                    self.hover = True
                    self.canvas.dc.refresh()
                return True
            else:
                if self.hover:
                    self.hover = False
                    self.canvas.dc.refresh()
        return False


class LogoObj(CanvasObj):
    logo = None
    cursor = 'hand'

    def __init__(self, canvas):
        CanvasObj.__init__(self, canvas)
        logo_file = os.path.join(
            config.resource_dir, 'icons', 'color-picker.png')
        self.logo = cairo.ImageSurface.create_from_png(logo_file)

    def paint(self, ctx):
        colors = self.canvas.mw.doc.model.colors
        border = config.canvas_border

        if not colors:
            logo_w, logo_h = self.logo.get_width(), self.logo.get_height()
            dx = self.canvas.width - logo_w - border
            dy = self.canvas.height - logo_h - border
            ctx.set_matrix(cairo.Matrix(1.0, 0.0, 0.0, 1.0, dx, dy))
            ctx.set_source_surface(self.logo)
            ctx.paint()
            ctx.set_matrix(NO_TRAFO)

            ctx.set_font_size(12)
            ctx.set_source_rgb(*config.canvas_fg)
            txt = 'https://' + self.canvas.app.appdata.app_domain
            ext = ctx.text_extents(txt)
            ctx.move_to(dx + logo_w / 2 - ext.width / 2, dy + logo_h + 10)
            ctx.show_text(txt)

            self.bbox = (dx + logo_w / 2 - ext.width / 2,
                         dy,
                         dx + logo_w / 2 + ext.width / 2,
                         dy + logo_h + 10 + ext.height)

        self.active = not colors


class ScrollObj(CanvasObj):
    def paint(self, ctx):
        w, h = self.canvas.width, self.canvas.height
        sw = config.scroll_hover if self.hover else config.scroll_normal
        self.bbox = (w - sw, 0, w, h)
        virtual_h = self.canvas.virtual_h

        if virtual_h > h:
            rect_h = h * h / virtual_h
            rect_w = sw
            y = self.canvas.dy + self.canvas.dy * h / virtual_h
            ctx.set_source_rgb(*config.scroll_fg)
            ctx.rectangle(w - rect_w, y, w, rect_h)
            ctx.fill()

        self.active = virtual_h > h


class AddButtonObj(CanvasObj):
    cursor = 'hand'

    def paint(self, ctx):
        cell_h = config.cell_height
        cell_w = config.cell_width
        border = config.canvas_border
        cell_num = len(self.canvas.mw.doc.model.colors)
        cell_max = self.canvas.cell_max
        y_count = cell_num // cell_max if cell_max else 0
        x_count = cell_num - cell_max * y_count

        x = border + x_count * cell_w
        y = border + y_count * cell_h
        ctx.set_source_rgb(*config.addbutton_fg)
        rect = (x + 10, y + 10, cell_w - 20, cell_h - 20)
        self.bbox = (rect[0], rect[1] - self.canvas.dy,
                     rect[0] + rect[2], rect[1] + rect[3] - self.canvas.dy)
        draw_rounded_rect(ctx, rect, 20)
        ctx.set_line_width(4.0)
        ctx.set_dash([15, 8])
        ctx.stroke()

        size = cell_h // 3
        ctx.set_line_width(8.0)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.set_dash([])
        ctx.move_to(x + cell_w / 2, y + cell_h / 2 - size / 2)
        ctx.line_to(x + cell_w / 2, y + cell_h / 2 + size / 2)
        ctx.stroke()
        ctx.move_to(x + cell_w / 2 - size / 2, y + cell_h / 2)
        ctx.line_to(x + cell_w / 2 + size / 2, y + cell_h / 2)
        ctx.stroke()


class ColorGrid(CanvasObj):
    def paint(self, ctx):
        cms = self.canvas.cms
        border = config.canvas_border
        cell_h = config.cell_height
        cell_w = config.cell_width
        cell_max = self.canvas.cell_max
        x_count = y_count = 0

        colors = self.canvas.mw.doc.model.colors
        for item in colors:
            color = cms.get_display_color(item)
            color_name = cms.get_color_name(item)
            x = border + x_count * cell_w
            y = border + y_count * cell_h
            ctx.set_source_rgb(*color)
            rect = (x + 2, y + 2, cell_w - 4, cell_h - 4)
            draw_rounded_rect(ctx, rect, 20)
            ctx.fill()

            if check_brightness(color):
                ctx.set_source_rgb(*config.cell_border_color)
                rect = (x + 3, y + 3, cell_w - 6, cell_h - 6)
                draw_rounded_rect(ctx, rect, 20)
                ctx.set_line_width(1.0)
                ctx.set_dash([])
                ctx.stroke()

            ctx.set_font_size(15)
            label = color_to_hex(color)
            ext = ctx.text_extents(label)
            ctx.move_to(x + cell_w / 2 - ext.width / 2,
                        y + cell_h / 2 + ext.height / 2)
            ctx.set_source_rgb(*text_color(color))
            ctx.show_text(label)

            ctx.set_font_size(10)
            ext = ctx.text_extents(color_name)
            ctx.move_to(x + cell_w / 2 - ext.width / 2,
                        y + cell_h / 1.5 + ext.height / 2)
            ctx.show_text(color_name)

            x_count += 1
            if x_count == cell_max:
                x_count = 0
                y_count += 1


class BackgroundObj(CanvasObj):
    def paint(self, ctx):
        self.bbox = (0, 0, self.canvas.width, self.canvas.height)
        ctx.set_source_rgb(*config.canvas_bg)
        ctx.paint()


class Canvas(Decomposable):
    app = None
    mw = None
    dc = None
    rend = None
    cms = None
    surface = None
    ctx = None

    dy = 0
    max_dy = 0
    width = 0
    height = 0
    virtual_h = 0
    cell_max = 5
    z_order = None

    def __init__(self, mw):
        self.mw = mw
        self.app = mw.app
        self.dc = mw.dc
        self.cms = self.app.default_cms
        self.rend = CairoRenderer(self)

        self.colors = ColorGrid(self)
        self.scroll = ScrollObj(self)

        self.z_order = [
            LogoObj(self),
            self.scroll,
            AddButtonObj(self),
            self.colors,
            BackgroundObj(self),
        ]

    def set_cursor(self, cursor_name):
        self.dc.set_cursor(cursor_name)

    def on_scroll(self, event):
        self.dy += event.get_scroll() * config.mouse_scroll_sensitivity
        if self.dy < 0 or self.virtual_h <= self.height:
            self.dy = 0
        elif self.virtual_h > self.height and \
                self.dy > self.virtual_h - self.height:
            self.dy = self.virtual_h - self.height
        self.dc.refresh()

    def on_move(self, event):
        for obj in self.z_order:
            if obj.on_move(event.get_point()):
                break

    def on_leave(self, _event):
        if self.scroll.hover:
            self.scroll.hover = False
            self.dc.refresh()

    def paint(self, widget_ctx):
        w, h = self.dc.get_size()
        border = config.canvas_border
        cell_h = config.cell_height
        cell_num = len(self.mw.doc.model.colors)
        self.cell_max = (w - 2 * config.canvas_border) // config.cell_width
        self.virtual_h = \
            2 * border + math.ceil(cell_num / self.cell_max) * cell_h
        max_dy = round(self.virtual_h - h)
        self.max_dy = max_dy if max_dy > 0 else 0
        self.dy = min(self.dy, self.max_dy)

        if self.surface is None or self.width != w or self.height != h:
            self.surface = cairo.ImageSurface(cairo.FORMAT_RGB24, w, h)
            self.width, self.height = w, h
        self.ctx = cairo.Context(self.surface)

        self.ctx.set_matrix(cairo.Matrix(1.0, 0.0, 0.0, 1.0, 0.0, -self.dy))

        for obj in reversed(self.z_order):
            obj.paint(self.ctx)

        widget_ctx.set_source_surface(self.surface)
        widget_ctx.paint()
