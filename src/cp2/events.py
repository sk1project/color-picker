# -*- coding: utf-8 -*-
#
#  Copyright (C) 2011-2017 by Igor E. Novikov
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.

import logging

LOG = logging.getLogger(__name__)

"""
Module provides Qt-like signal-slot functionality
for internal events processing.

Signal arguments:
CONFIG_MODIFIED   attr, value - modified config field
CMS_CHANGED		  no args
"""

# Signal channels

CONFIG_MODIFIED = ['CONFIG_MODIFIED']
CMS_CHANGED = ['CMS_CHANGED']

ALL_CHANNELS = [CONFIG_MODIFIED, CMS_CHANGED, ]


def connect(channel, receiver):
    """
    Connects signal receive method
    to provided channel.
    """
    if callable(receiver):
        # noinspection PyBroadException
        try:
            channel.append(receiver)
        except Exception:
            msg = "Cannot connect to channel <%s> receiver: <%s> %s"
            LOG.exception(msg, channel, receiver)


def disconnect(channel, receiver):
    """
    Disconnects signal receive method
    from provided channel.
    """
    if callable(receiver):
        # noinspection PyBroadException
        try:
            channel.remove(receiver)
        except Exception:
            msg = "Cannot disconnect from channel <%s> receiver: <%s> %s"
            LOG.exception(msg, channel, receiver)


def emit(channel, *args):
    """
    Sends signal to all receivers in channel.
    """
    for receiver in channel[1:]:
        # noinspection PyBroadException
        try:
            if callable(receiver):
                receiver(*args)
        except Exception:
            msg = 'Error calling <%s> receiver with %s %s'
            LOG.exception(msg, receiver, args)
            continue


def clean_channel(channel):
    """
    Cleans channel queue.
    """
    name = channel[0]
    channel[:] = []
    channel.append(name)


def clean_all_channels():
    """
    Cleans all channels.
    """
    for item in ALL_CHANNELS:
        clean_channel(item)
