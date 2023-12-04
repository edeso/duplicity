#!/bin/bash

cd `dirname $0`/../..

export PYTHONPATH=`pwd`
export PASSPHRASE=foo

alias duplicity=duplicity/__main__.py

for t in 'mirror' 'stripe'; do
    for i in $(seq 3); do
        duplicity full \
                  --no-encryption \
                  /etc/hosts \
                  "multi:///`pwd`/testing/regression/issue781.json?mode=$t"
        sleep 1
    done

    duplicity  remove-all-but-n-full 1 \
               --verbosity 9 \
               --no-encryption \
               "multi:///`pwd`/testing/regression/issue781.json?mode=$t" \
               --force

    ls -l /tmp/*_drive

    rm -rf /tmp/*_drive
done
