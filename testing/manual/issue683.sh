#!/bin/bash

set -e

cd `dirname $0`/../..

export PYTHONPATH=`pwd`
export PASSPHRASE="test"

rm -rf /tmp/issue683/ ~/.cache/duplicity/issue683
LANG=cs_CZ.UTF-8 bin/duplicity -vINFO --name=issue683 testing file:///tmp/issue683
LANG=cs_CZ.UTF-8 bin/duplicity --pydevd -vINFO --name=issue683 testing file:///tmp/issue683
