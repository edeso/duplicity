#!/usr/bin/python3
# -*- coding: utf-8 -*-
import re
import sys
from duplicity.__main__ import dup_run
if __name__ == '__main__':
    sys.argv[0] = re.sub(r'(-script\.pyw|\.exe)?$', '', sys.argv[0])
    sys.exit(dup_run())
