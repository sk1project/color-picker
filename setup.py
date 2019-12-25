#!/usr/bin/python3
#
#   Setup script for Color Picker 1.x
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

"""
Usage:
--------------------------------------------------------------------------
 to build package:       python setup.py build
 to install package:     python setup.py install
 to remove installation: python setup.py uninstall
--------------------------------------------------------------------------
 to create source distribution:   python setup.py sdist
--------------------------------------------------------------------------
 to create binary RPM distribution:  python setup.py bdist_rpm
--------------------------------------------------------------------------
 to create binary DEB distribution:  python setup.py bdist_deb
--------------------------------------------------------------------------.
 Help on available distribution formats: --help-formats
"""
from distutils.core import setup
import datetime
import os
import sys
import string
import logging

############################################################

import utils.deb
import utils.rpm
from utils import build
from utils import fsutils
from utils import po

from utils import dependencies
from utils import native_mods


logging.basicConfig(level=0, format='%(levelname)-8s %(message)s')
log = logging.getLogger('setup')

sys.path.insert(1, os.path.abspath('./src'))

CURRENT_PATH = os.path.dirname(os.path.abspath(__file__))

from cp2 import appconst

############################################################
# Flags
############################################################
UPDATE_MODULES = False
DEB_PACKAGE = False
RPM_PACKAGE = False
CLEAR_BUILD = False

############################################################
# Package description
############################################################
NAME = appconst.APPNAME
VERSION = appconst.VERSION + appconst.REVISION
DESCRIPTION = 'Palette editor'
AUTHOR = 'Igor E. Novikov'
AUTHOR_EMAIL = 'sk1.project.org@gmail.com'
MAINTAINER = AUTHOR
MAINTAINER_EMAIL = AUTHOR_EMAIL
LICENSE = 'GPL v3'
URL = 'https://sk1project.net'
DOWNLOAD_URL = URL
CLASSIFIERS = [
    'Development Status :: 5 - Stable',
    'Environment :: Desktop',
    'Intended Audience :: End Users/Desktop',
    'License :: OSI Approved :: GPL v3',
    'Operating System :: POSIX',
    'Operating System :: MacOS :: MacOS X',
    'Operating System :: Microsoft :: Windows',
    'Programming Language :: Python',
    'Programming Language :: C',
    "Topic :: Multimedia :: Graphics :: Editors :: Vector-Based",
]
LONG_DESCRIPTION = '''
Advanced cross-platform Color Picker application powered by magnify glass 
and palette editing functionality.
sK1 Project (https://sk1project.net),
Copyright (C) 2018-%s sK1 Project Team
''' % str(datetime.date.today().year)

LONG_DEB_DESCRIPTION = ''' .
 Advanced cross-platform Color Picker application powered by magnify glass 
 and palette editing functionality.
 . 
 sK1 Project (https://sk1project.net),
 Copyright (C) 2018-%s sK1 Project Team
 .
''' % str(datetime.date.today().year)

############################################################
# Build data
############################################################
install_path = '/usr/lib/%s-%s' % (NAME, VERSION)
os.environ["APP_INSTALL_PATH"] = "%s" % (install_path,)
src_path = 'src'
include_path = '/usr/include'
modules = []
scripts = ['src/_script/color-picker', ]
deb_scripts = []
data_files = [
    ('/usr/share/applications', ['src/color-picker.desktop', ]),
    ('/usr/share/pixmaps', ['src/color-picker.png', 'src/color-picker.xpm', ]),
    ('/usr/share/icons/hicolor/scalable/apps', ['src/color-picker.svg', ]),
    (install_path, ['LICENSE', ]),
]

LOCALES_PATH = 'src/cp2/share/locales'

EXCLUDES = []

############################################################
deb_depends = ''
rpm_depends = ''
############################################################

dirs = fsutils.get_dirs_tree('src/cp2/share')
share_dirs = []
for item in dirs:
    share_dirs.append(os.path.join(item[8:], '*.*'))

package_data = {
    'cp2': share_dirs,
}


def build_locales():
    src_path = 'po-cp2'
    dest_path = LOCALES_PATH
    po.build_locales(src_path, dest_path, 'cp2')


############################################################
# Main build procedure
############################################################

if len(sys.argv) == 1:
    print('Please specify build options!')
    print(__doc__)
    sys.exit(0)

if len(sys.argv) > 1:

    if sys.argv[1] == 'bdist_rpm':
        CLEAR_BUILD = True
        RPM_PACKAGE = True
        sys.argv[1] = 'sdist'
        rpm_depends = dependencies.get_cp2_rpm_depend()

    elif sys.argv[1] == 'bdist_deb':
        DEB_PACKAGE = True
        CLEAR_BUILD = True
        sys.argv[1] = 'build'
        deb_depends = dependencies.get_cp2_deb_depend()

    elif sys.argv[1] == 'uninstall':
        if os.path.isdir(install_path):
            # removing cp2 folder
            log.info('REMOVE: %s', install_path)
            os.system('rm -rf ' + install_path)
            # removing scripts
            for item in scripts:
                filename = os.path.basename(item)
                log.info('REMOVE: /usr/bin/%s', filename)
                os.system('rm -rf /usr/bin/' + filename)
            # removing data files
            for item in data_files:
                location = item[0]
                file_list = item[1]
                for file_item in file_list:
                    filename = os.path.basename(file_item)
                    filepath = os.path.join(location, filename)
                    if not os.path.isfile(filepath):
                        continue
                    log.info('REMOVE: %s', filepath)
                    os.system('rm -rf ' + filepath)
            if os.system('update-desktop-database'):
                log.info('Desktop database update: DONE')
            else:
                log.error('Desktop database update: ERROR')
        else:
            log.warning('Color Picker installation is not found!')
        sys.exit(0)

    elif sys.argv[1] == 'update_pot':
        paths = ['src/cp2', 'src/uc2']
        po.build_pot(paths, 'po-cp2/cp2.pot', False)
        sys.exit(0)

    elif sys.argv[1] == 'build_locales':
        build_locales()
        sys.exit(0)

# Preparing start script
src_script = 'src/_script/color-picker.tmpl'
dst_script = 'src/_script/color-picker'

with open(src_script, 'r') as fileptr:
    tmpl = string.Template(fileptr.read())
    console_scripts = tmpl.safe_substitute(APP_INSTALL_PATH=install_path)

with open(dst_script, 'w') as fileptr:
    fileptr.write(console_scripts)

# Preparing setup.cfg
############################################################

with open('setup.cfg.in', 'r') as fileptr:
    content = fileptr.read()
    if rpm_depends:
        content += '\nrequires = ' + rpm_depends

with open('setup.cfg', 'w') as fileptr:
    fileptr.write(content)

# Preparing locales
############################################################
if not os.path.exists(LOCALES_PATH):
    build_locales()

############################################################
# Native extensions
############################################################

modules += native_mods.make_cp2_modules(src_path, include_path)

############################################################
# Setup routine
############################################################

setup(
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    maintainer=MAINTAINER,
    maintainer_email=MAINTAINER_EMAIL,
    license=LICENSE,
    url=URL,
    download_url=DOWNLOAD_URL,
    long_description=LONG_DESCRIPTION,
    classifiers=CLASSIFIERS,
    packages=build.get_source_structure(excludes=EXCLUDES),
    package_dir=build.get_package_dirs(excludes=EXCLUDES),
    package_data=package_data,
    data_files=data_files,
    scripts=scripts,
    ext_modules=modules,)

############################################################
# .py source compiling
############################################################
if not UPDATE_MODULES:
    build.compile_sources()

############################################################
# This section for developing purpose only
# Command 'python setup.py build_update' allows
# automating build and copying of native extensions
# into package directory
############################################################
if UPDATE_MODULES:
    build.copy_modules(modules)

############################################################
# Implementation of bdist_deb command
############################################################
if DEB_PACKAGE:
    utils.deb.DebBuilder(
        name=NAME,
        version=VERSION,
        maintainer='%s <%s>' % (AUTHOR, AUTHOR_EMAIL),
        depends=deb_depends,
        homepage=URL,
        description=DESCRIPTION,
        long_description=LONG_DEB_DESCRIPTION,
        section='graphics',
        package_dirs=build.get_package_dirs(excludes=EXCLUDES),
        package_data=package_data,
        scripts=scripts,
        data_files=data_files,
        deb_scripts=deb_scripts,
        dst=install_path)

############################################################
# Implementation of bdist_rpm command
############################################################
if RPM_PACKAGE:
    utils.rpm.RpmBuilder(
        name=NAME,
        version=VERSION,
        release='0',
        arch='',
        maintainer='%s <%s>' % (AUTHOR, AUTHOR_EMAIL),
        summary=DESCRIPTION,
        description=LONG_DESCRIPTION,
        license_=LICENSE,
        url=URL,
        depends=rpm_depends.split(' '),
        build_script='setup.py',
        install_path=install_path,
        data_files=data_files, )


os.chdir(CURRENT_PATH)

if CLEAR_BUILD:
    build.clear_build()

FOR_CLEAR = ['MANIFEST', 'src/_script/color-picker', 'setup.cfg']
for item in FOR_CLEAR:
    if os.path.lexists(item):
        os.remove(item)
