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

import uc2

from . import app_conf

_ = uc2._
config = app_conf.AppConfig()


def read_locale(cfg_file):
    lang = 'system'
    if os.path.isfile(cfg_file):
        try:
            with open(cfg_file, 'r') as fp:
                while True:
                    line = fp.readline()
                    if not line:
                        break
                    if line.startswith('language'):
                        lang = line.split('=')[1].strip().replace('\'', '')
                        break
        except Exception:
            lang = 'system'
    return lang


def init_config(cfgdir='~'):
    """sK1 config initialization"""

    cfg_dir = os.path.join(cfgdir, '.config', 'color-picker')
    cfg_file = os.path.join(cfg_dir, 'preferences.cfg')
    resource_dir = os.path.join(__path__[0], 'share')

    # Setting locale before app initialization
    lang = read_locale(cfg_file)
    lang_path = os.path.join(resource_dir, 'locales')
    _.set_locale('color-picker', lang_path, lang)

    global config
    config = app_conf.get_app_config()
    config.load(cfg_file)
    config.resource_dir = resource_dir


def run():
    cfgdir = os.path.expanduser('~')
    _pkgdir = __path__[0]
    init_config(cfgdir)
    from .app import ColorPickerApp
    ColorPickerApp(_pkgdir, cfgdir)
