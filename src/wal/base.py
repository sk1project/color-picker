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

import os

import gi

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
    dc = None
    hdr = None

    def __init__(self, app):
        self.app = app
        super().__init__()
        self.dc = CanvasDC()
        self.add(self.dc)
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


class CanvasDC(Gtk.DrawingArea):
    surface = None
    ctx = None
    width = 0
    height = 0
    paint_callback = None

    def __init__(self):
        super().__init__()
        self.connect('draw', self.paint)

    def refresh(self):
        self.queue_draw()

    def get_size(self):
        rect = self.get_allocation()
        return rect.width, rect.height

    def set_paint_callback(self, callback):
        self.paint_callback = callback

    def paint(self, _widget, widget_ctx):
        if self.paint_callback:
            self.paint_callback(widget_ctx)
