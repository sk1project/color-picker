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
from cp2 import _
from uc2 import uc2const


def get_open_file_name(parent, default_dir=None, title=None, file_types=None):
    title = title or _('Select file to open')
    default_dir = default_dir or os.path.expanduser('~')

    descr = uc2const.FORMAT_DESCRIPTION
    ext = uc2const.FORMAT_EXTENSION
    all_ = [(['*'], '*.* - All files'), ]
    ft = []
    if file_types:
        for item in file_types:
            ft.append(([f'*.{ext[item][0]}'], descr[item]))
    if ft:
        supported = [ext[0] for ext, _txt in ft]
        ft.insert(0, (supported, _('All supported files')))
    file_types = ft + all_ if ft else all_

    return wal.get_open_file_name(parent, default_dir, title, file_types)


def get_save_file_name(
        parent, path, title=None, file_types=None, path_only=False):
    title = title or _('Save file as...')
    path = path or os.path.expanduser('~')

    descr = uc2const.FORMAT_DESCRIPTION
    ext = uc2const.FORMAT_EXTENSION
    ft = []
    if file_types:
        for item in file_types:
            ft.append(('*.' + ext[item][0], descr[item]))

    ret = wal.get_save_file_name(parent, path, title, ft)
    if not path_only and isinstance(ret, tuple):
        for wildcard, descr in ft:
            if ret[1] == descr:
                index = ft.index((wildcard, descr))

                doc_file = ret[0]
                if os.path.splitext(doc_file)[1] != "." + \
                        uc2const.FORMAT_EXTENSION[file_types[index]][0]:
                    doc_file = os.path.splitext(doc_file)[0] + "." + \
                               uc2const.FORMAT_EXTENSION[file_types[index]][0]

                return doc_file, file_types[index]
    return ret
