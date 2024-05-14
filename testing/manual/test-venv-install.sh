#!/bin/bash

# clean previous runs
rm -rf /tmp/test-setup

# clone the setup branch
git clone -b setup git@gitlab.com:duplicity/duplicity.git /tmp/test-setup
cd /tmp/test-setup

# create a venv in /tmp/test-setup/venv and activate
python3 -m venv venv --system-site-packages
source venv/bin/activate

# install and test - should return version and date
python3 -m pip install .
duplicity -V
python3 -m duplicity -V

# deactivate venv and show that venv without activate works
deactivate
venv/bin/duplicity -V
venv/bin/python3 -m duplicity -V
