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
# Alex 20090504
# eLyXer configuration manipulation

import sys
import datetime
from util.trace import Trace
from util.options import *
from conf.config import *
from conf.fileconfig import *


class Config(object):
  "A configuration file"

  cfg = 'conf/base.cfg'
  py = 'conf/config.py'
  help = False

  def run(self, args):
    "Parse command line options and run export to cfg or to py"
    parser = CommandLineParser(Config)
    error = parser.parseoptions(args)
    if error:
      Trace.error(error)
      self.usage()
    elif Config.help:
      self.usage()
    option = self.parseoption(args)
    if not option:
      Trace.error('Choose cfg or py')
      self.usage()
    if option == 'cfg':
      self.exportcfg()
      return
    elif option == 'py':
      self.exportpy()
      return
    else:
      Trace.error('Unknown option ' + option)
      self.usage()

  def usage(self):
    "Show tool usage"
    Trace.error('Usage: exportconfig.py [options] [cfg|py]')
    Trace.error('  cfg: export to text configuration file')
    Trace.error('  py: export to python file')
    Trace.error('  options: --cfg base.cfg, --py config.py')
    exit()

  def read(self):
    "Read from configuration file"
    linereader = LineReader(Config.cfg)
    reader = ConfigReader(linereader)
    reader.parse()
    reader.objects['GeneralConfig.version']['date'] = datetime.date.today().isoformat()
    return reader

  def exportcfg(self):
    "Export configuration to a cfg file"
    linewriter = LineWriter(Config.cfg)
    writer = ConfigWriter(linewriter)
    writer.writeall([FormulaConfig(), ContainerConfig(), BlackBoxConfig(), SpaceConfig(), TranslationConfig()])

  def exportpy(self):
    "Export configuration as a Python file"
    reader = self.read()
    linewriter = LineWriter(Config.py)
    translator = ConfigTranslator(linewriter)
    translator.write(reader.objects)

  def parseoption(self, args):
    "Parse the next option"
    if len(args) == 0:
      return None
    option = args[0]
    del args[0]
    return option

config = Config()
del sys.argv[0]
config.run(sys.argv)

