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
        path = fsutils.expanduser(
            os.path.join(cfgdir, '.config', 'color-picker'))
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
    mw_min_size = (620, 460)

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

    # ============== SCROLL OPTIONS ================
    mouse_scroll_sensitivity = 20
    scroll_normal = 5
    scroll_hover = 10

    # ============== PALETTE OPTIONS ================
    cell_width = 100
    cell_height = 100

    # ============== CANVAS OPTIONS ================
    canvas_border = 20
    canvas_fg = (0.0, 0.0, 0.0)
    canvas_bg = (1.0, 1.0, 1.0)

    # colors
    addbutton_fg = (0.9, 0.9, 0.9)
    cell_border = 2
    cell_border_color = (0.9, 0.9, 0.9)
    cell_corner_radius = 18
    cell_mark_center = (84, 16)
    cell_mark_border = 1.0
    cell_mark_border_color = (0.0, 0.0, 0.0)
    cell_mark_bg = (1.0, 1.0, 1.0)
    cell_mark_fg = (0.0, 0.6, 0.0)
    cell_mark_radius = 9
    cell_mark_internal_radius = 5

    # Scroll fg will be overridden in runtime by gtk3 theme selection bg value
    scroll_fg = (0.9375, 0.46484375, 0.2734375)  # #F07746

    # ============== SNAPPING OPTIONS ================


class LinuxConfig(AppConfig):
    os = system.LINUX
    os_name = system.get_os_name()


class MacosxConfig(AppConfig):
    os = system.MACOS
    os_name = system.get_os_name()


class WinConfig(AppConfig):
    os = system.WINDOWS
    os_name = system.get_os_name()


def get_app_config():
    os_mapping = {system.MACOS: MacosxConfig, system.WINDOWS: WinConfig}
    return os_mapping.get(system.get_os_family(), LinuxConfig)()
