#! /usr/bin/env python
# -*- coding: utf-8 -*-

# eLyXer: LyX to HTML converter
# Copyright 2009 Alex Fernández
# Published under the GPLv3, see LICENSE for details

# Alex 20090313
# eLyXer runtime options

import codecs


class Options(object):
  "A set of runtime options"

  nocopy = False
  debug = False
  quiet = False

  def parseoptions(self, args):
    "Parse command line options"
    while args[0].startswith('--'):
      option = args[0].replace('-', '')
      if option == 'help':
        return 'eLyXer help'
      if not hasattr(Options, option):
        return 'Option ' + option + ' not recognized'
      setattr(Options, option, True)
      del args[0]
    return None

