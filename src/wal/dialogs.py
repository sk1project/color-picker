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


def _add_filters(dialog, file_types):
    for file_pattern, file_type_name in file_types:
        filter_any = Gtk.FileFilter()
        filter_any.add_pattern(file_pattern)
        filter_any.set_name(file_type_name)
        dialog.add_filter(filter_any)


def get_open_file_name(parent, default_dir, title, file_types='*'):
    dialog = Gtk.FileChooserDialog(title, parent,
                                   Gtk.FileChooserAction.OPEN,
                                   (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                    Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
    dialog.set_current_folder(default_dir)
    dialog.set_default_response(Gtk.ResponseType.OK)
    _add_filters(dialog, file_types)

    response = dialog.run()
    ret = dialog.get_filename().strip() \
        if response == Gtk.ResponseType.OK else None
    dialog.destroy()
    return ret or None


def get_save_file_name():
    pass


def error_dialog(parent, title, msg, secondary_msg=None):
    dialog = Gtk.MessageDialog(
        parent, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.OK, msg)

    if secondary_msg:
        dialog.format_secondary_text(secondary_msg)
    dialog.run()
    dialog.destroy()


def msg_dialog(parent, title, msg, secondary_msg=None):
    dialog = Gtk.MessageDialog(
        parent, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.OK, msg)

    if secondary_msg:
        dialog.format_secondary_text(secondary_msg)
    dialog.run()
    dialog.destroy()
