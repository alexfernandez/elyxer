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
# Alex 20090203
# eLyXer parsers

import codecs
from util.trace import Trace
from util.options import *
from config import *
from parse.configparse import *


linewriter = LineWriter('base.cfg')
writer = ConfigWriter(linewriter)
writer.writeall([FormulaConfig(), ContainerConfig(), BlackBoxConfig(), SpaceConfig(), TranslationConfig()])
linereader = LineReader('base.cfg')
reader = ConfigReader(linereader)
reader.parse()
for section, object in reader.objects.iteritems():
  print
  print 'Section ' + section
  if isinstance(object, list):
    print '  ',
    for piece in object:
      print piece + ', ',
    print
  else:
    for key, value in object.iteritems():
      print '  ' + key + ': ' + value

