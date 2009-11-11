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
import struct
from util.trace import Trace
from gen.container import *
from io.path import *


class Image(Container):
  "An embedded image"

  converter = True
  ignoredtexts = ImageConfig.size['ignoredtexts']

  def __init__(self):
    self.parser = InsetParser()
    self.output = ImageOutput()
    self.type = 'embedded'
    self.width = None
    self.height = None

  def process(self):
    "Place the url, convert the image if necessary."
    self.origin = InputPath(self.parameters['filename'])
    if not self.origin.exists():
      Trace.error('Image ' + unicode(self.origin) + ' not found')
      return
    self.destination = self.getdestination(self.origin)
    self.convert(self.getparams())
    self.setsize()

  def getdestination(self, origin):
    "Convert origin path to destination path."
    "Changes extension of destination to output image format."
    destination = OutputPath(origin)
    forceformat = '.jpg'
    forcedest = '.png'
    if Options.forceformat:
      forceformat = Options.forceformat
      forcedest = Options.forceformat
    if not destination.hasext(forceformat):
      destination.changeext(forcedest)
    destination.removebackdirs()
    return destination

  def convert(self, params):
    "Convert an image to PNG"
    if not Image.converter:
      return
    if self.origin == self.destination:
      return
    if self.destination.exists():
      if self.origin.getmtime() <= self.destination.getmtime():
        # file has not changed; do not convert
        return
    self.destination.createdirs()
    command = 'convert '
    for param in params:
      command += '-' + param + ' ' + unicode(params[param]) + ' '
    command += '"' + unicode(self.origin) + '" "'
    command += unicode(self.destination) + '"'
    try:
      result = os.system(command)
      Trace.debug('ImageMagick Command: "' + command + '"')
      if result != 0:
        Trace.error('ImageMagick not installed; images will not be processed')
        Image.converter = False
        return
      Trace.message('Converted ' + unicode(self.origin) + ' to ' +
          unicode(self.destination))
    except OSError:
      Trace.error('Error while converting image ' + self.origin)

  def getparams(self):
    "Get the parameters for ImageMagick conversion"
    params = dict()
    scale = 100
    if 'scale' in self.parameters:
      scale = int(self.parameters['scale'])
    if self.origin.hasext('.svg'):
      params['density'] = scale
    elif self.origin.hasext('.jpg') or self.origin.hasext('.png'):
      params['resize'] = unicode(scale) + '%'
    elif self.origin.hasext('.pdf'):
      params['define'] = 'pdf:use-cropbox=true'
    return params

  def setsize(self):
    "Set the size attributes width and height."
    self.setifparam('width')
    self.setifparam('height')
    if self.width or self.height:
      return
    imagefile = ImageFile(self.destination)
    width, height = imagefile.getdimensions()
    if width:
      self.width = unicode(width)
    if height:
      self.height = unicode(height)

  def setifparam(self, name):
    "Set the value in the container if it exists as a param."
    if not name in self.parameters:
      return
    value = unicode(self.parameters[name])
    for ignored in Image.ignoredtexts:
      if ignored in value:
        value = value.replace(ignored, '')
    setattr(self, name, value)

class ImageFile(object):
  "A file corresponding to an image (JPG or PNG)"

  dimensions = dict()

  def __init__(self, path):
    "Create the file based on its path"
    self.path = path

  def getdimensions(self):
    "Get the dimensions of a JPG or PNG image"
    if not self.path.exists():
      return None, None
    if unicode(self.path) in ImageFile.dimensions:
      return ImageFile.dimensions[unicode(self.path)]
    dimensions = (None, None)
    if self.path.hasext('.png'):
      dimensions = self.getpngdimensions()
    elif self.path.hasext('.jpg'):
      dimensions = self.getjpgdimensions()
    ImageFile.dimensions[unicode(self.path)] = dimensions
    return dimensions

  def getpngdimensions(self):
    "Get the dimensions of a PNG image"
    pngfile = self.path.open()
    pngfile.seek(16)
    width = self.readlong(pngfile)
    height = self.readlong(pngfile)
    pngfile.close()
    return (width, height)

  def getjpgdimensions(self):
    "Get the dimensions of a JPEG image"
    jpgfile = self.path.open()
    start = self.readword(jpgfile)
    if start != int('ffd8', 16):
      Trace.error(unicode(self.path) + ' not a JPEG file')
      return (None, None)
    self.skipheaders(jpgfile, ['ffc0', 'ffc2'])
    self.seek(jpgfile, 3)
    height = self.readword(jpgfile)
    width = self.readword(jpgfile)
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
      self.seek(file, length - 2)
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

  def seek(self, file, bytes):
    "Seek forward, just by reading the given number of bytes"
    file.read(bytes)

class ImageOutput(object):
  "Returns an image in the output"

  figure = TranslationConfig.constants['figure']

  def gethtml(self, container):
    "Get the HTML output of the image as a list"
    html = ['<img class="' + container.type + '"']
    if container.origin.exists():
      html.append(' src="' + container.destination.url +
          '" alt="' + ImageOutput.figure + ' ' + container.destination.url + '"')
      if container.width:
        html.append(' width="' + container.width + '"')
      if container.height:
        html.append(' height="' + container.height + '"')
    else:
      html.append(' src="' + container.origin.url + '"')
    html.append('/>\n')
    return html

