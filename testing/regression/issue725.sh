#!/bin/bash

set -e

cd `dirname $0`/../..

export PYTHONPATH=`pwd`
export PASSPHRASE=test

cd /tmp
rm -rf original backup
mkdir -p original/.git/config backup
touch original/.git/config/configfile
touch original/.git/gitfile
touch original/file.txt
cd -

for patt in '/tmp/original' '/tmp/original/*/configfile' '/tmp/original/**/configfile'; do
    duplicity/__main__.py \
        full \
        -v0 --no-print \
        --include=${patt} \
        --exclude='**' \
        /tmp/original \
        file:///tmp/backup
    echo -e "\nduplicity --include=${patt}\n"
    duplicity/__main__.py \
        list-current-files \
        file:///tmp/backup
    echo -e "\nglob.glob(${patt}) results\n"
    python3 -c "import glob; print(glob.glob('${patt}', include_hidden=True, recursive=True))"
done
