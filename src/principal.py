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
# Alex 20090308
# eLyXer main script
# http://www.nongnu.org/elyxer/


import sys
import os.path
from io.convert import *
from util.trace import Trace
from util.options import *


def readdir(filename, diroption):
  "Read the current directory if needed"
  if getattr(Options, diroption) != None:
    return
  setattr(Options, diroption, os.path.dirname(filename))
  if getattr(Options, diroption) == '':
    setattr(Options, diroption, '.')

def convertdoc(args):
  "Read a whole document and write it"
  ioparser = InOutParser().parse(args)
  if ioparser.parsedin:
    readdir(ioparser.filein, 'directory')
  else:
    Options.directory = '.'
  if ioparser.parsedout:
    readdir(ioparser.fileout, 'destdirectory')
  else:
    Options.destdirectory = '.'
  converter = eLyXerConverter(ioparser)
  converter.convert()

def main():
  "Main function, called if invoked from the command line"
  args = list(sys.argv)
  del args[0]
  Options().parseoptions(args)
  convertdoc(args)

if __name__ == '__main__':
  main()

