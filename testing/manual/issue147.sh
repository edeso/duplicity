#!/bin/bash

set -e

cd `dirname $0`/../..

export PYTHONPATH=`pwd`

export PASSPHRASE=goodpass
bin/duplicity --name issue147 --no-print -vNOTICE `pwd` file:///tmp/testbackup
export PASSPHRASE=badpass
bin/duplicity --name issue147 --no-print -vNOTICE `pwd` file:///tmp/testbackup
