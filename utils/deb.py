# -*- coding: utf-8 -*-
#
#   DEB builder
#
# 	Copyright (C) 2018-2019 by Igor E. Novikov
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
import platform
import sys
import logging

LOG = logging.getLogger(__name__)

RM_CODE = 21
MK_CODE = 22
CP_CODE = 23

logging.addLevelName(RM_CODE, 'REMOVING')
logging.addLevelName(MK_CODE, 'CREATING')
logging.addLevelName(CP_CODE, 'COPYING')


def get_size(start_path='.'):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size


def _make_dir(path):
    if not os.path.lexists(path):
        LOG.log(MK_CODE, '%s directory.', path)
        try:
            os.makedirs(path)
        except:
            raise IOError('Error while creating %s directory.' % path)


def copy_scripts(folder, scripts):
    if not scripts:
        return
    _make_dir(folder)
    for item in scripts:
        LOG.log(CP_CODE, '%s -> %s', item, folder)
        if os.system('cp %s %s' % (item, folder)):
            raise IOError('Cannot copying %s -> %s' % (item, folder))
        filename = os.path.basename(item)
        path = os.path.join(folder, filename)
        if os.path.isfile(path):
            LOG.log(MK_CODE, '%s as executable', path)
            if os.system('chmod +x %s' % path):
                raise IOError('Cannot set executable flag for %s' % path)


def copy_files(path, files):
    if files and not os.path.isdir(path):
        _make_dir(path)
    if not files:
        return
    for item in files:
        msg = '%s -> %s' % (item, path)
        if len(msg) > 80:
            msg = '%s -> \n%s%s' % (item, ' ' * 10, path)
        LOG.log(CP_CODE, msg)
        if os.system('cp %s %s' % (item, path)):
            raise IOError('Cannot copying %s -> %s' % (item, path))


class DebBuilder:
    """
    Represents deb package build object.
    The object implements "setup.py bdist_deb" command.
    Works after regular "setup.py build" command and
    constructs deb package using build result in build/ directory.
    Arguments:

    name - package names
    version - package version
    arch - system architecture (amd64, i386, all), if not provided will be
            detected automatically
    maintainer - package maintainer (John Smith <js@email.x>)
    depends - comma separated string of dependencies
    section - package section (default 'python')
    priority - package priority for users (default 'optional')
    homepage - project homepage
    description - short package description
    long_description - long description as defined by Debian rules
    package_dirs - list of root python packages
    scripts - list of executable scripts
    data_files - list of data files and appropriate destination directories.
    deb_scripts - list of Debian package scripts.
    """

    name = None
    package_dirs = {}
    package_data = {}
    scripts = []
    data_files = []
    deb_scripts = []

    package = ''
    version = None
    arch = ''
    maintainer = ''
    installed_size = 0
    depends = ''
    section = 'python'
    priority = 'optional'
    homepage = ''
    description = ''
    long_description = ''

    package_name = ''
    py_version = ''
    machine = ''
    build_dir = 'build/deb-root'
    deb_dir = 'build/deb-root/DEBIAN'
    src = ''
    dst = ''
    bin_dir = ''
    pixmaps_dir = ''
    apps_dir = ''

    def __init__(
            self,
            name='',
            version='',
            arch='',
            maintainer='',
            depends='',
            section='',
            priority='',
            homepage='',
            description='',
            long_description='',
            package_dirs=None,
            package_data=None,
            scripts=None,
            data_files=None,
            deb_scripts=None,
            dst=''):

        deb_scripts = deb_scripts or []
        data_files = data_files or []
        scripts = scripts or []
        package_dirs = package_dirs or []
        package_data = package_data or {}

        self.name = name
        self.version = version
        self.arch = arch
        self.maintainer = maintainer
        self.depends = depends
        if section:
            self.section = section
        if priority:
            self.priority = priority
        self.homepage = homepage
        self.description = description
        self.long_description = long_description

        self.package_dirs = package_dirs
        self.package_data = package_data
        self.scripts = scripts
        self.data_files = data_files
        self.deb_scripts = deb_scripts
        if dst:
            self.dst = dst

        self.package = 'python3-' + self.name
        self.py_version = '.'.join(sys.version.split()[0].split('.')[:2])

        if not self.arch:
            arch = platform.architecture()[0]
            self.arch = 'amd64' if arch == '64bit' else 'i386'

        self.machine = platform.machine()

        self.src = 'build/lib.linux-%s-%s' % (self.machine, self.py_version)

        if not self.dst:
            path = '%s/usr/lib/python%s/dist-packages'
            self.dst = path % (self.build_dir, self.py_version)
        else:
            self.dst = self.build_dir + self.dst
        self.bin_dir = '%s/usr/bin' % self.build_dir

        self.package_name = 'python3-%s-%s_%s.deb' % (
            self.name, self.version, self.arch)
        self.build()

    def clear_build(self):
        if os.path.lexists(self.build_dir):
            LOG.log(RM_CODE, '%s directory.', self.build_dir)
            if os.system('rm -rf ' + self.build_dir):
                raise IOError(
                    'Error while removing %s directory.' % self.build_dir)
        if os.path.lexists('dist'):
            LOG.log(RM_CODE, 'Cleaning dist/ directory.')
            if os.system('rm -rf dist/*.deb'):
                raise IOError('Error while cleaning dist/ directory.')
        else:
            _make_dir('dist')

    def write_control(self):
        _make_dir(self.deb_dir)
        control_list = [
            ['Package', self.package],
            ['Version', self.version],
            ['Architecture', self.arch],
            ['Maintainer', self.maintainer],
            ['Installed-Size', self.installed_size],
            ['Depends', self.depends],
            ['Section', self.section],
            ['Priority', self.priority],
            ['Homepage', self.homepage],
            ['Description', self.description],
            ['', self.long_description],
        ]
        path = os.path.join(self.deb_dir, 'control')
        LOG.log(MK_CODE, 'Writing Debian control file.')
        try:
            control = open(path, 'w')
            for item in control_list:
                name, val = item
                if val:
                    if name:
                        control.write('%s: %s\n' % (name, val))
                    else:
                        control.write('%s\n' % val)
            control.close()
        except:
            raise IOError('Error while writing Debian control file.')

    def copy_build(self):
        for item in os.listdir(self.src):
            path = os.path.join(self.src, item)
            if os.path.isdir(path):
                LOG.log(CP_CODE, '%s -> %s', path, self.dst)
                if os.system('cp -R %s %s' % (path, self.dst)):
                    raise IOError(
                        'Error while copying %s -> %s' % (path, self.dst))
            elif os.path.isfile(path):
                LOG.log(CP_CODE, '%s -> %s', path, self.dst)
                if os.system('cp %s %s' % (path, self.dst)):
                    raise IOError(
                        'Error while copying %s -> %s' % (path, self.dst))

    def copy_data_files(self):
        for item in self.data_files:
            path, files = item
            copy_files(self.build_dir + path, files)

    def copy_package_data_files(self):
        files = []
        pkgs = self.package_data.keys()
        for pkg in pkgs:
            items = self.package_data[pkg]
            for item in items:
                path = os.path.join(self.package_dirs[pkg], item)
                if os.path.basename(path) == '*.*':
                    flist = []
                    folder = os.path.join(self.dst, os.path.dirname(item))
                    fldir = os.path.dirname(path)
                    fls = os.listdir(fldir)
                    for fl in fls:
                        flpath = os.path.join(fldir, fl)
                        if os.path.isfile(flpath):
                            flist.append(flpath)
                    files.append([folder, flist])
                else:
                    if os.path.isfile(path):
                        folder = os.path.join(self.dst, os.path.dirname(item))
                        files.append([folder, [path, ]])
        for item in files:
            path, files = item
            copy_files(path, files)

    def make_package(self):
        os.system('chmod -R 755 %s' % self.build_dir)
        LOG.log(MK_CODE, '%s package.', self.package_name)
        if os.system('sudo dpkg --build %s/ dist/%s' % (
                self.build_dir, self.package_name)):
            raise IOError('Cannot create package %s' % self.package_name)

    def build(self):
        line = '=' * 30
        LOG.info(line)
        LOG.info('DEB PACKAGE BUILD')
        LOG.info(line)
        try:
            if not os.path.isdir('build'):
                raise IOError('There is no project build! '
                              'Run "setup.py build" and try again.')
            self.clear_build()
            _make_dir(self.dst)
            self.copy_build()
            copy_scripts(self.bin_dir, self.scripts)
            copy_scripts(self.deb_dir, self.deb_scripts)
            self.copy_data_files()
            self.installed_size = str(int(get_size(self.build_dir) / 1024))
            self.write_control()
            self.make_package()
        except IOError as e:
            LOG.error(e)
            LOG.warning(line)
            LOG.warning('BUILD FAILED!')
            return 1
        LOG.info(line)
        LOG.info('BUILD SUCCESSFUL!')
        LOG.info(line)
        return 0
