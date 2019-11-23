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

INDENT = 4
WRAP = 3


class XmlElement(object):
    parent = None
    childs = None
    tag = None
    attrs = None
    comment = None
    content = None
    nl = False

    def __init__(self, tag, kwargs=None, content=None):
        self.tag = tag
        self.childs = []
        self.content = content
        self.attrs = {key: value
                      for key, value in kwargs.items()} if kwargs else {}

    def destroy(self):
        for child in self.childs:
            child.destroy()
        for item in self.__dict__.keys():
            self.__dict__[item] = None

    def add(self, child):
        if child:
            self.childs.append(child)
            child.parent = self

    def set(self, kwargs):
        self.attrs.update(kwargs)

    def get(self, key):
        return self.attrs.get(key)

    def pop(self, key):
        if key in self.attrs:
            self.attrs.pop(key)

    def write_xml(self, fp, indent=0):
        if self.nl:
            fp.write('\n')
        tab = indent * ' '
        if self.comment:
            fp.write('%s<!-- %s -->\n' % (tab, self.comment))
        fp.write('%s<%s' % (tab, self.tag))
        prefix = '\n%s  ' % tab if len(self.attrs) > WRAP else ' '
        for key, value in self.attrs.items():
            fp.write('%s%s="%s"' % (prefix, key, value))
        if self.childs:
            fp.write('>\n')
            for child in self.childs:
                child.write_xml(fp, indent + INDENT)
            fp.write('%s</%s>\n' % (tab, self.tag))
        elif self.content:
            fp.write('>')
            fp.write(self.content)
            fp.write('</%s>\n' % self.tag)
        else:
            fp.write(' />\n')
