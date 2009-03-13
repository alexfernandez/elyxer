#!/bin/bash

# eLyXer: LyX to HTML converter
# Copyright 2009 Alex Fernández
# Published under the GPLv3, see LICENSE for details

# Alex 20090310: make script to generate "binary"

# create executable
cd src
./conflate.py elyxer.py > elyxer
mv elyxer ..
cd ..
chmod 755 elyxer
# prepare documentation
cd docs
../elyxer userguide.lyx userguide.html
../elyxer devguide.lyx devguide.html
rm -f *.lyx~
cd ..
# make compressed files
mkdir -p dist
cd ..
DATE=$(date +%Y%m%d)
tar --exclude "elyxer/dist" --exclude "elyxer/.git" --exclude "elyxer/samples" -czf elyxer-$DATE.tar.gz elyxer
mv elyxer-$DATE.tar.gz elyxer/dist
zip -q elyxer-$DATE.zip elyxer/* -x *dist*
zip -qr elyxer-$DATE.zip elyxer/src
zip -qr elyxer-$DATE.zip elyxer/docs
zip -qr elyxer-$DATE.zip elyxer/test
mv elyxer-$DATE.zip elyxer/dist
cd elyxer
# run tests
echo "Testing eLyXer -- any text below this line signals an error"
cd test
for file in $(ls *.lyx); do
name=$(basename $file .lyx)
../elyxer --quiet $name.lyx $name-test.html
diff $name-test.html $name-good.html
done

