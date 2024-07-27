#!/bin/bash

set -e

export PYTHONPATH=.
export GNUPGHOME=./testing/gnupg

NAME=1G-test
TARGET=/tmp/testdup

rm -rf $TARGET ~/.cache/duplicity/$NAME

# [ -e /tmp/random.dat ] || openssl rand -out /tmp/random.dat $(( 2*(2**30) ))
[ -e /tmp/random.dat ] || dd bs=1M count=2048 if=/dev/urandom of=/tmp/random.dat

duplicity/__main__.py full \
                      /tmp/random.dat \
                      file://$TARGET \
                      --encrypt-key=453005CE9B736B2A \
                      --concurrency=2 \
                      --volsize=1 \
                      --verbosity=info \
                      --name=$NAME

duplicity/__main__.py verify \
                      file://$TARGET \
                      /tmp/random.dat \
                      --encrypt-key=453005CE9B736B2A \
                      --verbosity=info \
                      --name=$NAME
