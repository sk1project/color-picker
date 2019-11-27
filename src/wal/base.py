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
import cairo
import gi
import math
import os

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, Gio


class Application(Gtk.Application):
    mw = None

    def __init__(self):
        super().__init__()

    @staticmethod
    def set_app_name(name):
        GLib.set_application_name(name)

    def drop_win(self, win):
        pass

    def run(self):
        Gtk.main()

    def exit(self, *_args):
        Gtk.main_quit()


class PaletteWindow(Gtk.Window):
    app = None
    canvas = None
    hdr = None

    def __init__(self, app):
        self.app = app
        super().__init__()
        self.canvas = CanvasDC()
        self.add(self.canvas)
        self.connect('destroy', self.close_action)
        self.hdr = Gtk.HeaderBar()
        self.hdr.set_show_close_button(True)
        self.hdr.props.title = '---'
        self.hdr.props.subtitle = 'Basic palette'
        self.set_titlebar(self.hdr)

        icon = os.path.join(
            os.path.split(__file__)[0], "..", "cp2", "share",
            "icons", "color-picker.png")
        self.set_default_icon(Gtk.Image.new_from_file(icon).get_pixbuf())

        self.pickbtn = Gtk.Button()
        self.pickbtn.set_tooltip_text('Pick color')
        icon = Gio.ThemedIcon(name="color-select-symbolic")
        self.pickbtn.add(Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON))
        self.hdr.pack_start(self.pickbtn)

        self.zoombtn = Gtk.Button()
        self.zoombtn.set_tooltip_text('Zoomed pick')
        icon = Gio.ThemedIcon(name="find-location-symbolic")
        self.zoombtn.add(Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON))
        self.hdr.pack_start(self.zoombtn)

        self.menubtn = Gtk.Button()
        self.menubtn.set_tooltip_text('Open menu')
        icon = Gio.ThemedIcon(name="open-menu-symbolic")
        self.menubtn.add(Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON))
        self.hdr.pack_end(self.menubtn)

    def close_action(self, *_args):
        self.destroy()
        self.app.drop_win(self)

    def set_size(self, w, h):
        self.resize(w, h)

    def set_min_size(self, w, h):
        self.set_size_request(w, h)

    def set_title(self, title):
        self.hdr.props.title = title

    def set_subtitle(self, subtitle):
        self.hdr.props.subtitle = subtitle

    def center(self):
        self.set_position(Gtk.WindowPosition.CENTER)

    def show(self):
        self.show_all()


CELL_SIZE = 150
CELL_W = 100
CELL_H = 100
CELL_MAX = 5
BORDER = 20
CAIRO_BLACK = (0.0, 0.0, 0.0)
CAIRO_GRAY = (0.75, 0.75, 0.75)
CAIRO_LIGHT_GRAY = (0.9, 0.9, 0.9)
CAIRO_WHITE = [1.0, 1.0, 1.0]
SEL_BG = [0.9375, 0.46484375, 0.2734375]  # #F07746


class CanvasDC(Gtk.DrawingArea):
    surface = None
    ctx = None
    width = 0
    height = 0

    def __init__(self):
        super().__init__()
        self.connect('draw', self.paint)

    def get_size(self):
        rect = self.get_allocation()
        return rect.width, rect.height

    def color_to_hex(self, color):
        hexcolor = '#'
        for value in color:
            hexval = hex(round(value * 255))[2:]
            if len(hexval) < 2:
                hexval = '0' + hexval
            hexcolor += hexval
        return hexcolor.upper()

    def rgb_to_hsv(self, color):
        h, s, v = colorsys.rgb_to_hsv(*color)
        return h * 360, s * 100, v * 100

    def text_color(self, color):
        h, s, v = self.rgb_to_hsv(color)
        if v < 55:
            return CAIRO_WHITE
        if s > 80 and (h > 210 or h < 20):
            return CAIRO_WHITE
        return CAIRO_BLACK

    def check_brightness(self, color):
        h, s, v = self.rgb_to_hsv(color)
        return s < 10 and v > 90

    def draw_rounded_rect(self, ctx, rect, radius):
        pi = math.pi
        x, y, w, h = rect
        ctx.move_to(x, y)
        ctx.new_path()
        ctx.arc(x + w - radius, y + radius, radius, -pi / 2, 0)
        ctx.arc(x + w - radius, y + h - radius, radius, 0, pi / 2)
        ctx.arc(x + radius, y + h - radius, radius, pi / 2, pi)
        ctx.arc(x + radius, y + radius, radius, pi, 3 * pi / 2)
        ctx.close_path()

    def paint(self, _widget, widget_ctx):
        colors = [((0.0, 0.0, 0.0), 'Black'),
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
        w, h = self.get_size()
        cell_max = (w - 2 * BORDER) // CELL_W
        if self.surface is None or self.width != w or self.height != h:
            self.surface = cairo.ImageSurface(cairo.FORMAT_RGB24, w, h)
            self.width, self.height = w, h
        self.ctx = cairo.Context(self.surface)
        self.ctx.set_source_rgb(*CAIRO_WHITE)
        self.ctx.paint()

        self.ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        x_count = y_count = 0
        for color, color_name in colors:
            x = BORDER + x_count * CELL_W
            y = BORDER + y_count * CELL_H
            self.ctx.set_source_rgb(*color)
            rect = (x + 2, y + 2, CELL_W - 4, CELL_H - 4)
            self.draw_rounded_rect(self.ctx, rect, 20)
            self.ctx.fill()

            if self.check_brightness(color):
                self.ctx.set_source_rgb(*CAIRO_LIGHT_GRAY)
                rect = (x + 3, y + 3, CELL_W - 6, CELL_H - 6)
                self.draw_rounded_rect(self.ctx, rect, 20)
                self.ctx.set_line_width(1.0)
                self.ctx.set_dash([])
                self.ctx.stroke()

            self.ctx.set_font_size(15)
            label = self.color_to_hex(color)
            ext = self.ctx.text_extents(label)
            self.ctx.move_to(x + CELL_W / 2 - ext.width / 2,
                             y + CELL_H / 2 + ext.height / 2)
            self.ctx.set_source_rgb(*self.text_color(color))
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

        size = CELL_H //3
        self.ctx.set_line_width(8.0)
        self.ctx.set_dash([])
        self.ctx.move_to(x + CELL_W/2, y + CELL_H/2 - size/2)
        self.ctx.line_to(x + CELL_W/2,y + CELL_H/2 + size/2)
        self.ctx.stroke()
        self.ctx.move_to(x + CELL_W/2 - size/2, y + CELL_H/2)
        self.ctx.line_to(x + CELL_W/2 + size/2, y + CELL_H/2)
        self.ctx.stroke()

        # Scroll
        virtual_h = 2 * BORDER + math.ceil(len(colors) / cell_max) * CELL_H
        if virtual_h > h:
            rect_h = h * h / virtual_h
            rect_w = 5
            self.ctx.set_source_rgb(*SEL_BG)
            self.ctx.rectangle(w - rect_w, 0, w, rect_h)
            self.ctx.fill()

        widget_ctx.set_source_surface(self.surface)
        widget_ctx.paint()
