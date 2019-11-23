# -*- coding: utf-8 -*-
#
#   macOS pkg build
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

#   Requires xar and bomutils:
# sudo apt-get install libxml2-dev libssl-dev
# tar -zxvf ./bomutils-0.2.tar.gz && cd bomutils-0.2&& make && make install
# tar -zxvf ./xar-1.5.2.tar.gz && cd ./xar-1.5.2 && \
# ./configure && make && make install

import os
import shutil
import sys

from . import fsutils
from .bbox import echo_msg
from .dmg import dmg_build
from .xmlutils import XmlElement

# KW_SAMPLE = {
#     'src_dir': '',  # path to distribution folder
#     'build_dir': './build_dir',  # path for build
#     'install_dir': '/opt/appName',  # where to install app
#     'identifier': 'com.ProFarms.SimCow',  # domain.Publisher.AppName
#     'app_name': 'Some App 1.3.0', # pretty app name
#     'app_ver': '1.3.0', # pretty app version
#     'pkg_name': 'app_1.3.0.pkg', # pretty package name
#     ------- OPTIONAL --------
#     'remove_build': False,
#     'preinstall': None, # path to preinstall script
#     'postinstall': None, # path to postinstall script
#     'check_version': '10.11', # check macOS version
#     'background': '', # path to background image
#     'readme': 'readme.rtf', # path to readme file
#     'welcome': 'welcome.rtf', # path to welcome file
#     'license': 'license.rtf', # path to license file
#     'dmg': {
#              'targets': [], # list of paths to target files
#              'dmg_filename': 'app_1.3.0.dmg',
#              'volume_name: 'App 1.3.0',
#              'dist_dir': '.',
#            }
# }

MAC_VER = {
    '10.5': 'Mac OS X 10.5 Leopard',
    '10.6': 'Mac OS X 10.6 Snow Leopard',
    '10.7': 'Mac OS X 10.7 Lion',
    '10.8': 'OS X 10.8 Mountain Lion',
    '10.9': 'OS X 10.9 Mavericks',
    '10.10': 'OS X 10.10 Yosemite',
    '10.11': 'OS X 10.11 El Capitan',
    '10.12': 'macOS 10.12 Sierra',
    '10.13': 'macOS 10.13 High Sierra',
    '10.14': 'macOS 10.14 Mojave',
    '10.15': 'macOS 10.15 Catalina',
}

CHECK_SCRIPT = """function install_check() {
  if(!(system.compareVersions(system.version.ProductVersion,%s) >= 0)) {
    my.result.title = 'Failure';
    my.result.message = 'You need at least %s to install %s.';
    my.result.type = 'Fatal';
    return false;
  }
  return true;
}
"""


class PkgBuilder:
    def __init__(self, kwargs):
        self.kwargs = kwargs
        self.payload_sz = (0, 0)
        self.build_dir = fsutils.normalize_path(self.kwargs['build_dir'])
        self.flat_dir = os.path.join(self.build_dir, 'flat')
        self.scripts_dir = os.path.join(self.build_dir, 'scripts')
        self.proj_dir = os.path.join(self.flat_dir, 'Resources', 'en.lproj')
        self.pkg_dir = os.path.join(self.flat_dir, 'base.pkg')
        self.root_dir = os.path.join(self.build_dir, 'root')
        self.clear_build()

        for item in (self.proj_dir, self.pkg_dir):
            os.makedirs(item)
        self.create_payload()
        self.create_pkg_info()
        self.create_bom()
        self.create_distribution()
        self.make_pkg()
        self.make_dmg()
        if self.kwargs.get('remove_build', False):
            self.clear_build()

    def clear_build(self):
        if os.path.exists(self.build_dir):
            os.system('rm -rf %s' % self.build_dir)

    def create_payload(self):
        echo_msg('Creating payload...  ', False)
        src = fsutils.normalize_path(self.kwargs['src_dir'])
        shutil.copytree(src, self.root_dir)
        if os.system('( cd %s && find . | '
                     'cpio -o --format odc --owner 0:80 | '
                     'gzip -c ) > %s/Payload' % (self.root_dir, self.pkg_dir)):
            echo_msg('Error in payload')
            sys.exit(1)
        self.payload_sz = fsutils.getsize(self.root_dir, True)
        echo_msg('Payload created!')

    def add_scripts(self):
        echo_msg('Adding scripts...', False)
        scripts = None
        os.makedirs(self.scripts_dir)
        if 'preinstall' in self.kwargs:
            scripts = XmlElement('scripts')

            scr = self.kwargs['preinstall']
            name = os.path.basename(scr)
            path = os.path.join(self.scripts_dir, name)
            shutil.copy(fsutils.normalize_path(scr), path)
            os.system('chmod +x %s' % path)
            scripts.add(XmlElement('preinstall', {'file': './%s' % name}))

        if 'postinstall' in self.kwargs:
            scripts = XmlElement('scripts') if not scripts else scripts

            scr = self.kwargs['postinstall']
            name = os.path.basename(scr)
            path = os.path.join(self.scripts_dir, name)
            shutil.copy(fsutils.normalize_path(scr), path)
            os.system('chmod +x %s' % path)
            scripts.add(XmlElement('postinstall', {'file': './%s' % name}))

        if scripts:
            os.system('( cd %s && find . | '
                      'cpio -o --format odc --owner 0:80 | gzip -c ) > '
                      '%s/Scripts' % (self.scripts_dir, self.pkg_dir))

        os.system('rm -rf %s' % self.scripts_dir)
        echo_msg('   OK')
        return scripts

    def create_pkg_info(self):
        echo_msg('Creating package info...')
        pkg_info = XmlElement('pkg-info', {
            'format-version': '2',
            'identifier': '%s.base.pkg' % self.kwargs['identifier'],
            'version': self.kwargs['app_ver'],
            'auth': 'root',
            'overwrite-permissions': 'true',
            'relocatable': 'false',
        })
        pkg_info.add(XmlElement('payload', {
            'installKBytes': '%d' % (self.payload_sz[0] // 1024),
            'numberOfFiles': '%d' % self.payload_sz[1],
        }))
        pkg_info.add(self.add_scripts())
        pkg_info.add(XmlElement('bundle-version'))

        pkg_info_file = os.path.join(self.pkg_dir, 'PackageInfo')
        with open(pkg_info_file, 'w') as fileptr:
            fileptr.write(
                '<?xml version="1.0" encoding="utf-8" standalone="no"?>\n')
            pkg_info.write_xml(fileptr)
        echo_msg('Package info created.')

    def create_bom(self):
        echo_msg('Creating Bom...', False)
        os.system('mkbom -u 0 -g 80 %s %s/Bom' % (self.root_dir, self.pkg_dir))
        os.system('rm -rf %s' % self.root_dir)
        echo_msg('   OK')

    def add_rescource(self, tag_name):
        ret = None
        if tag_name in self.kwargs:
            path = fsutils.normalize_path(self.kwargs[tag_name])
            name = os.path.basename(path)
            dest = os.path.join(self.proj_dir, name)
            shutil.copy(path, dest)
            ret = XmlElement(tag_name, {'file': name})
            if tag_name == 'background':
                ret.set({'alignment': 'bottomleft', 'scaling': 'none'})
        return ret

    def create_distribution(self):
        echo_msg('Creating Distribution...', False)
        distr = XmlElement('installer-script', {
            'minSpecVersion': '1.000000',
            'authoringTool': 'com.apple.PackageMaker',
            'authoringToolVersion': '3.0.3',
            'authoringToolBuild': '174',
        })
        distr.add(XmlElement('title', content=self.kwargs['app_name']))
        distr.add(XmlElement('options', {
            'customize': 'never',
            'allow-external-scripts': 'no',
        }))
        distr.add(XmlElement('domains', {'enable_anywhere': 'true'}))

        if 'check_version' in self.kwargs:
            distr.add(XmlElement('installation-check', {
                'script': 'install_check();'}))
            ver = self.kwargs['check_version']
            ver = '10.10' if ver not in MAC_VER else ver
            os_name = MAC_VER[ver]
            content = CHECK_SCRIPT % (ver, os_name, self.kwargs['app_name'])
            distr.add(XmlElement('script', content=content))

        for item in ('background', 'welcome', 'readme', 'license'):
            distr.add(self.add_rescource(item))

        choices_outline = XmlElement('choices-outline')
        choices_outline.add(XmlElement('line', {'choice': 'choice1'}))
        distr.add(choices_outline)

        choice = XmlElement('choice', {'id': 'choice1', 'title': 'base'})
        choice.add(XmlElement(
            'pkg-ref', {'id': '%s.base.pkg' % self.kwargs['identifier']}))
        distr.add(choice)

        distr.add(XmlElement('pkg-ref', {
            'id': '%s.base.pkg' % self.kwargs['identifier'],
            'installKBytes': '%d' % (self.payload_sz[0] // 1024),
            'version': self.kwargs['app_ver'],
            'auth': 'Root',
        }, content='#base.pkg'))

        distr_file = os.path.join(self.flat_dir, 'Distribution')
        with open(distr_file, 'w') as fileptr:
            fileptr.write(
                '<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n')
            distr.write_xml(fileptr)
        echo_msg('   OK')

    def make_pkg(self):
        echo_msg('Creating package...', False)
        os.system('( cd %s && xar --compression none '
                  '-cf "../%s" * )' % (self.flat_dir, self.kwargs['pkg_name']))
        echo_msg('   OK')

    def make_dmg(self):
        if 'dmg' in self.kwargs:
            dmg_build(**self.kwargs['dmg'])
