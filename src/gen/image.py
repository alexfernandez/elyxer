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
# eLyXer image treatment

import os
import os.path
import struct
from util.trace import Trace
from gen.container import *
from io.output import MirrorOutput


class Image(Container):
  "An embedded image"

  converter = True

  def __init__(self):
    self.parser = InsetParser()
    self.output = ImageOutput()

  def process(self):
    "Place the url, convert the image if necessary."
    self.url = self.parser.parameters['filename']
    origin = self.getoriginpath(self.url)
    if not os.path.exists(origin):
      Trace.error('Image ' + origin + ' not found')
      return
    self.destination = self.getdestination(self.url)
    destination = self.getdestinationpath(self.destination)
    density = 100
    if 'scale' in self.parser.parameters:
      density = int(self.parser.parameters['scale'])
    self.convert(origin, destination, density)
    self.width, self.height = self.getdimensions(destination)

  def getoriginpath(self, path):
    "Get the correct origin path for the image."
    if os.path.isabs(path):
      return path
    return Options.directory + os.path.sep + path

  def getdestination(self, path):
    "Get the destination path to use in the web page."
    if os.path.isabs(path):
      path = os.path.basename(path)
    base, ext = os.path.splitext(path)
    if ext.lower() != '.jpg':
      ext = '.png'
    return base + ext

  def getdestinationpath(self, path):
    "Get the destination path on disk for the image."
    return Options.destdirectory + os.path.sep + path

  def convert(self, origin, destination, density):
    "Convert an image to PNG"
    if not Image.converter:
      return
    if origin == destination:
      return
    if os.path.exists(destination):
      if os.path.getmtime(origin) <= os.path.getmtime(destination):
        # file has not changed; do not convert
        return
    dir = os.path.dirname(destination)
    if len(dir) > 0 and not os.path.exists(dir):
      os.makedirs(dir)
    try:
      result = os.system('convert -density ' + unicode(density) + ' "' + origin +
          '" "' + destination + '"')
      if result != 0:
        Trace.error('ImageMagick not installed; images will not be processed')
        Image.converter = False
        return
      Trace.message('Converted ' + origin + ' to ' + destination + ' at ' +
          unicode(density) + '%')
    except OSError:
      Trace.error('Error while converting image ' + origin)

  dimensions = dict()

  def getdimensions(self, filename):
    "Get the dimensions of a PNG image"
    if not os.path.exists(filename):
      return None, None
    if filename in Image.dimensions:
      return Image.dimensions[filename]
    base, ext = os.path.splitext(filename)
    dimensions = (None, None)
    if ext == '.png':
      dimensions = self.getpngdimensions(filename)
    elif ext == '.jpg':
      dimensions = self.getjpgdimensions(filename)
    Image.dimensions[filename] = dimensions
    return dimensions

  def getpngdimensions(self, filename):
    "Get the dimensions of a PNG image"
    pngfile = codecs.open(filename, 'rb')
    pngfile.seek(16)
    width = self.readlong(pngfile)
    height = self.readlong(pngfile)
    pngfile.close()
    return (width, height)

  def getjpgdimensions(self, filename):
    "Get the dimensions of a JPEG image"
    jpgfile = codecs.open(filename, 'rb')
    start = self.readword(jpgfile)
    if start != int('ffd8', 16):
      Trace.error(filename + ' not a JPEG file')
      return (None, None)
    self.skipheaders(jpgfile, ['ffc0', 'ffc2'])
    jpgfile.seek(3, os.SEEK_CUR)
    width = self.readword(jpgfile)
    height = self.readword(jpgfile)
    jpgfile.close()
    return (width, height)

  def skipheaders(self, file, hexvalues):
    "Skip JPEG headers until one of the parameter headers is found"
    headervalues = [int(value, 16) for value in hexvalues]
    header = self.readword(file)
    safetycounter = 0
    while header not in headervalues and safetycounter < 30:
      length = self.readword(file)
      if length == 0:
        Trace.error('End of file ' + file.name)
        return
      file.seek(length - 2, os.SEEK_CUR)
      header = self.readword(file)
      safetycounter += 1

  def readlong(self, file):
    "Read a long (32-bit) value from file"
    return self.readformat(file, '>L', 4)

  def readword(self, file):
    "Read a 16-bit value from file"
    return self.readformat(file, '>H', 2)

  def readformat(self, file, format, bytes):
    "Read any format from file"
    read = file.read(bytes)
    if read == '':
      Trace.error('EOF reached')
      return 0
    tuple = struct.unpack(format, read)
    return tuple[0]

class ImageOutput(object):
  "Returns an image in the output"

  def gethtml(self, container):
    "Get the HTML output of the image as a list"
    cssclass = 'embedded'
    html = ['<img class="' + cssclass + '"']
    if hasattr(container, 'destination'):
      html.append(' src="' + container.destination +
          '" alt="figure ' + container.destination + '" width="' +
          unicode(container.width) + '" height="' + unicode(container.height) + '"')
    else:
      html.append(' src="' + container.url + '"')
    html.append('/>\n')
    return html

