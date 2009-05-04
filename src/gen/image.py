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

  ending = '\\end_inset'

  converter = True

  def __init__(self):
    self.parser = InsetParser()
    self.output = ImageOutput()

  def process(self):
    self.url = self.parser.parameters['filename']
    origin = self.getpath(self.url)
    if not os.path.exists(origin):
      Trace.error('Image ' + origin + ' not found')
      return
    self.destination = self.getdestination(self.url)
    destination = self.getpath(self.destination)
    density = 100
    if 'scale' in self.parser.parameters:
      density = int(self.parser.parameters['scale'])
    self.convert(origin, destination, density)
    self.width, self.height = self.getdimensions(destination)

  def getpath(self, path):
    "Get the correct path for the image"
    if os.path.isabs(path):
      return path
    return Options.directory + os.path.sep + path

  def getdestination(self, origin):
    "Get the destination URL for an image URL"
    if os.path.isabs(origin):
      dest = os.path.basename(origin)
    else:
      dest = origin
    return os.path.splitext(dest)[0] + '.png'

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
      result = os.system('convert -density ' + str(density) + ' "' + origin +
          '" "' + destination + '"')
      if result != 0:
        Trace.error('ImageMagick not installed; images will not be processed')
        Image.converter = False
        return
      Trace.message('Converted ' + origin + ' to ' + destination + ' at ' +
          str(density) + '%')
    except OSError:
      Trace.error('Error while converting image ' + origin)

  dimensions = dict()

  def getdimensions(self, filename):
    "Get the dimensions of a PNG image"
    if not os.path.exists(filename):
      return None, None
    if filename in Image.dimensions:
      return Image.dimensions[filename]
    pngfile = codecs.open(filename, 'rb')
    pngfile.seek(16)
    width = self.readlong(pngfile)
    height = self.readlong(pngfile)
    dimensions = (width, height)
    pngfile.close()
    Image.dimensions[filename] = dimensions
    return dimensions

  def readlong(self, file):
    "Read a long value"
    tuple = struct.unpack('>L', file.read(4))
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
          str(container.width) + '" height="' + str(container.height) + '"')
    else:
      html.append(' src="' + container.url + '"')
    html.append('/>\n')
    return html

