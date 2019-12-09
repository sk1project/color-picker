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


def _set_colors(canvas, colors):
    canvas.doc.model.colors = colors


def _set_selection(canvas, selection):
    canvas.selection = selection


def color_transaction(func):
    def func_wrapper(canvas, *args, **kwargs):
        colors_before = [] + canvas.doc.model.colors
        selection_before = [] + canvas.selection

        func(canvas, *args, **kwargs)

        colors_after = [] + canvas.doc.model.colors
        selection_after = [] + canvas.selection
        canvas.history.add_transaction(
            [[
                (_set_colors, canvas, colors_before),
                (_set_selection, canvas, selection_before)
            ], [
                (_set_colors, canvas, colors_after),
                (_set_selection, canvas, selection_after)
            ]]
        )

    return func_wrapper


@color_transaction
def add_color(canvas, color):
    canvas.doc.model.colors = canvas.doc.model.colors + [color]
    canvas.selection = [(color, len(canvas.doc.model.colors) - 1)]


@color_transaction
def add_colors(canvas, colors):
    model_colors = [] + canvas.doc.model.colors
    index = len(model_colors)
    model_colors += colors
    canvas.doc.model.colors = model_colors
    selection = []
    for color in colors:
        selection.append((color, index))
        index += 1
