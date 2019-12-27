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

import colorsys
import math
import os
import time
from copy import deepcopy

import cairo

import uc2.cms
import wal
from cp2 import _, config, api
from uc2 import uc2const
from uc2.utils.mixutils import Decomposable

"""
undo/redo actions are lists of callable and args:
[(callable, arg0, arg1...), (callable, arg0, arg1...), ...]

Transaction - list of [undo_actions, redo_actions]

Undo stack format:
[transaction, transaction, ... ,transaction]

index - last transaction (0 if Undo stack is empty)
saved index - transaction saved in file (-1 if not saved)
"""


class UndoHistory(Decomposable):
    canvas = None
    undo_stack = None
    index = 0
    saved_index = 0

    def __init__(self, canvas):
        self.canvas = canvas
        self.undo_stack = [[None, None]]

    def add_transaction(self, transaction):
        if self.index < len(self.undo_stack) - 1:
            self.undo_stack = self.undo_stack[:self.index + 1]
        self.undo_stack[-1][1] = transaction[1]
        self.undo_stack.append([transaction[0], None])
        self.index += 1
        self.canvas.reflect_transaction()

    def is_undo(self):
        return self.index > 0

    def is_redo(self):
        return bool(self.undo_stack[self.index][1])

    def is_saved(self):
        return self.index == self.saved_index

    def set_saved(self):
        self.saved_index = self.index
        self.canvas.reflect_transaction()

    # noinspection PyTypeChecker
    def undo(self):
        if self.is_undo():
            for item in self.undo_stack[self.index][0]:
                item[0](*item[1:])
            self.index -= 1
            self.canvas.reflect_transaction()

    # noinspection PyTypeChecker
    def redo(self):
        if self.is_redo():
            for item in self.undo_stack[self.index][1]:
                item[0](*item[1:])
            self.index += 1
            self.canvas.reflect_transaction()


CAIRO_WHITE = (1.0, 1.0, 1.0)
CAIRO_BLACK = (0.0, 0.0, 0.0)
NO_TRAFO = cairo.Matrix(1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
NO_BBOX = (0, 0, 0, 0)


def in_bbox(bbox, point):
    return bbox[0] < point[0] < bbox[2] and bbox[1] < point[1] < bbox[3]


def rect2bbox(rect):
    x, y, w, h = rect
    return x, y, x + w, y + h


# Color processing functions
def rgb_to_hsv(color):
    h, s, v = colorsys.rgb_to_hsv(*color)
    return h * 360, s * 100, v * 100


def text_color(color):
    h, s, v = rgb_to_hsv(color)
    if v < 55:
        return CAIRO_WHITE
    if s > 80 and (h > 210 or h < 20):
        return CAIRO_WHITE
    return CAIRO_BLACK


def check_brightness(color):
    h, s, v = rgb_to_hsv(color)
    return s < 10 and v > 90


# Cairo functions
def draw_rounded_rect(ctx, rect, radius):
    pi = math.pi
    x, y, w, h = rect
    ctx.move_to(x, y)
    ctx.new_path()
    ctx.arc(x + w - radius, y + radius, radius, -pi / 2, 0)
    ctx.arc(x + w - radius, y + h - radius, radius, 0, pi / 2)
    ctx.arc(x + radius, y + h - radius, radius, pi / 2, pi)
    ctx.arc(x + radius, y + radius, radius, pi, 3 * pi / 2)
    ctx.close_path()


class CanvasObj(Decomposable):
    canvas = None
    bbox = NO_BBOX
    cursor = 'arrow'
    active = True
    hover = False

    def __init__(self, canvas):
        self.canvas = canvas

    def paint(self, ctx):
        pass

    def is_over(self, point):
        return in_bbox(self.bbox, point)

    def on_move(self, event):
        point = event.get_point()
        if self.active:
            if self.is_over(point):
                self.canvas.set_cursor(self.cursor)
                if not self.hover:
                    self.hover = True
                    self.canvas.dc.refresh()
                return True
            else:
                if self.hover:
                    self.hover = False
                    self.canvas.dc.refresh()
        return False

    def on_left_pressed(self, event):
        return self.is_over(event.get_point()) and self.active

    def on_left_released(self, _event):
        pass

    def on_left_double_click(self, event):
        pass

    def on_right_pressed(self, event):
        return self.is_over(event.get_point()) and self.active

    def on_right_released(self, _event):
        pass


class LogoObj(CanvasObj):
    logo = None
    cursor = 'pointer'

    def __init__(self, canvas):
        CanvasObj.__init__(self, canvas)
        logo_file = os.path.join(
            config.resource_dir, 'icons', 'color-picker.png')
        self.logo = cairo.ImageSurface.create_from_png(logo_file)

    def on_left_released(self, _event):
        app = self.canvas.app
        app.open_url('https://%s' % app.appdata.app_domain)

    def paint(self, ctx):
        cells = self.canvas.grid.cells
        border = config.canvas_border

        if not cells:
            logo_w, logo_h = self.logo.get_width(), self.logo.get_height()
            dx = self.canvas.width - logo_w - border
            dy = self.canvas.height - logo_h - border
            ctx.set_matrix(cairo.Matrix(1.0, 0.0, 0.0, 1.0, dx, dy))
            ctx.set_source_surface(self.logo)
            ctx.paint()
            ctx.set_matrix(NO_TRAFO)

            ctx.set_font_size(12)
            ctx.set_source_rgb(*config.canvas_fg)
            txt = 'https://%s' % self.canvas.app.appdata.app_domain
            ext = ctx.text_extents(txt)
            ctx.move_to(dx + logo_w / 2 - ext.width / 2, dy + logo_h + 10)
            ctx.show_text(txt)

            self.bbox = (dx + logo_w / 2 - ext.width / 2,
                         dy,
                         dx + logo_w / 2 + ext.width / 2,
                         dy + logo_h + 10 + ext.height)

        self.active = not cells


class ScrollObj(CanvasObj):
    tbbox = NO_BBOX
    start = None
    coef = 1.0

    def on_left_pressed(self, event):
        self.start = event.get_point()
        if not self.is_over(self.start):
            return False
        if in_bbox(self.tbbox, self.start):
            return True
        elif self.start[1] > self.tbbox[3]:
            dy = (self.start[1] - self.tbbox[3] + self.tbbox[1]) / self.coef
        else:
            dy = self.start[1] / self.coef
        self.canvas.dy = dy
        self.canvas.dc.refresh()
        return True

    def on_move(self, event):
        if not self.canvas.left_pressed == self:
            return CanvasObj.on_move(self, event)
        else:
            point = event.get_point()
            dy = self.canvas.dy + (point[1] - self.start[1]) // self.coef
            dy = dy if dy > 0 else 0
            dy = dy if dy < self.canvas.max_dy else self.canvas.max_dy
            self.start = point
            self.canvas.dy = dy
            self.canvas.dc.refresh()
            return True

    def paint(self, ctx):
        w, h = self.canvas.width, self.canvas.height
        sw = config.scroll_hover if self.hover else config.scroll_normal
        self.bbox = (w - config.scroll_hover, 0, w, h)
        virtual_h = self.canvas.virtual_h
        self.tbbox = NO_BBOX
        self.coef = 1.0

        if virtual_h > h:
            self.coef = h / virtual_h
            rect_h = h * self.coef
            rect_w = sw
            y = self.canvas.dy + self.canvas.dy * self.coef
            ctx.set_source_rgba(*config.scroll_fg)
            ctx.rectangle(w - rect_w, y, w, rect_h)
            self.tbbox = (w - rect_w, y, w, y + rect_h)
            ctx.fill()

        self.active = virtual_h > h


class AddButtonObj(CanvasObj):
    cursor = 'pointer'

    def on_left_released(self, _event):
        clr = wal.color_dialog(self.canvas.mw, _('Select color'))
        if clr:
            color = [uc2const.COLOR_RGB, clr, 1.0, '', '']
            api.add_color(self.canvas, color)

    def paint(self, ctx):
        cell_h = config.cell_height
        cell_w = config.cell_width
        border = config.canvas_border
        cell_num = len(self.canvas.grid.cells)
        cell_max = self.canvas.cell_max
        y_count = cell_num // cell_max if cell_max else 0
        x_count = cell_num - cell_max * y_count

        x = border + x_count * cell_w
        y = border + y_count * cell_h
        ctx.set_source_rgb(*config.addbutton_fg)
        rect = (x + 10, y + 10, cell_w - 20, cell_h - 20)
        self.bbox = (border + x_count * cell_w,
                     border + y_count * cell_h - self.canvas.dy,
                     border + (x_count + 1) * cell_w,
                     border + (y_count + 1) * cell_h - self.canvas.dy)
        draw_rounded_rect(ctx, rect, 20)
        ctx.set_line_width(4.0)
        ctx.set_dash([15, 8])
        ctx.stroke()

        size = cell_h // 3
        ctx.set_line_width(8.0)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.set_dash([])
        ctx.move_to(x + cell_w / 2, y + cell_h / 2 - size / 2)
        ctx.line_to(x + cell_w / 2, y + cell_h / 2 + size / 2)
        ctx.stroke()
        ctx.move_to(x + cell_w / 2 - size / 2, y + cell_h / 2)
        ctx.line_to(x + cell_w / 2 + size / 2, y + cell_h / 2)
        ctx.stroke()


APPROXIMATES = [(20, 2), (15, 3), (12, 4), (10, 5), (7, 7),
                (5, 10), (4, 12), (3, 15), (2, 20)]


class ColorCell:
    color = None
    bboxes = None

    def __init__(self, canvas, color):
        self.canvas = canvas
        self.color = color
        self.bboxes = []

    def win2grid(self, point):
        border = config.canvas_border
        return point[0] - border, point[1] - border + self.canvas.dy

    def grid2win(self, point):
        border = config.canvas_border
        return point[0] + border, point[1] + border - self.canvas.dy

    def win2cell(self, point):
        cell_max = self.canvas.cell_max
        index = self.canvas.grid.cells.index(self)
        row = index // cell_max
        column = index - row * cell_max
        origin = (column * config.cell_width, row * config.cell_height)
        grid_point = self.win2grid(point)
        return tuple(i0 - i1 for i0, i1 in zip(grid_point, origin))

    def cell2win(self, point):
        cell_max = self.canvas.cell_max
        index = self.canvas.grid.cells.index(self)
        row = index // cell_max
        column = index - row * cell_max
        origin = (column * config.cell_width, row * config.cell_height)
        return tuple(i0 + i1 for i0, i1 in zip(point, self.grid2win(origin)))

    def is_over(self, point):
        cpoint = self.win2cell(point)
        return any([in_bbox(bbox, cpoint) for bbox in self.bboxes])

    def is_top(self, point):
        return self.win2cell(point)[1] < config.cell_height / 2.4

    def is_middle(self, point):
        return config.cell_height / 2.4 < \
               self.win2cell(point)[1] < config.cell_height / 1.8

    def paint(self, ctx, x_count, y_count):
        cms = self.canvas.cms
        border = config.canvas_border
        cell_h = config.cell_height
        cell_w = config.cell_width

        color = cms.get_display_color(self.color)
        color_name = cms.get_color_name(self.color)

        # Colored rect
        x = border + x_count * cell_w
        y = border + y_count * cell_h
        ctx.set_source_rgb(*color)
        cb = config.cell_border
        rect = (x + cb, y + cb, cell_w - 2 * cb, cell_h - 2 * cb)
        draw_rounded_rect(ctx, rect, config.cell_corner_radius)
        ctx.fill()

        # Border for light color
        if check_brightness(color):
            ctx.set_source_rgb(*config.cell_border_color)
            rect = (x + cb + 1, y + cb + 1,
                    cell_w - 2 * cb - 2,
                    cell_h - 2 * cb - 2)
            draw_rounded_rect(ctx, rect, config.cell_corner_radius)
            ctx.set_line_width(1.0)
            ctx.set_dash([])
            ctx.stroke()

        # Color value label
        ctx.set_font_size(15)
        label = uc2.cms.rgb_to_hexcolor(color)
        ext = ctx.text_extents(label)
        ctx.move_to(x + cell_w / 2 - ext.width / 2,
                    y + cell_h / 2 + ext.height / 2)
        ctx.set_source_rgb(*text_color(color))
        ctx.show_text(label)

        # Color name label
        if color_name != label and color_name.lower() != label.lower():
            max_size = 0.9 * (config.cell_width - 2 * config.cell_border)
            ctx.set_font_size(10)

            ext = ctx.text_extents(color_name)
            color_name2 = []
            while ext.width > max_size:
                words = color_name.split()
                color_name2 = [words[-1]] + color_name2
                color_name = ' '.join(words[:-1])
                ext = ctx.text_extents(color_name)

            ctx.move_to(x + cell_w / 2 - ext.width / 2,
                        y + cell_h / 1.5 + ext.height / 2)
            ctx.show_text(color_name)

            if color_name2:
                color_name2 = ' '.join(color_name2)
                if 'Hexachrome' in color_name2:
                    color_name2 = color_name2.replace('Hexachrome ', 'Hexach.')
                ext2 = ctx.text_extents(color_name2)

                ctx.move_to(x + cell_w / 2 - ext2.width / 2,
                            y + cell_h / 1.5 + ext.height * 1.5 +
                            ext2.height / 2)
                ctx.show_text(color_name2)

        # Selection mark
        if self in self.canvas.selection:
            cx, cy = self.cell2win(config.cell_mark_center)
            cy += self.canvas.dy
            r = config.cell_mark_radius
            ctx.arc(cx, cy, r, 0, 2 * math.pi)
            ctx.set_source_rgb(*config.cell_mark_bg)
            ctx.fill()

            ctx.arc(cx, cy, r, 0, 2 * math.pi)
            ctx.set_source_rgb(*config.cell_mark_border_color)
            ctx.set_line_width(1.0)
            ctx.set_dash([])
            ctx.stroke()

            r = config.cell_mark_internal_radius
            ctx.arc(cx, cy, r, 0, 2 * math.pi)
            ctx.set_source_rgb(*config.cell_mark_fg)
            ctx.fill()


class ColorGrid(CanvasObj):
    cells = None
    tail_bbox = NO_BBOX

    def __init__(self, canvas):
        super().__init__(canvas)
        self.sync_from()

    def sync_from(self):
        self.cells = [ColorCell(self.canvas, color)
                      for color in self.canvas.doc.model.colors]

    def sync_to(self):
        self.canvas.doc.model.colors = [cell.color for cell in self.cells]

    def win2grid(self, point):
        border = config.canvas_border
        return point[0] - border, point[1] - border + self.canvas.dy

    def index_by_point(self, point):
        index = None
        if in_bbox(self.bbox, point):
            x, y = self.win2grid(point)
            column = x // config.cell_width
            row = y // config.cell_height
            index = row * self.canvas.cell_max + column
            index = int(index) if index < len(self.canvas.grid.cells) else None
        return index

    def is_over(self, point, check_cell=True):
        if in_bbox(self.bbox, point) and not in_bbox(self.tail_bbox, point):
            if not check_cell:
                return True
            index = self.index_by_point(point)
            if index is not None:
                return self.cells[index].is_over(point)
        return False

    def make_cell(self, color):
        return ColorCell(self.canvas, color)

    def add_color(self, color):
        self.cells = self.cells + [self.make_cell(color)]
        return self.cells[-1]

    def insert_color(self, color, index):
        cells = [] + self.cells
        cell = self.make_cell(color)
        cells.insert(index, cell)
        self.cells = cells
        return cell

    def on_change_color(self, *_args):
        if self.canvas.is_single_selection():
            self.change_color(self.canvas.selection[0])

    def change_color(self, cell):
        clr0 = [] + cell.color[1]
        clr = wal.color_dialog(self.canvas.mw, _('Change color'), clr0)
        if clr and clr0 != clr:
            color = [uc2const.COLOR_RGB, clr, 1.0, cell.color[3], '']
            api.change_color(self.canvas, cell, color)

    def change_color_hexvalue(self, cell):
        point = cell.cell2win((config.cell_width / 2,
                               config.cell_height / 2))
        popover = wal.EntryPopover(
            self.canvas.dc, point, self.cells.index(cell),
            uc2.cms.rgb_to_hexcolor(cell.color[1]), self.set_color_hexvalue)
        popover.set_pos(top=True)
        popover.run()

    def change_color_name(self, cell):
        point = cell.cell2win((config.cell_width / 2,
                               config.cell_height * 4 / 5))
        popover = wal.EntryPopover(
            self.canvas.dc, point, self.cells.index(cell),
            cell.color[3], self.set_color_name)
        popover.set_pos(bottom=True)
        popover.run()

    def set_color_name(self, index, name):
        cell = self.cells[index]
        color = deepcopy(self.cells[index].color)
        color[3] = name
        api.change_color(self.canvas, cell, color)

    def set_color_hexvalue(self, index, hexvalue):
        try:
            clr = uc2.cms.hexcolor_to_rgb(hexvalue)
        except Exception:
            wal.error_dialog(self.canvas.mw, _('Wrong value'),
                             _('Wrong color value: ') + hexvalue,
                             _('Fix it and try again'))
            return
        cell = self.cells[index]
        color = deepcopy(self.cells[index].color)
        color[1] = clr
        api.change_color(self.canvas, cell, color)

    @staticmethod
    def get_approximates():
        coef = config.cell_corner_radius / 18
        border = config.cell_border
        w = config.cell_width
        h = config.cell_height
        apoints = [(x * coef + border, y * coef + border)
                   for x, y in APPROXIMATES]
        return [(x, y, w - x, h - y) for x, y in apoints]

    def on_left_released(self, event):
        point = event.get_point()
        index = self.index_by_point(point)
        if index is not None:
            if event.is_shift() or event.is_ctrl():
                if self.cells[index] in self.canvas.selection:
                    self.canvas.selection.remove(self.cells[index])
                else:
                    self.canvas.selection.append(self.cells[index])
            else:
                self.canvas.selection = [self.cells[index]]
            self.canvas.reflect_transaction()

    def on_left_double_click(self, event):
        index = self.index_by_point(event.get_point())
        self.canvas.selection = [self.cells[index]]
        self.canvas.reflect_transaction()
        if self.cells[index].is_top(event.get_point()):
            self.change_color(self.cells[index])
        elif self.cells[index].is_middle(event.get_point()):
            self.change_color_hexvalue(self.cells[index])
        else:
            self.change_color_name(self.cells[index])

    def on_right_pressed(self, event):
        return self.is_over(event.get_point(), False) and self.active

    def on_right_released(self, event):
        index = self.index_by_point(event.get_point())
        cell = self.cells[index]
        if cell not in self.canvas.selection:
            self.canvas.selection = [cell]
        self.canvas.dc.show_ctx_menu(event.get_point(), self.canvas.ctx_menu)

    def paint(self, ctx):
        cell_max = self.canvas.cell_max
        x_count = y_count = 0

        bboxes = self.get_approximates()

        for cell in self.cells:
            cell.paint(ctx, x_count, y_count)
            cell.bboxes = bboxes

            x_count += 1
            if x_count == cell_max:
                x_count = 0
                y_count += 1

        self.bbox = self.tail_bbox = NO_BBOX
        if self.cells:
            border = config.canvas_border
            cell_h = config.cell_height
            cell_w = config.cell_width
            cell_num = len(self.cells)

            if len(self.cells) > cell_max:
                w = cell_max * cell_w
                h = math.ceil(cell_num / cell_max) * cell_h
            else:
                h = cell_h
                w = cell_num * cell_w
            self.bbox = (border, border - self.canvas.dy,
                         border + w, border + h - self.canvas.dy)

            if cell_num / cell_max > cell_num // cell_max:
                last_row = cell_num - round((cell_num // cell_max) * cell_max)
                self.tail_bbox = (border + last_row * cell_w,
                                  border + h - cell_h - self.canvas.dy,
                                  border + w, border + h - self.canvas.dy)


class BackgroundObj(CanvasObj):
    def on_left_released(self, _event):
        self.canvas.selection = []
        self.canvas.reflect_transaction()

    def on_right_released(self, _event):
        self.canvas.dc.show_ctx_menu(_event.get_point(), self.canvas.ctx_menu)

    def paint(self, ctx):
        self.bbox = (0, 0, self.canvas.width, self.canvas.height)
        ctx.set_source_rgb(*config.canvas_bg)
        ctx.paint()


class Canvas(Decomposable):
    app = None
    mw = None
    dc = None
    doc = None
    history = None
    cms = None
    surface = None
    ctx = None
    selection = None

    dy = 0
    max_dy = 0
    width = 0
    height = 0
    virtual_h = 0
    cell_max = 5
    z_order = None

    left_pressed = None
    right_pressed = None
    press_timestamp = 0
    release_timestamp = 0

    def __init__(self, mw, doc):
        self.mw = mw
        self.doc = doc
        self.app = mw.app
        self.dc = mw.dc
        self.cms = self.app.default_cms
        self.history = UndoHistory(self)
        self.selection = []

        self.grid = ColorGrid(self)
        self.scroll = ScrollObj(self)

        self.z_order = [
            LogoObj(self),
            self.scroll,
            AddButtonObj(self),
            self.grid,
            BackgroundObj(self),
        ]
        self.reflect_transaction()
        self.ctx_menu = [
            [
                (_('Cut'), 'cut', self.mw.cut_selected, self.is_selection),
                (_('Copy'), 'copy', self.mw.copy_selected, self.is_selection),
                (_('Paste'), 'paste', self.mw.paste, self.mw.is_clipboard),
            ],
            [
                (_('Change color'), 'change-color',
                 self.grid.on_change_color, self.is_single_selection),
            ],
            [
                (_('Delete'), 'delete',
                 self.mw.delete_selected, self.is_selection),
                (_('Duplicate'), 'duplicate',
                 self.mw.duplicate, self.is_selection),
            ],
            [
                (_('Select all'), 'select-all',
                 self.mw.select_all, self.is_not_selected),
                (_('Deselect'), 'deselect',
                 self.mw.deselect, self.is_selection),
            ],
            [
                (_('Paste from file...'), 'paste-from',
                 self.mw.on_paste_from, None),
            ],
        ]

    def destroy(self):
        if self.doc:
            self.doc.close()
        Decomposable.destroy(self)

    def reflect_transaction(self):
        mark = '' if self.history.is_saved() else ' [*]'
        self.mw.set_title(self.app.appdata.app_name + mark)

        subtitle = self.doc.model.name or _('Untitled palette')
        if not self.doc.model.name:
            self.doc.model.name = subtitle
        colornum = len(self.grid.cells)
        txt = _('colors')
        self.mw.set_subtitle('%s (%s %s)' % (subtitle, colornum, txt))
        self.dc.refresh()

    def is_selection(self):
        return bool(self.selection)

    def is_single_selection(self):
        return len(self.selection) == 1

    def is_not_selected(self):
        return self.is_colors() and \
               len(self.selection) != len(self.doc.model.colors)

    def is_colors(self):
        return bool(self.doc.model.colors)

    def set_cursor(self, cursor_name):
        self.dc.set_cursor(cursor_name)

    def go_home(self, *_args):
        self.dy = 0
        self.dc.refresh()

    def go_end(self, *_args):
        self.dy = self.max_dy
        self.dc.refresh()

    def page_up(self, *_args):
        self.dy = max(0, self.dy - self.height)
        self.dc.refresh()

    def page_down(self, *_args):
        self.dy = min(self.max_dy, self.height + self.dy)
        self.dc.refresh()

    def scroll_up(self, *_args):
        self.dy = max(0, self.dy - config.cell_height // 2)
        self.dc.refresh()

    def scroll_down(self, *_args):
        self.dy = min(self.max_dy, config.cell_height // 2 + self.dy)
        self.dc.refresh()

    def _is_locked(self):
        return bool(self.left_pressed) or bool(self.right_pressed)

    def on_scroll(self, event):
        self.dy += event.get_scroll() * config.mouse_scroll_sensitivity
        if self.dy < 0 or self.virtual_h <= self.height:
            self.dy = 0
        elif self.virtual_h > self.height and \
                self.dy > self.virtual_h - self.height:
            self.dy = self.virtual_h - self.height
        self.dc.refresh()

    def on_move(self, event):
        if self.left_pressed:
            self.left_pressed.on_move(event)
            return
        for obj in self.z_order:
            if obj.on_move(event):
                break

    def on_leave(self, _event):
        if self.scroll.hover and not self.scroll == self.left_pressed:
            self.scroll.hover = False
            self.dc.refresh()

    def on_left_pressed(self, event):
        for obj in self.z_order:
            self.left_pressed = None
            if obj.on_left_pressed(event):
                self.left_pressed = obj
                self.press_timestamp = time.time()
                break

    def on_left_released(self, event):
        if self.left_pressed:
            self.left_pressed.on_left_released(event)
            timestamp = time.time()
            if timestamp - self.release_timestamp < 0.5 or \
                    timestamp - self.press_timestamp > 0.5:
                self.left_pressed.on_left_double_click(event)
            self.release_timestamp = timestamp
            self.left_pressed = None

    def on_right_pressed(self, event):
        for obj in self.z_order:
            self.right_pressed = None
            if obj.on_right_pressed(event):
                self.right_pressed = obj
                break

    def on_right_released(self, event):
        if self.right_pressed:
            self.right_pressed.on_right_released(event)
            self.right_pressed = None

    def on_btn1_move(self, event):
        pass

    def paint(self, widget_ctx):
        w, h = self.dc.get_size()
        border = config.canvas_border
        cell_h = config.cell_height
        cell_num = len(self.doc.model.colors) + 1
        self.cell_max = (w - 2 * config.canvas_border) // config.cell_width
        self.virtual_h = \
            2 * border + math.ceil(cell_num / self.cell_max) * cell_h
        max_dy = round(self.virtual_h - h)
        self.max_dy = max_dy if max_dy > 0 else 0
        self.dy = min(self.dy, self.max_dy)

        if self.surface is None or self.width != w or self.height != h:
            self.surface = cairo.ImageSurface(cairo.FORMAT_RGB24, w, h)
            self.width, self.height = w, h
        self.ctx = cairo.Context(self.surface)

        self.ctx.set_matrix(cairo.Matrix(1.0, 0.0, 0.0, 1.0, 0.0, -self.dy))

        for obj in reversed(self.z_order):
            obj.paint(self.ctx)

        widget_ctx.set_source_surface(self.surface)
        widget_ctx.paint()
