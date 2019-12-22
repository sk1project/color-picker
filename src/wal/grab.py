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

import cairo
import gi

from .base import get_cursor

gi.require_version("Gtk", "3.0")
from gi.repository import Gdk, Gtk

NORMAL_TRAFO = cairo.Matrix(1, 0, 0, 1, 0, 0)


class Grabber:
    mw = None
    canvas = None
    w = None
    pointer = None
    keyboard = None
    lock = False
    size = (151, 151)
    pb = None
    handlers = None

    def _set_devices(self):
        device_manager = self.mw.get_screen().get_display().get_device_manager()
        self.pointer = device_manager.get_client_pointer()
        kbds = [device
                for device in device_manager.list_devices(Gdk.DeviceType.MASTER)
                if device.get_property("input-source") ==
                Gdk.InputSource.KEYBOARD]
        self.keyboard = kbds[0] if len(kbds) > 0 else None

        self.w = Gtk.Window()
        self.w.set_size_request(1, 1)
        self.w.move(0, 0)
        screen = self.w.get_screen()
        visual = screen.get_rgba_visual()
        if visual and screen.is_composited():
            self.w.set_visual(visual)

        self.w.set_app_paintable(True)
        self.w.set_decorated(False)

        self.w.add_events(Gdk.EventMask.POINTER_MOTION_MASK)
        self.w.add_events(Gdk.EventMask.SMOOTH_SCROLL_MASK)
        self.w.add_events(Gdk.EventMask.KEY_PRESS_MASK)
        self.w.set_modal(self.mw)

        self.handlers = [
            self.w.connect("button-press-event", self.on_btn_press),
            self.w.connect("scroll-event", self.on_scroll),
            self.w.connect("key-press-event", self.on_keypress),
            self.w.connect("motion-notify-event", self.on_move),
        ]
        self.w.show_all()

    def __call__(self, canvas):
        self.canvas = canvas
        self.mw = canvas.mw
        self._set_devices()
        self.lock = True

        if self.keyboard:
            self.keyboard.grab(
                self.w.get_window(),
                Gdk.GrabOwnership.APPLICATION,
                True,
                Gdk.EventMask.KEY_PRESS_MASK,
                None,
                Gdk.CURRENT_TIME)
        self.set_cursor()

    def release(self, *_args):
        self.pointer.ungrab(Gdk.CURRENT_TIME)
        if self.keyboard:
            self.keyboard.ungrab(Gdk.CURRENT_TIME)
        self.lock = False
        for handler in self.handlers:
            self.w.disconnect(handler)
        self.w.destroy()

    def get_color_from_pb(self, pb):
        pixel_data = pb.get_pixels()
        w, h = self.size
        rs = pb.get_rowstride()
        offset = rs * (h // 2) + (rs // w) * (w // 2)
        return [v / 255.0 for v in pixel_data[offset:offset + 3]]

    def set_cursor(self):
        pointer, x, y = self.pointer.get_position()
        w, h = self.size

        self.pb = Gdk.pixbuf_get_from_window(
            Gdk.get_default_root_window(), x - (w // 2), y - (h // 2), w, h)

        cursor = get_cursor('crosshair')

        self.pointer.grab(
            self.w.get_window(),
            Gdk.GrabOwnership.APPLICATION,
            True,
            (Gdk.EventMask.BUTTON_PRESS_MASK |
             Gdk.EventMask.POINTER_MOTION_MASK |
             Gdk.EventMask.SCROLL_MASK),
            cursor,
            Gdk.CURRENT_TIME)

    def on_move(self, *_args):
        if self.lock:
            self.set_cursor()

    def on_keypress(self, _widget, event):
        if self.lock and event.keyval == Gdk.KEY_Escape:
            self.release()

    def on_btn_press(self, _widget, event):
        if self.lock:
            if event.button == 1:
                self.mw.add_color(self.get_color_from_pb(self.pb))
                if event.state & Gdk.ModifierType.CONTROL_MASK or \
                        event.state & Gdk.ModifierType.SHIFT_MASK:
                    return True
            self.release()

    def on_scroll(self, _widget, event):
        pass


class ZoomedGrabber(Grabber):
    zoom = 3

    def __init__(self):
        super().__init__()

    def __call__(self, canvas):
        self.zoom = 3
        Grabber.__call__(self, canvas)

    def set_cursor(self):
        pointer, x, y = self.pointer.get_position()
        w, h = self.size

        self.pb = Gdk.pixbuf_get_from_window(
            Gdk.get_default_root_window(), x - (w // 2), y - (h // 2), w, h)

        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
        ctx = cairo.Context(surface)
        trafo = (self.zoom, 0, 0, self.zoom,
                 -(self.zoom - 1) * w // 2, -(self.zoom - 1) * h // 2)
        ctx.set_matrix(cairo.Matrix(*trafo))

        Gdk.cairo_set_source_pixbuf(ctx, self.pb, 0, 0)
        ctx.get_source().set_filter(cairo.FILTER_NEAREST)
        ctx.paint()

        ctx.set_antialias(cairo.ANTIALIAS_NONE)
        ctx.set_matrix(NORMAL_TRAFO)
        ctx.set_source_rgb(0, 0, 0)
        ctx.set_line_width(1)
        ctx.rectangle(1, 1, w - 1, h - 1)
        ctx.stroke()

        size = 10
        x0, y0 = w // 2 + 1, h // 2 + 1
        ctx.rectangle(x0 - size / 2, y0 - size / 2, size, size)
        ctx.set_source_rgb(1, 0, 0)
        ctx.stroke()
        ctx.rectangle(x0 - size / 2 - 1, y0 - size / 2 - 1, size + 2, size + 2)
        ctx.set_source_rgb(1, 1, 1)
        ctx.stroke()

        cursor_pb = Gdk.pixbuf_get_from_surface(surface, 0, 0, w, h)

        cursor = Gdk.Cursor.new_from_pixbuf(
            self.w.get_screen().get_display(),
            cursor_pb, w // 2, h // 2)

        self.pointer.grab(
            self.w.get_window(),
            Gdk.GrabOwnership.APPLICATION,
            True,
            (Gdk.EventMask.BUTTON_PRESS_MASK |
             Gdk.EventMask.POINTER_MOTION_MASK |
             Gdk.EventMask.SCROLL_MASK),
            cursor,
            Gdk.CURRENT_TIME)

    def on_scroll(self, _widget, event):
        if self.lock:
            if event.direction == Gdk.ScrollDirection.UP:
                self.zoom = min(self.zoom + 2, 30)
            elif event.direction == Gdk.ScrollDirection.DOWN:
                self.zoom = max(self.zoom - 2, 3)
            self.set_cursor()


grabber = Grabber()
zoomed_grabber = ZoomedGrabber()


def pick_color(canvas):
    grabber(canvas)


def pick_color_zoomed(canvas):
    zoomed_grabber(canvas)
