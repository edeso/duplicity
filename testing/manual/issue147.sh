#!/bin/bash

cd `dirname "$0"`/../..

export PYTHONPATH=`pwd`

rm -rf /tmp/testbackup/

export PASSPHRASE=goodpass
bin/duplicity --name issue147 -vNOTICE `pwd` file:///tmp/testbackup

echo 'test' > newfile

export PASSPHRASE=badpass
bin/duplicity --name issue147 -vNOTICE `pwd` file:///tmp/testbackup

rm newfile
