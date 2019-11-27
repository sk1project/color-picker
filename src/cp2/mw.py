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
from cp2 import config


class PaletteWindow(wal.PaletteWindow):
    def __init__(self, app, doc):
        wal.PaletteWindow.__init__(self, app)
        self.doc = doc

        self.set_title(self.app.appdata.app_name)
        self.set_min_size(*config.mw_min_size)
        self.center()
        self.show()
