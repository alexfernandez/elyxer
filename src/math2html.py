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

from elyxer.util.trace import Trace
from elyxer.util.options import *
from elyxer.maths.formula import *
from elyxer.maths.bits import *
from elyxer.maths.command import *
from elyxer.maths.hybrid import *
from elyxer.maths.array import *
from elyxer.maths.macro import *
from elyxer.proc.formulaproc import *


def math2html(formula):
  "Convert some TeX math to HTML."
  factory = FormulaFactory()
  whole = factory.parseformula(formula)
  FormulaProcessor().process(whole)
  whole.process()
  return ''.join(whole.gethtml())

def main():
  "Main function, called if invoked from elyxer.the command line"
  args = sys.argv
  Options().parseoptions(args)
  if len(args) != 1:
    Trace.error('Usage: math2html.py escaped_string')
    exit()
  result = math2html(args[0])
  Trace.message(result)

if __name__ == '__main__':
  main()

