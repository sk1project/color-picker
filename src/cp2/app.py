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

import logging
import os
import sys

import wal
from cp2 import _, config, dialogs
from cp2.app_cms import AppColorManager
from cp2.app_conf import AppData
from cp2.app_stdout import StreamLogger
from cp2.mw import PaletteWindow
from uc2 import uc2const
from uc2.application import UCApplication
from uc2.formats import get_loader
from uc2.formats.skp.skp_presenter import SKP_Presenter
from uc2.utils.mixutils import config_logging


LOG = logging.getLogger(__name__)


class ColorPickerApp(wal.Application, UCApplication):
    wins = None

    def __init__(self, path, cfgdir):
        self.path = path

        wal.Application.__init__(self)
        UCApplication.__init__(self, path, cfgdir, False)

        self.appdata = AppData(self, cfgdir)
        log_level = config.log_level
        self.log_filepath = os.path.join(self.appdata.app_config_dir,
                                         '%s.log' % self.appdata.app_proc)
        config_logging(self.log_filepath, log_level)
        sys.stderr = StreamLogger()
        LOG.info('Logging started')

        self.default_cms = AppColorManager(self)

        self.wins = []
        self.new()
        self.run()

    def exit(self, *_args):
        config.save(self.appdata.app_config)
        wal.Application.exit(self)

    def drop_win(self, win):
        self.wins.remove(win)
        if not self.wins:
            self.exit()

    def new(self, filepath=None):
        win = PaletteWindow(
            self, SKP_Presenter(self.appdata, filepath=filepath))
        self.wins.append(win)

    def clear(self, win):
        win.set_doc(SKP_Presenter(self.appdata))

    def open_doc(self, filepath=None, win=None):
        if win:
            filepath = dialogs.get_open_file_name(
                win, config.open_dir, file_types=uc2const.PALETTE_LOADERS)
        if not filepath:
            return
        if os.path.isfile(filepath):
            try:
                loader = get_loader(filepath)
                if not loader:
                    raise LookupError('Cannot find loader for %s' % filepath)
                doc = loader(self.appdata, filepath, convert=True)
            except Exception as e:
                msg = _('Cannot parse file:')
                msg = "%s\n'%s'" % (msg, filepath) + '\n'
                msg2 = _('The file may be corrupted or not supported format')
                wnd = win or self.wins[0]
                dialogs.error_dialog(wnd, self.appdata.app_name, msg, msg2)
                LOG.error('Cannot parse file <%s> %s', filepath, e)
                return
            self.wins.append(PaletteWindow(self, doc))
            config.open_dir = str(os.path.dirname(filepath))

    def save_as_doc(self, doc):
        pass


