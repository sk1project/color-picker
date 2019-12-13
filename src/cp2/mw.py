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

import copy
import wal
from cp2 import _, config
from cp2.canvas import Canvas
import uc2.cms
from uc2 import uc2const
from . import api


class PaletteWindow(wal.PaletteWindow):
    canvas = None

    def __init__(self, app, doc):
        wal.PaletteWindow.__init__(self, app)

        menu = [
            [(_('New palette'), 'new', self.on_new), ],
            [
                (_('Open palette...'), 'open', self.on_open),
                # (_('Paste from file...'), 'paste-from', self.on_paste_from),
                (_('Save as...'), 'save-as', self.on_save_as),
                # (_('Clear palette'), 'clear', self.on_clear),
            ],
            [
                (_('Palette Collection'), 'palettes', self.on_palettes),
            ],
            [
                (_('Online help'), 'online-help', self.stub),
                (_('About Color Picker'), 'about', self.stub),
            ],
            [(_('Exit'), 'exit', self.app.exit), ],
        ]
        self.make_menu(menu)

        acc_keys = [
            [('Ctrl', 'N'), self.on_new],
            [('Ctrl', 'O'), self.on_open],
            [('Ctrl', 'S'), self.on_save_as],
            [('None', 'Home'), self.go_home],
            [('None', 'End'), self.go_end],
            [('None', 'KP_Home'), self.go_home],
            [('None', 'KP_End'), self.go_end],
            [('None', 'Page_Up'), self.page_up],
            [('None', 'Page_Down'), self.page_down],
            [('None', 'KP_Page_Up'), self.page_up],
            [('None', 'KP_Page_Down'), self.page_down],
            [('Ctrl', 'Up'), self.canvas_up],
            [('Ctrl', 'Down'), self.canvas_down],
            [('Ctrl', 'KP_Up'), self.canvas_up],
            [('Ctrl', 'KP_Down'), self.canvas_down],
            [('Ctrl', 'Z'), self.canvas_undo],
            [('Ctrl-Shift', 'Z'), self.canvas_redo],

            [('Ctrl-Shift', 'A'), self.deselect],
            [('Ctrl', 'A'), self.select_all],
            [('None', 'Delete'), self.delete_selected],
            [('None', 'KP_Delete'), self.delete_selected],
            [('Ctrl', 'C'), self.copy_selected],
            [('Ctrl', 'X'), self.cut_selected],
        ]
        self.make_shortcuts(acc_keys)

        self.set_min_size(*config.mw_min_size)
        self.center()
        self.show()
        self.set_doc(doc)

    def set_doc(self, doc):
        if self.canvas:
            self.canvas.destroy()
        self.canvas = Canvas(self, doc)
        self.dc.refresh()

    def can_be_reloaded(self):
        return not bool(self.canvas.doc.model.colors)

    def close_action(self, *_args):
        wal.PaletteWindow.destroy(self)
        self.app.drop_win(self)

    def stub(self, *_args):
        print('stub')

    def on_new(self, *_args):
        self.app.new()

    def on_open(self, *_args):
        self.app.open_doc(win=self)

    def on_paste_from(self, *_args):
        self.app.paste_from(win=self)

    def on_save_as(self, *_args):
        self.app.save_as_doc(self.canvas.doc, self)

    def on_clear(self, *_args):
        self.app.clear(self)

    def on_palettes(self, *_args):
        self.app.open_url('https://sk1project.net/palettes/')

    def go_home(self, *_args):
        self.canvas.go_home()

    def go_end(self, *_args):
        self.canvas.go_end()

    def page_up(self, *_args):
        self.canvas.page_up()

    def page_down(self, *_args):
        self.canvas.page_down()

    def canvas_up(self, *_args):
        self.canvas.scroll_up()

    def canvas_down(self, *_args):
        self.canvas.scroll_down()

    def canvas_undo(self, *_args):
        self.canvas.history.undo()

    def canvas_redo(self, *_args):
        self.canvas.history.redo()

    def select_all(self, *_args):
        if self.canvas.grid.cells:
            self.canvas.selection = [] + self.canvas.grid.cells
            self.canvas.reflect_transaction()

    def deselect(self, *_args):
        if self.canvas.selection:
            self.canvas.selection = []
            self.canvas.reflect_transaction()

    def delete_selected(self, *_args):
        if self.canvas.selection:
            api.delete_selected(self.canvas)

    def copy_selected(self, *_args):
        selection = self.canvas.selection
        if selection:
            selected = [copy.deepcopy(cell.color) for cell in selection]
            txt = self._colors2txt(selected)
            wal.set_to_clipboard(txt)
            wal.set_to_clipboard(selected, False)

    def cut_selected(self, *_args):
        self.copy_selected()
        self.delete_selected()

    def _colors2txt(self, colors):
        return ' '.join([uc2.cms.rgb_to_hexcolor(color[1]) for color in colors])

    def _txt2colors(self, txt):
        colors = []
        for item in txt.split():
            if item.startswith('#') and len(item) in (4,7):
                try:
                    colors.append(uc2.cms.hexcolor_to_rgb(item))
                except Exception:
                    pass
        return [[uc2const.COLOR_RGB, clr, 1.0, ''] for clr in colors]

    def paste(self, *_args):
        colors = wal.get_from_clipboard(False)
        txt = wal.get_from_clipboard()

        if not colors and not txt:
            return
        elif not colors and txt:
            colors = self._txt2colors(txt)
        elif colors and txt:
            if self._colors2txt(colors) != txt:
                clrs = self._txt2colors(txt)
                colors = clrs or colors

        if not colors:
            return

        selection = self.canvas.selection
        if len(selection)==1:
            pass
        else:
            api.add_colors(self.canvas, colors)
