#!/bin/bash

set -e -v

cd `dirname $0`/../..

export PYTHONPATH=`pwd`

# use testing/gnupg forever keys
export GNUPGHOME="testing/gnupg"
export PASSPHRASE="test"
export SIGN_KEY="839E6A2856538CCF"
export SIGN_PASSPHRASE="test"
export ENCRYPT_KEY1="839E6A2856538CCF"
export ENCRYPT_KEY2="453005CE9B736B2A"

ulimit -n 1024
ulimit -n

# Clean up if previous failure
rm -rf /tmp/testfiles /tmp/testbackup ~/.cache/duplicity/issue125

# Make test dirs
mkdir /tmp/testfiles
mkdir /tmp/testbackup

# Full backup plus 256 incremental backups
for i in {1..256}
do
    echo "File test${i}.file"
    dd if=/dev/urandom of="/tmp/testfiles/test${i}.file" bs=1M count=1 status=none
    bin/duplicity --name issue125 --encrypt-key ${ENCRYPT_KEY1} --no-print -v0 /tmp/testfiles file:///tmp/testbackup
done

# Verify may crash with "filedescriptor out of range in select()"
bin/duplicity verify --name issue125 --encrypt-key ${ENCRYPT_KEY1} file:///tmp/testbackup /tmp/testfiles

# Clean up
rm -r /tmp/testfiles /tmp/testbackup ~/.cache/duplicity/issue125
