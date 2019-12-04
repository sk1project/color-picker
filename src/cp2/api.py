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


class UndoAPI:
    mw = None
    model = None
    app = None
    undo = []
    redo = []
    undo_marked = False
    selection = None
    callback = None

    def __init__(self, mw, callback):
        self.mw = mw
        self.app = mw.app
        self.callback = callback
        self.undo = []
        self.redo = []

    def do_undo(self):
        transaction_list = self.undo[-1][0]
        for transaction in transaction_list:
            self._do_action(transaction)
        tr = self.undo[-1]
        self.undo.remove(tr)
        self.redo.append(tr)
        # self.eventloop.emit(self.eventloop.DOC_MODIFIED)
        if self.undo and self.undo[-1][2]:
            self.callback()
        if not self.undo and not self.undo_marked:
            self.callback()

    def do_redo(self):
        action_list = self.redo[-1][1]
        for action in action_list:
            self._do_action(action)
        tr = self.redo[-1]
        self.redo.remove(tr)
        self.undo.append(tr)
        # self.eventloop.emit(self.eventloop.DOC_MODIFIED)
        if not self.undo or self.undo[-1][2]:
            self.callback()

    def _do_action(self, action):
        if not action:
            return
        if len(action) == 1:
            action[0]()
        else:
            action[0](*action[1:])

    def _clear_history_stack(self, stack):
        for obj in stack:
            if isinstance(obj, list):
                self._clear_history_stack(obj)
        return []

    def add_undo(self, transaction):
        self.redo = self._clear_history_stack(self.redo)
        self.undo.append(transaction)
        # self.eventloop.emit(self.eventloop.DOC_MODIFIED)
        self.callback()

    def save_mark(self):
        for item in self.undo:
            item[2] = False
        for item in self.redo:
            item[2] = False

        if self.undo:
            self.undo[-1][2] = True
            self.undo_marked = True
