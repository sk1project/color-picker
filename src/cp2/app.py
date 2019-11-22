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


class ColorPickerApp(wal.Application):

    def __init__(self):
        super().__init__()

        self.mw = wal.PaletteWindow(self)
        self.mw.set_title('Color Picker')
        self.mw.set_min_size(620, 460)
        self.mw.center()

        self.run()

    def exit(self, *_args):
        wal.Application.exit(self)
