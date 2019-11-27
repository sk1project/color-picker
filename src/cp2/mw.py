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
from cp2.rend import CairoRenderer


class PaletteWindow(wal.PaletteWindow):
    doc = None
    canvas = None

    def __init__(self, app, doc):
        wal.PaletteWindow.__init__(self, app)
        self.set_title(self.app.appdata.app_name)
        self.set_min_size(*config.mw_min_size)
        self.center()
        self.show()
        self.set_doc(doc)

    def set_doc(self, doc):
        self.doc = doc
        if not self.doc.model.name:
            self.doc.model.name = _('Untitled palette')
        self.set_subtitle(self.doc.model.name)
        self.canvas = Canvas(self)
        self.dc.refresh()


class Canvas:
    app = None
    mw = None
    dc = None
    rend = None
    cms = None
    dy = 0
    max_dy = 0

    def __init__(self, mw):
        self.mw = mw
        self.app = mw.app
        self.dc = mw.dc
        self.cms = self.app.default_cms
        self.rend = CairoRenderer(self)
        self.dc.set_paint_callback(self.rend.paint)



