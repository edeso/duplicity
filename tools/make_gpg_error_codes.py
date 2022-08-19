#!/usr/bin/env python3
# -*- Mode:Shell; indent-tabs-mode:nil; tab-width -*-
#
# Copyright 2022 Kenneth Loafman <kenneth@loafman.com>
#
# This file is part of duplicity.
#
# Duplicity is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version.
#
# Duplicity is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with duplicity; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

import os
import re
import subprocess

code_line_re = re.compile(r"^(\d+)\t+([A-Z_]+)\t+(.*)$")

p = subprocess.run(["curl", "https://raw.githubusercontent.com/gpg/libgpg-error/master/src/err-codes.h.in",
               "--output", "/tmp/error-codes.h.in"])
if p.returncode:
    raise subprocess.CalledProcessError

lines = open(u"/tmp/error-codes.h.in").readlines()

os.chdir(os.path.dirname(__file__) + u"/../duplicity")
output = open(u"gpg_error_codes.py", u"w")

print(u"""\
# *******************************************************
# *** This is a generated file from project duplicity ***
# ***                 DO NOT MODIFY!                  ***
# *** Use tools/make_gpg_error_codes.py to update.    ***
# *******************************************************
""", file=output)

print(u"gpg_error_codes = {", file=output)

for line in lines:
    match = code_line_re.match(line)
    if match:
        print(f"    {match.group(1)}: u'{match.group(2)}: ' + _(u'{match.group(3)}'),", file=output)

print(u"}", file=output)
