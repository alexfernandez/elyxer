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
# Alex 20101110
# eLyXer standalone formula conversion to HTML.

from util.trace import Trace
from maths.formula import *
from maths.bits import *
from maths.command import *
from maths.hybrid import *
from maths.array import *
from maths.macro import *


def math2html(formula):
  "Convert some TeX math to HTML."
  factory = FormulaFactory()
  whole = factory.parseformula(formula)
  whole.process()
  return ''.join(whole.gethtml())

