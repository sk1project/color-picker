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

CELL_SIZE = 150
CELL_W = 100
CELL_H = 100
CELL_MAX = 5
BORDER = 20
CAIRO_BLACK = (0.0, 0.0, 0.0)
CAIRO_GRAY = (0.75, 0.75, 0.75)
CAIRO_LIGHT_GRAY = (0.9, 0.9, 0.9)
CAIRO_WHITE = (1.0, 1.0, 1.0)
SEL_BG = [0.9375, 0.46484375, 0.2734375]  # #F07746

COLORS = [((0.0, 0.0, 0.0), 'Black'),
          ((0.5, 0.5, 0.5), 'Gray 50%'),
          ((0.75, 0.75, 0.75), 'Gray 25%'),
          ((0.9, 0.9, 0.9), 'Gray 10%'),
          ((1.0, 1.0, 1.0), 'White'),
          ((0.0, 1.0, 0.0), 'Green'),
          ((0.0, 0.0, 1.0), 'Blue'),
          ((1.0, 0.0, 0.0), 'Red'),
          ((1.0, 1.0, 0.0), 'Yellow'),
          ((0.0, 1.0, 1.0), 'Cyan'),
          ((1.0, 0.0, 1.0), 'Magenta'), ]


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


class CairoRenderer:
    canvas = None
    dc = None
    surface = None
    ctx = None
    width = 0
    height = 0

    def __init__(self, canvas):
        self.canvas = canvas
        self.dc = canvas.dc
        self.cms = canvas.cms
        logo_file = os.path.join(
            config.resource_dir, 'icons', 'color-picker.png')
        self.logo = cairo.ImageSurface.create_from_png(logo_file)

    @staticmethod
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

    def paint(self, widget_ctx):
        w, h = self.dc.get_size()
        cell_max = (w - 2 * BORDER) // CELL_W

        if self.surface is None or self.width != w or self.height != h:
            self.surface = cairo.ImageSurface(cairo.FORMAT_RGB24, w, h)
            self.width, self.height = w, h
        self.ctx = cairo.Context(self.surface)
        self.ctx.set_source_rgb(*CAIRO_WHITE)
        self.ctx.paint()

        self.ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        x_count = y_count = 0
        colors = self.canvas.mw.doc.model.colors
        for item in colors:
            color = self.cms.get_display_color(item)
            color_name = self.cms.get_color_name(item)
            x = BORDER + x_count * CELL_W
            y = BORDER + y_count * CELL_H
            self.ctx.set_source_rgb(*color)
            rect = (x + 2, y + 2, CELL_W - 4, CELL_H - 4)
            self.draw_rounded_rect(self.ctx, rect, 20)
            self.ctx.fill()

            if check_brightness(color):
                self.ctx.set_source_rgb(*CAIRO_LIGHT_GRAY)
                rect = (x + 3, y + 3, CELL_W - 6, CELL_H - 6)
                self.draw_rounded_rect(self.ctx, rect, 20)
                self.ctx.set_line_width(1.0)
                self.ctx.set_dash([])
                self.ctx.stroke()

            self.ctx.set_font_size(15)
            label = color_to_hex(color)
            ext = self.ctx.text_extents(label)
            self.ctx.move_to(x + CELL_W / 2 - ext.width / 2,
                             y + CELL_H / 2 + ext.height / 2)
            self.ctx.set_source_rgb(*text_color(color))
            self.ctx.show_text(label)

            self.ctx.set_font_size(10)
            ext = self.ctx.text_extents(color_name)
            self.ctx.move_to(x + CELL_W / 2 - ext.width / 2,
                             y + CELL_H / 1.5 + ext.height / 2)
            self.ctx.show_text(color_name)

            x_count += 1
            if x_count == cell_max:
                x_count = 0
                y_count += 1

        # AddColor button
        x = BORDER + x_count * CELL_W
        y = BORDER + y_count * CELL_H
        self.ctx.set_source_rgb(*CAIRO_LIGHT_GRAY)
        rect = (x + 10, y + 10, CELL_W - 20, CELL_H - 20)
        self.draw_rounded_rect(self.ctx, rect, 20)
        self.ctx.set_line_width(4.0)
        self.ctx.set_dash([15, 8])
        self.ctx.stroke()

        size = CELL_H // 3
        self.ctx.set_line_width(8.0)
        self.ctx.set_dash([])
        self.ctx.move_to(x + CELL_W / 2, y + CELL_H / 2 - size / 2)
        self.ctx.line_to(x + CELL_W / 2, y + CELL_H / 2 + size / 2)
        self.ctx.stroke()
        self.ctx.move_to(x + CELL_W / 2 - size / 2, y + CELL_H / 2)
        self.ctx.line_to(x + CELL_W / 2 + size / 2, y + CELL_H / 2)
        self.ctx.stroke()

        # Scroll
        virtual_h = 2 * BORDER + math.ceil(len(colors) / cell_max) * CELL_H
        if virtual_h > h:
            rect_h = h * h / virtual_h
            rect_w = 5
            self.ctx.set_source_rgb(*SEL_BG)
            self.ctx.rectangle(w - rect_w, 0, w, rect_h)
            self.ctx.fill()

        # Logo
        if not colors:
            logo_w, logo_h = self.logo.get_width(), self.logo.get_height()
            dx, dy = w - logo_w - BORDER, h - logo_h - BORDER
            self.ctx.set_matrix(cairo.Matrix(1.0, 0.0, 0.0, 1.0, dx, dy))
            self.ctx.set_source_surface(self.logo)
            self.ctx.paint()
            self.ctx.set_matrix(cairo.Matrix(1.0, 0.0, 0.0, 1.0, 0.0, 0.0))

            self.ctx.set_font_size(12)
            self.ctx.set_source_rgb(*CAIRO_BLACK)
            txt = 'https://' + self.canvas.app.appdata.app_domain
            ext = self.ctx.text_extents(txt)
            self.ctx.move_to(dx + logo_w / 2 - ext.width / 2, dy + logo_h + 10)
            self.ctx.show_text(txt)

        widget_ctx.set_source_surface(self.surface)
        widget_ctx.paint()
