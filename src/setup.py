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

from distutils.core import setup


packages = [
    'elyxer', 'elyxer.bib', 'elyxer.conf', 'elyxer.gen', 'elyxer.io',
    'elyxer.main', 'elyxer.maths', 'elyxer.out', 'elyxer.parse',
    'elyxer.proc', 'elyxer.ref', 'elyxer.util', 'elyxer.xtra'
    ]
packages = []

setup(name = 'eLyXer',
    version = 'unknown',
    description = 'LyX to HTML converter',
    long_description = 'eLyXer is a LyX to HTML converter, with a focus on flexibility and elegant output.',
    author = 'Alex Fernandez',
    author_email = 'elyxer@gmail.com',
    url = 'http://elyxer.nongnu.org/',
    packages = packages,
    scripts = ['elyxer.py', 'math2html.py', 'loremipsumize.py'],
    classifiers = [
      'License :: OSI Approved :: GNU General Public License (GPL)',
      'Development Status :: 5 - Production/Stable', 'Environment :: Console',
      'Operating System :: OS Independent', 'Programming Language :: Python :: 2.4',
      'Topic :: Printing', 'Topic :: Text Processing :: Markup :: HTML',
      'Topic :: Utilities', 'Topic :: Internet :: WWW/HTTP :: Dynamic Content'
      ],
    license = 'GPL version 3 or later',
    platforms = ['Windows NT/2000/XP', 'Mac OS X', 'GNU/Linux'],
    )

