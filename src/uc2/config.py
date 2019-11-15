# -*- coding: utf-8 -*-

import os

APP_NAME = 'Color Picker'
APP_PROC = 'color-picker'
APP_ORG = 'sK1 Project'
APP_DOMAIN = 'sk1project.net'
VERSION = '1.0'
REVISION = 'rc1'
BUILD = ''
CFG_PATH = os.path.expanduser('~')
CFG_DIR = os.path.join(CFG_PATH, '.config', 'color-picker')
CFG_FILE = os.path.join(CFG_DIR, 'config.json')


class JsonConfig(dict):
    pass
