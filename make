#!/bin/bash

# eLyXer: LyX to HTML converter
# Copyright 2009 Alex Fernández
# Published under the GPLv3, see LICENSE for details

# Alex 20090310: make script to generate "binary"

cd src
./conflate.py elyxer.py > elyxer
mv elyxer ..
cd ..
chmod 755 elyxer
cd docs
../elyxer userguide.lyx userguide.html
../elyxer devguide.lyx devguide.html

