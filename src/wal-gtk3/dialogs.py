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
from gi.repository import Gtk, Gdk


def _add_filters(dialog, file_types):
    for file_patterns, file_type_name in file_types:
        filter_any = Gtk.FileFilter()
        for file_pattern in file_patterns:
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


def get_save_file_name(parent, path, title, file_types='*'):
    dialog = Gtk.FileChooserDialog(title, parent,
                                   Gtk.FileChooserAction.SAVE,
                                   (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                    Gtk.STOCK_SAVE, Gtk.ResponseType.OK))
    path = os.path.expanduser(path)
    dialog.set_current_folder(os.path.dirname(path))
    dialog.set_current_name(os.path.basename(path))
    dialog.set_default_response(Gtk.ResponseType.OK)
    dialog.set_do_overwrite_confirmation(True)
    _add_filters(dialog, file_types)

    response = dialog.run()
    ret = dialog.get_filename().strip() \
        if response == Gtk.ResponseType.OK else None
    if ret:
        ret = (ret, dialog.get_filter().get_name())
    dialog.destroy()
    return ret


def error_dialog(parent, title, msg, secondary_msg=None):
    dialog = Gtk.MessageDialog(
        parent, Gtk.DialogFlags.DESTROY_WITH_PARENT,
        Gtk.MessageType.ERROR, Gtk.ButtonsType.OK, msg)

    if secondary_msg:
        dialog.format_secondary_text(secondary_msg)
    dialog.run()
    dialog.destroy()


def msg_dialog(parent, title, msg, secondary_msg=None):
    dialog = Gtk.MessageDialog(
        parent, Gtk.DialogFlags.DESTROY_WITH_PARENT,
        Gtk.MessageType.ERROR, Gtk.ButtonsType.OK, msg)

    if secondary_msg:
        dialog.format_secondary_text(secondary_msg)
    dialog.run()
    dialog.destroy()


def yesno_dialog(parent, title, msg, secondary_msg=None):
    dialog = Gtk.MessageDialog(
        parent, Gtk.DialogFlags.DESTROY_WITH_PARENT,
        Gtk.MessageType.QUESTION,
        Gtk.ButtonsType.YES_NO, msg)

    if secondary_msg:
        dialog.format_secondary_text(secondary_msg)
    response = dialog.run()
    ret = response == Gtk.ResponseType.YES
    dialog.destroy()
    return ret


def color_dialog(parent, title=None, color=None):
    ret_color = None
    colordialog = Gtk.ColorChooserDialog(title or 'Select color', parent)
    colordialog.set_use_alpha(False)
    if color:
        colordialog.set_rgba(Gdk.RGBA(*color))

    if colordialog.run() == Gtk.ResponseType.OK:
        ret_color = list(colordialog.get_rgba())[:3]

    colordialog.destroy()
    return ret_color


LICENSES = {
    'LGPLv3': Gtk.License.LGPL_3_0,
    'LGPLv2': Gtk.License.LGPL_2_1,
    'AGPLv3': Gtk.License.AGPL_3_0,
    'GPLv2': Gtk.License.GPL_2_0,
    'GPLv3': Gtk.License.GPL_3_0,
}


def about_dialog(**kwargs):
    license_type = kwargs.get('license_type')
    kwargs['license_type'] = LICENSES.get(license_type)

    about_dlg = Gtk.AboutDialog(**kwargs)
    about_dlg.run()
    about_dlg.destroy()


class PropertiesDialog(Gtk.Dialog):
    """
    input dict
    {'name':(_name,name),
    'source': (_source, source),
    'columns': (_columns, int),
    'comments': (_comments, comments),
    }
    """

    def __init__(self, parent, title, **kwargs):
        Gtk.Dialog.__init__(self, title, parent, 0,
                            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                             Gtk.STOCK_OK, Gtk.ResponseType.OK))

        self.set_size_request(400, 300)

        grid = Gtk.Grid()
        grid.set_border_width(10)
        grid.set_column_spacing(10)
        grid.set_row_spacing(10)

        grid.attach(Gtk.Label(kwargs['name'][0]), 0, 0, 1, 1)
        self.name = Gtk.Entry()
        self.name.set_text(kwargs['name'][1])
        self.name.set_hexpand(True)
        grid.attach(self.name, 1, 0, 1, 1)

        grid.attach(Gtk.Label(kwargs['source'][0]), 0, 1, 1, 1)
        self.source = Gtk.Entry()
        self.source.set_text(kwargs['source'][1])
        grid.attach(self.source, 1, 1, 1, 1)

        grid.attach(Gtk.Label(kwargs['columns'][0]), 0, 2, 1, 1)
        adjustment = Gtk.Adjustment(value=kwargs['columns'][1] or 5,
                                    lower=1,
                                    upper=50,
                                    step_increment=1,
                                    page_increment=1,
                                    page_size=0)
        self.columns = Gtk.SpinButton(adjustment=adjustment)
        self.columns.set_hexpand(False)
        hbox = Gtk.HBox()
        hbox.pack_start(self.columns, False, False, 0)
        grid.attach(hbox, 1, 2, 1, 1)

        grid.attach(Gtk.Label(kwargs['comments'][0]), 0, 3, 1, 1)
        self.comments = Gtk.TextView()
        self.comments.get_buffer().set_text(kwargs['comments'][1])
        self.comments.set_vexpand(True)
        self.comments.set_border_width(1)
        grid.attach(self.comments, 1, 3, 1, 1)

        self.get_content_area().pack_start(grid, True, True, 0)

        self.show_all()

    def get_metadata(self):
        start = self.comments.get_buffer().get_start_iter()
        end = self.comments.get_buffer().get_end_iter()
        return {
            'name': self.name.get_text(),
            'source': self.source.get_text(),
            'columns': self.columns.get_value(),
            'comments': self.comments.get_buffer().get_text(start, end, True),
        }


def properties_dialog(parent, title, **kwargs):
    prop_dlg = PropertiesDialog(parent, title, **kwargs)
    metadata = None
    if prop_dlg.run() == Gtk.ResponseType.OK:
        metadata = prop_dlg.get_metadata()
    prop_dlg.destroy()
    return metadata
