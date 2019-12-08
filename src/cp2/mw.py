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

import wal
from cp2 import _, config
from cp2.canvas import Canvas


class PaletteWindow(wal.PaletteWindow):
    canvas = None

    def __init__(self, app, doc):
        wal.PaletteWindow.__init__(self, app)

        menu = [
            [(_('New palette'), 'new', self.on_new), ],
            [
                (_('Open palette...'), 'open', self.on_open),
                (_('Paste from file...'), 'paste-from', self.on_paste_from),
                (_('Save as...'), 'save-as', self.on_save_as),
                (_('Clear palette'), 'clear', self.on_clear),
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
        ]
        self.make_shortcuts(acc_keys)

        self.set_title(self.app.appdata.app_name)
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
        # TODO should be history check
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
