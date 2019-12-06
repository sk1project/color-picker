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
from gi.repository import Gtk, Gdk, GLib, Gio


class Application(Gtk.Application):

    def __init__(self):
        Gtk.Application.__init__(self)

    @staticmethod
    def set_app_name(name):
        GLib.set_application_name(name)

    def drop_win(self, win):
        pass

    def run(self):
        Gtk.main()

    def exit(self, *_args):
        Gtk.main_quit()


class PaletteWindow(Gtk.ApplicationWindow):
    app = None
    hdr = None
    dc = None
    canvas = None

    def __init__(self, app):
        self.app = app
        Gtk.ApplicationWindow.__init__(self)
        self.dc = CanvasDC(self)
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

        self.menubtn = Gtk.MenuButton()
        self.menubtn.set_tooltip_text('Open menu')
        icon = Gio.ThemedIcon(name="open-menu-symbolic")
        self.menubtn.add(Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON))
        self.hdr.pack_end(self.menubtn)

    def get_scroll_fg(self):
        context = self.get_style_context()
        bg_color = context.get_background_color(Gtk.StateFlags.SELECTED)
        return tuple(bg_color)

    def make_menu(self, sections):
        menu = Gio.Menu()
        for section in sections:
            section_menu = Gio.Menu()
            for label, name, callback in section:
                action = Gio.SimpleAction.new(name, None)
                action.connect("activate", callback)
                self.add_action(action)
                section_menu.append(label, 'win.' + name)
            menu.append_section(None, section_menu)
        self.menubtn.set_menu_model(menu)

    def make_shortcuts(self, shortcuts):
        accel = Gtk.AccelGroup()
        for shortcut, callback in shortcuts:
            modifier = {
                'None': 0,
                'Ctrl': Gdk.ModifierType.CONTROL_MASK,
                'Alt': Gdk.ModifierType.META_MASK,
                'Shift': Gdk.ModifierType.SHIFT_MASK,
                'Ctrl-Shift': Gdk.ModifierType.CONTROL_MASK |
                Gdk.ModifierType.SHIFT_MASK}.get(shortcut[0])
            accel.connect(Gdk.keyval_from_name(shortcut[1]), modifier,
                          0, callback)
        self.add_accel_group(accel)

    def close_action(self, *_args):
        self.dc.mw = None
        self.destroy()

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


class CanvasEvent:
    event = None

    def __init__(self, event):
        self.event = event

    def get_scroll(self):
        return self.event.get_scroll_deltas()[2]

    def is_ctrl(self):
        return bool(self.event.state & Gdk.ModifierType.CONTROL_MASK)

    def is_alt(self):
        return bool(self.event.state & Gdk.ModifierType.MOD1_MASK)

    def is_shift(self):
        return bool(self.event.state & Gdk.ModifierType.SHIFT_MASK)

    def get_point(self):
        return int(self.event.x), int(self.event.y)

    def get_button(self):
        return self.event.button if hasattr(self.event, 'button') else None


GTK_CURSOR_NAMES = [
    'none', 'default', 'help', 'pointer', 'context-menu', 'progress', 'wait',
    'cell', 'crosshair', 'text', 'vertical-text', 'alias', 'copy', 'no-drop',
    'move', 'not-allowed', 'grab', 'grabbing', 'all-scroll', 'col-resize',
    'row-resize', 'n-resize', 'e-resize', 's-resize', 'w-resize', 'ne-resize',
    'nw-resize', 'sw-resize', 'se-resize', 'ew-resize', 'ns-resize',
    'nesw-resize', 'nwse-resize', 'zoom-in', 'zoom-out', ]


def _cursor_from_name(name):
    # https://lazka.github.io/pgi-docs/Gdk-3.0/classes/Cursor.html#Gdk.Cursor.new_from_name
    # https://developer.gnome.org/gdk3/stable/gdk3-Cursors.html
    return Gdk.Cursor.new_from_name(Gdk.Display.get_default(), name)


CURSORS = {
    'default': _cursor_from_name('default'),
    'arrow': _cursor_from_name('arrow'),
    'pointer': _cursor_from_name('pointer'),
}


def _get_cursor(name):
    if name in GTK_CURSOR_NAMES and name not in CURSORS:
        CURSORS[name] = _cursor_from_name(name)
    elif name not in CURSORS:
        name = 'default'
    return CURSORS[name]


class CanvasDC(Gtk.DrawingArea):
    mw = None
    cursor = 'arrow'
    pressed = False

    def __init__(self, mw):
        self.mw = mw
        super().__init__()
        self.connect('draw', self.paint)
        self.add_events(Gdk.EventMask.SMOOTH_SCROLL_MASK)
        self.connect('scroll-event', self.on_scroll)
        self.add_events(Gdk.EventMask.POINTER_MOTION_MASK)
        self.connect('motion-notify-event', self.on_move)
        self.add_events(Gdk.EventMask.LEAVE_NOTIFY_MASK)
        self.connect('leave-notify-event', self.on_leave)
        self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        self.connect('button-press-event', self.on_btn_press)
        self.add_events(Gdk.EventMask.BUTTON_RELEASE_MASK)
        self.connect('button-release-event', self.on_btn_release)

    def refresh(self):
        self.queue_draw()

    def get_size(self):
        rect = self.get_allocation()
        return rect.width, rect.height

    def set_cursor(self, cursor_name):
        if not cursor_name == self.cursor:
            self.cursor = cursor_name
            self.get_root_window().set_cursor(_get_cursor(cursor_name))

    def paint(self, _widget, widget_ctx):
        if self.mw and self.mw.canvas:
            self.mw.canvas.paint(widget_ctx)

    def on_scroll(self, _widget, event):
        if self.mw and self.mw.canvas:
            self.mw.canvas.on_scroll(CanvasEvent(event))

    def on_move(self, _widget, event):
        if self.mw and self.mw.canvas:
            if self.pressed:
                print('move')
            self.mw.canvas.on_move(CanvasEvent(event))

    def on_leave(self, _widget, event):
        if self.mw and self.mw.canvas:
            self.mw.canvas.on_leave(CanvasEvent(event))

    def on_btn_press(self, _widget, event):
        if self.mw and self.mw.canvas:
            if event.button == 1:
                self.mw.canvas.on_left_pressed(CanvasEvent(event))
            elif event.button == 3:
                self.mw.canvas.on_right_pressed(CanvasEvent(event))

    def on_btn_release(self, _widget, event):
        if self.mw and self.mw.canvas:
            if event.button == 1:
                self.mw.canvas.on_left_released(CanvasEvent(event))
            elif event.button == 3:
                self.mw.canvas.on_right_released(CanvasEvent(event))
