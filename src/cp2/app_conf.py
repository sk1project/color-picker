# -*- coding: utf-8 -*-
#
#  Copyright (C) 2011-2018 by Igor E. Novikov
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os

from cp2 import events, appconst
from uc2 import uc2const
from uc2.uc2conf import UCConfig, UCData
from uc2.utils import system, fsutils


class AppData(UCData):
    app_name = 'Color Picker'
    app_proc = 'color-picker'
    app_org = 'sK1 Project'
    app_domain = 'sk1project.net'
    app_icon = None
    doc_icon = None
    version = appconst.VERSION
    revision = appconst.REVISION
    build = appconst.BUILD
    app_config_dir = ''
    plugin_dir = ''
    app_palette_dir = ''
    app_temp_dir = ''
    plugin_dirs = []

    def __init__(self, app, cfgdir='~'):
        # --- Init paths
        path = fsutils.expanduser(os.path.join(cfgdir, '.config', 'color-picker'))
        self.app_config_dir = path

        UCData.__init__(self, app, check=False)
        self.check_config_dirs()

        self.app_palette_dir = os.path.join(path, 'palettes')
        self.plugin_dir = os.path.join(path, 'cp2_custom_plugins')
        self.app_temp_dir = os.path.join(path, 'temp')

        # --- Check config directories
        paths = (self.app_palette_dir, self.plugin_dir, self.app_temp_dir)
        [fsutils.makedirs(item) for item in paths if not fsutils.exists(item)]

        plugin_dir_init = os.path.join(self.plugin_dir, '__init__.py')
        if not fsutils.exists(plugin_dir_init):
            fsutils.get_fileptr(plugin_dir_init, True).close()


class AppConfig(UCConfig):
    def __init__(self):
        self.palette_files = {}
        UCConfig.__init__(self)

    def __setattr__(self, attr, value):
        if attr in ['filename', 'app']:
            self.__dict__[attr] = value
            return
        if not hasattr(self, attr) or getattr(self, attr) != value:
            self.__dict__[attr] = value
            events.emit(events.CONFIG_MODIFIED, attr, value)

    def get_defaults(self):
        defaults = AppConfig.__dict__.copy()
        defaults.update(UCConfig.get_defaults(self))
        return defaults

    # ============== Application pointer ===============
    app = None
    # ============== GENERIC SECTION ===================
    os = system.LINUX
    os_name = system.UBUNTU
    log_level = 'INFO'
    language = 'system'
    app_server = True

    history_size = 100
    history_list_size = 10
    make_backup = True
    make_export_backup = False
    active_plugins = None

    # ============== UI SECTION ===================
    mw_maximized = 0
    mw_size = (1000, 700)
    mw_min_size = (1000, 700)
    mw_width = 1000
    mw_height = 650
    mw_min_width = 1000
    mw_min_height = 650

    # ============== I/O SECTION ===================
    open_dir = '~'
    save_dir = '~'
    import_dir = '~'
    export_dir = '~'
    template_dir = '~'
    resource_dir = ''
    plugin_dirs = []
    profile_import_dir = '~'
    collection_dir = '~'
    print_dir = '~'
    log_dir = '~'

    # ============== MOUSE OPTIONS ================
    mouse_scroll_sensitivity = 3.0

    # ============== PALETTE OPTIONS ================

    # ============== CANVAS OPTIONS ================

    # ============== SNAPPING OPTIONS ================


class LinuxConfig(AppConfig):
    os = system.LINUX
    os_name = system.get_os_name()


class MacosxConfig(AppConfig):
    os = system.MACOSX
    os_name = system.get_os_name()


class WinConfig(AppConfig):
    os = system.WINDOWS
    os_name = system.get_os_name()


def get_app_config():
    os_mapping = {system.MACOSX: MacosxConfig, system.WINDOWS: WinConfig}
    return os_mapping.get(system.get_os_family(), LinuxConfig)()
