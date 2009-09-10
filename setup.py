#! /usr/bin/env python
# -*- coding: utf-8 -*-

#   eLyXer -- convert LyX source files to HTML output.
#
#   Copyright (C) 2009 Alex Fernández
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

# --end--
# Alex 20090908
# eLyXer distutils management

import sys
sys.path.append('src')

from conf.config import *
#from util.trace import Trace
from distutils.core import setup

setup(name = 'eLyXer',
    version = GeneralConfig.version['number'],
    description = 'LyX to HTML converter',
    long_description = 'eLyXer is a LyX to HTML converter, with a focus on flexibility and elegant output.',
    author = 'Alex Fernandez',
    author_email = 'elyxer@gmail.com',
    url = 'http://www.nongnu.org/elyxer/',
    py_modules = ['elyxer'],
    license = 'GPL version 3 or later',
    platforms = ['Windows NT/2000/XP', 'Mac OS X', 'GNU/Linux'],
    )

