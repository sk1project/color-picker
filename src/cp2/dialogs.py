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

import wal
from wal import error_dialog
from cp2 import _
from uc2 import uc2const


def get_open_file_name(parent, default_dir=None, title=None, file_types=None):
    title = title or _('Select file to open')
    default_dir = default_dir or os.path.expanduser('~')

    descr = uc2const.FORMAT_DESCRIPTION
    ext = uc2const.FORMAT_EXTENSION
    all = [('*', '*.* - All files'), ]
    ft = []
    if file_types:
        for item in file_types:
            ft.append(('*.' + ext[item][0], descr[item]))

    file_types = ft + all if ft else all

    return wal.get_open_file_name(parent, default_dir, title, file_types)
