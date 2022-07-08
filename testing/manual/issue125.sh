#!/bin/bash

set -e -v

cd `dirname $0`/../..

export PYTHONPATH=`pwd`
export PASSPHRASE=""
export MYTESTKEY=2D7CDA824BB7660CDE350B228C2938CE3CAEB354

# Clean up
rm -rf /tmp/testfiles /tmp/testbackup ~/.cache/duplicity/issue125

ulimit -n 2048
ulimit -n

mkdir /tmp/testfiles
mkdir /tmp/testbackup

# Full backup plus 253 incremental backups
for i in {254..1}
do
    echo "File test${i}"
    dd if=/dev/urandom of=/tmp/testfiles/test${i}.file bs=1M count=1 status=none
    bin/duplicity --name issue125 --encrypt-key ${MYTESTKEY} --no-print -v0 /tmp/testfiles par2+file:///tmp/testbackup
done

# verify works
bin/duplicity verify --name issue125 --encrypt-key ${MYTESTKEY} par2+file:///tmp/testbackup /tmp/testfiles

# 255th backup set
dd if=/dev/urandom of=/tmp/testfiles/test255.file bs=1M count=1 status=none
bin/duplicity --name issue125 --encrypt-key ${MYTESTKEY} --no-print -v0 /tmp/testfiles par2+file:///tmp/testbackup

# verify crashes with "filedescriptor out of range in select()"
bin/duplicity verify --name issue125 --encrypt-key ${MYTESTKEY} par2+file:///tmp/testbackup /tmp/testfiles

# Clean up
rm -r /tmp/testfiles /tmp/testbackup ~/.cache/duplicity/issue125
