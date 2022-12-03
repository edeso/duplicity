#!/bin/bash

set -e

cd `dirname $0`/../..

export PYTHONPATH=`pwd`
export PASSPHRASE="test"

for l in $(<po/LINGUAS); do
    rm -rf /tmp/issue683/ ~/.cache/duplicity/issue683
    echo "Using LANG=$l.UTF-8"
    LANG=$l.UTF-8 bin/duplicity -vINFO --name=issue683 testing file:///tmp/issue683
    LANG=$l.UTF-8 bin/duplicity -vINFO --name=issue683 testing file:///tmp/issue683
    LANG=$l.UTF-8 bin/duplicity -vINFO --name=issue683 testing file:///tmp/issue683
done
