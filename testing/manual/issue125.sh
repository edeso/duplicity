#!/bin/bash

set -e -v

cd `dirname $0`/../..

export PYTHONPATH=`pwd`
export PASSPHRASE=""
export MYTESTKEY=2D7CDA824BB7660CDE350B228C2938CE3CAEB354

ulimit -n 1536
ulimit -n

# Clean up if previous failure
rm -rf /tmp/testfiles /tmp/testbackup ~/.cache/duplicity/issue125

mkdir /tmp/testfiles
mkdir /tmp/testbackup

# Full backup plus 256 incremental backups
for i in {1..256}
do
    echo "File test${i}.file"
    dd if=/dev/urandom of="/tmp/testfiles/test${i}.file" bs=1M count=1 status=none
    bin/duplicity --name issue125 --encrypt-key ${MYTESTKEY} --no-print -v0 /tmp/testfiles file:///tmp/testbackup
done

# verify crashes with "filedescriptor out of range in select()"
bin/duplicity verify --name issue125 --encrypt-key ${MYTESTKEY} file:///tmp/testbackup /tmp/testfiles

# Clean up
rm -r /tmp/testfiles /tmp/testbackup ~/.cache/duplicity/issue125
