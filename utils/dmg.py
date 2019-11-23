# -*- coding: utf-8 -*-
#
#   macOS dmg build
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

#   Requires hfsprogs:
#   sudo apt-get install hfsprogs

import math
import os
import shutil

from . import fsutils


def dmg_build(targets=None,
              dmg_filename='test.dmg',
              volume_name='Install',
              dist_dir='.', **_kwargs):
    """
    DMG generation using genisoimage.
    Produces well blessed DMG image.

    :param targets: target files and directories
    :param dmg_filename:
    :param volume_name: name for mounted volume
    :param dist_dir: directory where saving DMG file
    :param _kwargs: additional agrs
    """

    if not targets:
        raise Exception('DMG payload is not provided!')

    if os.path.exists('tmp_dmg'):
        os.system('rm -rf tmp_dmg')

    os.system('mkdir -p tmp_dmg')
    if not os.path.exists(dist_dir):
        os.makedirs(dist_dir)

    # Copying
    for item in targets:
        if os.path.isfile(item):
            shutil.copy(item, 'tmp_dmg')
        else:
            dst = os.path.join('tmp_dmg', os.path.basename(item))
            shutil.copytree(item, dst)

    dmg_file = os.path.join(dist_dir, dmg_filename)
    os.system('genisoimage -V "%s" -D -R -apple '
              '-no-pad -o %s tmp_dmg' % (volume_name, dmg_file))
    os.system('rm -rf tmp_dmg')


def dmg_build2(targets=None,
               dmg_filename='test.dmg',
               volume_name='Install',
               dist_dir='.', **_kwargs):
    """
    DMG generation using mkfs.hfsplus.
    Not perfect because there is no volume bless

    :param targets: target files and directories
    :param dmg_filename:
    :param volume_name: name for mounted volume
    :param dist_dir: directory where saving DMG file
    :param _kwargs: additional agrs
    """

    if not targets:
        raise Exception('DMG payload is not provided!')

    sz = float(sum(fsutils.getsize(item) for item in targets))
    size = int(math.ceil(sz / 10 ** 6)) or 1

    if os.path.exists('/tmp/%s' % dmg_filename):
        os.remove('/tmp/%s' % dmg_filename)

    if os.path.exists('/mnt/tmp_dmg'):
        os.system('rm -rf /mnt/tmp_dmg')

    # File allocation
    os.system('dd if=/dev/zero of=/tmp/%s bs=1M '
              'count=%d status=progress' % (dmg_filename, size))
    # Formatting for HFS+
    os.system('mkfs.hfsplus -v "%s" /tmp/%s' % (volume_name, dmg_filename))

    # Mounting
    os.system('mkdir -pv /mnt/tmp_dmg && '
              'mount -o loop /tmp/%s /mnt/tmp_dmg' % dmg_filename)
    # Copying
    for item in targets:
        if os.path.isfile(item):
            shutil.copy(item, '/mnt/tmp_dmg')
        else:
            dst = os.path.join('/mnt/tmp_dmg', os.path.basename(item))
            shutil.copytree(item, dst)

    # Unmounting
    os.system('umount /mnt/tmp_dmg && rm -rf /mnt/tmp_dmg')
    dst = os.path.join(dist_dir, dmg_filename)
    shutil.move('/tmp/%s' % dmg_filename, dst)
