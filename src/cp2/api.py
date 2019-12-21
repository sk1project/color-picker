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


def _set_cells(canvas, cells):
    canvas.grid.cells = cells


def _set_selection(canvas, selection):
    canvas.selection = selection


def _set_meta(canvas, meta):
    canvas.doc.model.__dict__.update(meta)


def color_transaction(func):
    def func_wrapper(canvas, *args, **kwargs):
        colors_before = [] + canvas.doc.model.colors
        cells_before = [] + canvas.grid.cells
        selection_before = [] + canvas.selection

        func(canvas, *args, **kwargs)

        colors_after = [] + canvas.doc.model.colors
        cells_after = [] + canvas.grid.cells
        selection_after = [] + canvas.selection
        canvas.history.add_transaction(
            [[
                (_set_colors, canvas, colors_before),
                (_set_cells, canvas, cells_before),
                (_set_selection, canvas, selection_before)
            ], [
                (_set_colors, canvas, colors_after),
                (_set_cells, canvas, cells_after),
                (_set_selection, canvas, selection_after)
            ]]
        )

    return func_wrapper


FIELDS = ('name', 'source', 'columns', 'comments')


def meta_transaction(func):
    def func_wrapper(canvas, *args, **kwargs):
        d = canvas.doc.model.__dict__
        meta_before = dict((item, d[item]) for item in FIELDS if item in d)

        func(canvas, *args, **kwargs)

        meta_after = dict((item, d[item]) for item in FIELDS)
        canvas.history.add_transaction(
            [[
                (_set_meta, canvas, meta_before),
            ], [
                (_set_meta, canvas, meta_after),
            ]]
        )

    return func_wrapper


@color_transaction
def add_color(canvas, color):
    canvas.doc.model.colors = canvas.doc.model.colors + [color]
    canvas.selection = [canvas.grid.add_color(color)]


@color_transaction
def add_colors(canvas, colors):
    canvas.doc.model.colors = canvas.doc.model.colors + colors
    canvas.selection = [canvas.grid.add_color(color) for color in colors]


@color_transaction
def delete_selected(canvas):
    for cell in canvas.selection:
        canvas.grid.cells.remove(cell)
    canvas.grid.sync_to()
    canvas.selection = []


@color_transaction
def insert_colors(canvas, cell, colors):
    canvas.selection = []
    index = canvas.grid.cells.index(cell)
    clrs = [] + canvas.doc.model.colors
    canvas.doc.model.colors = clrs[:index] + colors + clrs[index:]
    new_cells = [canvas.grid.make_cell(color) for color in colors]
    cells = canvas.grid.cells
    canvas.grid.cells = cells[:index] + new_cells + cells[index:]
    canvas.selection = new_cells


@color_transaction
def duplicate_selected(canvas):
    cells = canvas.selection
    selection = [] + cells
    for cell in cells:
        index = canvas.grid.cells.index(cell)
        new_cell = canvas.grid.make_cell(cell.color)
        canvas.grid.cells.insert(index, new_cell)
        selection.append(new_cell)
    canvas.grid.sync_to()
    canvas.selection = selection


@color_transaction
def change_color(canvas, cell, color):
    index = canvas.grid.cells.index(cell)
    new_cell = canvas.grid.make_cell(color)
    canvas.grid.cells.insert(index, new_cell)
    canvas.grid.cells.remove(cell)
    canvas.grid.sync_to()
    canvas.selection = [new_cell]


@meta_transaction
def change_meta(canvas, new_meta):
    d = canvas.doc.model.__dict__
    d.update(new_meta)
