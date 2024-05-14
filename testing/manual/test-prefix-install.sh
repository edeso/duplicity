#!/bin/bash

# clean previous runs
rm -rf /tmp/test-setup

# clone the setup branch
git clone -b setup git@gitlab.com:duplicity/duplicity.git /tmp/test-setup
cd /tmp/test-setup

# install and test - should return version and date
python3.12 -m pip install . --prefix=/tmp/test-setup/prefix
export PYTHONPATH=/tmp/test-setup/prefix/lib/python3.12/site-packages/
export PATH=/tmp/test-setup/prefix/bin:$PATH
duplicity -V
python3.12 -m duplicity -V
