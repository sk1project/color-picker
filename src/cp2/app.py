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
import webbrowser

import wal
from cp2 import _, config, dialogs, api
from cp2.app_cms import AppColorManager
from cp2.app_conf import AppData
from cp2.app_stdout import StreamLogger
from cp2.mw import PaletteWindow
from uc2 import uc2const
from uc2.application import UCApplication
from uc2.formats import get_loader, get_saver_by_id
from uc2.formats.skp.skp_presenter import SKP_Presenter
from uc2.utils.mixutils import config_logging

LOG = logging.getLogger(__name__)


class ColorPickerApp(wal.Application, UCApplication):
    wins = None

    def __init__(self, path, cfgdir):
        self.path = path
        wal.Application.__init__(self, application_id=AppData.app_id)

        UCApplication.__init__(self, path, cfgdir, False)
        self.appdata = AppData(self, cfgdir)

        log_level = config.log_level
        self.log_filepath = os.path.join(self.appdata.app_config_dir,
                                         '%s.log' % self.appdata.app_proc)
        config_logging(self.log_filepath, log_level)
        sys.stderr = StreamLogger()
        LOG.info('Logging started')

        self.default_cms = AppColorManager(self)
        LOG.info('Color Manager started')

        self.wins = []

    def do_startup(self):
        wal.Application.do_startup(self)
        wal.init_clipboard()
        self.set_app_name(self.appdata.app_name)

        menu = [[],
                [
                    (_('New palette'), 'new', self.on_new, None),
                    (_('Open palette...'), 'open', self.on_open, None),
                ],
                [
                    (_('Palette Collection'), 'palettes', self.on_palettes,
                     None),
                ],
                [
                    (_('Online help'), 'online-help', self.stub, None),
                    (_('About Color Picker'), 'about', self.stub, None),
                ],
                [(_('Quit'), 'exit', self.exit, None), ],
                ]
        self.make_menu(menu)
        LOG.info('Application startup successful')

    def do_activate(self):
        if not self.wins:
            self.new()
            # Setting scroll fg color
            config.scroll_fg = self.wins[0].get_scroll_fg()
            LOG.info('Application activated')

    def on_new(self, *_args):
        self.new()

    def on_open(self, *_args):
        self.new()
        self.open_doc(win=self.wins[-1])

    def on_palettes(self, *_args):
        self.open_url('https://sk1project.net/palettes/')

    def stub(self, *_args):
        pass

    def exit(self, *_args):
        config.save(self.appdata.app_config)
        wal.Application.exit(self)

    def drop_win(self, win):
        self.wins.remove(win)
        if not self.wins:
            self.exit()

    def new(self, filepath=None):
        doc = SKP_Presenter(self.appdata, filepath=filepath)
        win = PaletteWindow(self, doc)
        win.present()
        self.wins.append(win)
        LOG.info('New palette created')

    def clear(self, win):
        win.set_doc(SKP_Presenter(self.appdata))
        LOG.info('Palette reloaded from scratch')

    def _get_doc_form_file(self, filepath=None, win=None):
        doc = None
        wnd = win or self.wins[0]

        if wnd and not filepath:
            filepath = dialogs.get_open_file_name(
                wnd, config.open_dir, file_types=uc2const.PALETTE_LOADERS)
        if not filepath:
            return

        if os.path.isfile(filepath):
            try:
                loader = get_loader(filepath)
                if not loader:
                    raise LookupError('Cannot find loader for %s' % filepath)
                doc = loader(self.appdata, filepath, convert=True)
                config.open_dir = str(os.path.dirname(filepath))
            except Exception as e:
                msg = _('Cannot parse file:')
                msg = "%s\n'%s'" % (msg, filepath) + '\n'
                msg2 = _('The file may be corrupted or not supported format')
                dialogs.error_dialog(wnd, self.appdata.app_name, msg, msg2)
                LOG.exception('Cannot parse file <%s>' % filepath, e)
        return doc

    def open_doc(self, filepath=None, win=None):
        doc = self._get_doc_form_file(filepath, win)
        if not doc:
            return
        if win.can_be_reloaded():
            win.set_doc(doc)
            LOG.info('Palette reloaded from %s', doc.doc_file)
        else:
            self.wins.append(PaletteWindow(self, doc))
            LOG.info('Palette opened from %s', doc.doc_file)

    def paste_from(self, filepath=None, win=None):
        doc = self._get_doc_form_file(filepath, win)
        if not doc:
            return

        colors = doc.model.colors
        api.add_colors(win.canvas, colors)
        LOG.info('Palette updated from %s', doc.doc_file)

    def save_as_doc(self, doc, win=None):
        wnd = win or self.wins[0]
        doc_file = doc.doc_file
        doc_file = doc_file or doc.model.name
        if os.path.splitext(doc_file)[1] != "." + \
                uc2const.FORMAT_EXTENSION[uc2const.SKP][0]:
            doc_file = os.path.splitext(doc_file)[0] + "." + \
                       uc2const.FORMAT_EXTENSION[uc2const.SKP][0]
        if not os.path.exists(os.path.dirname(doc_file)):
            doc_file = os.path.join(config.save_dir,
                                    os.path.basename(doc_file))
        ret = dialogs.get_save_file_name(
            wnd, doc_file, file_types=uc2const.PALETTE_SAVERS)
        if ret and len(ret) == 2:
            try:
                doc_file, saver_id = ret
                saver = get_saver_by_id(saver_id)
                saver(doc, doc_file, translate=False, convert=True)
                LOG.info('Palette saved to %s', doc_file)
            except Exception as e:
                msg = _('Cannot save file:')
                msg = "%s\n'%s'" % (msg, doc_file) + '\n'
                msg2 = _('Details see in logs')
                dialogs.error_dialog(wnd, self.appdata.app_name, msg, msg2)
                LOG.exception('Cannot save file <%s>' % doc_file, e)

    def open_url(self, url):
        webbrowser.open(url, new=1, autoraise=True)
        LOG.info('URL %s opened in default browser', url)
