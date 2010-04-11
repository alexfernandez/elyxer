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
# Alex 20100411
# eLyXer multi-platform installation

import platform
import sys
import os
import shutil


class Installer(object):
  "The eLyXer installer."

  elyxer = 'elyxer.py'

  def error(self, string):
    "Print an error string."
    self.show(string, sys.stderr)

  def show(self, message, channel = sys.stdout):
    "Show a message out of a channel"
    channel.write(message + '\n')

  def usage(self):
    "Show usage and requirements."
    self.error('Usage: python install.py')
    self.error('Requirements: Python version 2.3 and above, Python 3 not supported.')
    exit()

  def copybin(self):
    "Check permissions, copy binary file."
    self.show('Path: ' + unicode(sys.path))
    system = platform.system()
    if system == 'Linux':
      path = self.copylinux()
    elif system == 'Windows':
      path = self.copywindows()
    else:
      self.error('Unknown operating system ' + system + '; aborting')
      self.usage()
    if path:
      self.show('eLyXer installed as a binary in ' + path + '.')

  def copylinux(self):
    "Copy binary on Linux."
    return self.copypaths(os.environ['PATH'].split(':'))

  def copywindows(self):
    "Copy binary on Windows."
    return self.copypaths(os.environ['PATH'].split(';'))

  def copypaths(self, paths):
    "Try to copy eLyXer to any of the given paths."
    for path in paths:
      if path == '.':
        next
      try:
        shutil.copy2(Installer.elyxer, path)
        return path
      except IOError:
        pass
    return None

  def installmodule(self):
    "Install eLyXer as a module."
    self.show('Uid: ' + unicode(os.getuid()))
    sys.argv.append('install')
    import setup
    self.show('eLyXer installed as a module.')

  def checkpermissions(self):
    "Check if the user has permissions to install as a module."
    pass

  def checkversion(self):
    "Check the current version."
    version = platform.python_version_tuple()
    if int(version[0]) > 2:
      self.error(unicode(version))
      self.usage()
    if int(version[1]) < 3:
      self.usage()
    self.error('System: ' + platform.system())
    if int(version[1]) == 3:
      self.copybin()
    self.copybin()
    self.installmodule()

Installer().checkversion()

