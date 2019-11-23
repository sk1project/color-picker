# -*- coding: utf-8 -*-
#
#   pkgconfig utils
#
# 	Copyright (C) 2018 by Igor E. Novikov
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

import subprocess


def get_pkg_version(pkg_name):
    process = subprocess.Popen(["pkg-config", "--modversion", pkg_name],
                               stdout=subprocess.PIPE)
    output, err = process.communicate()
    return output.strip()


def get_pkg_includes(pkg_names):
    includes = []
    for item in pkg_names:
        process = subprocess.Popen(["pkg-config", "--cflags-only-I", item],
                                   stdout=subprocess.PIPE)
        output, err = process.communicate()
        names = output.replace('-I', '').strip().split(' ')
        for name in names:
            if name not in includes:
                includes.append(name)
    return includes


def get_pkg_libs(pkg_names):
    libs = []
    for item in pkg_names:
        process = subprocess.Popen(["pkg-config", "--libs-only-l", item],
                                   stdout=subprocess.PIPE)
        output, err = process.communicate()
        names = output.decode().replace('-l', '').strip().split(' ')
        for name in names:
            if name not in libs:
                libs.append(name)
    return libs


def get_pkg_cflags(pkg_names):
    flags = []
    for item in pkg_names:
        process = subprocess.Popen(["pkg-config", "--cflags-only-other", item],
                                   stdout=subprocess.PIPE)
        output, err = process.communicate()
        names = output.strip().split(' ')
        for name in names:
            if name not in flags:
                flags.append(name)
    return flags
