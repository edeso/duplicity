# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4; encoding:utf-8 -*-
#
# Copyright 2008 Michael Terry <mike@mterry.name>
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
import sys
import unittest

from testing import _runtest_dir
from testing import _top_dir
from . import FunctionalTestCase


class LogTest(FunctionalTestCase):
    """Test machine-readable functions/classes in log.py"""

    logfile = f"{_runtest_dir}/duplicity.log"

    def setUp(self):
        super().setUp()
        assert not os.system(f"rm -f {self.logfile}")

    def tearDown(self):
        super().tearDown()
        assert not os.system(f"rm -f {self.logfile}")

    def test_command_line_error(self):
        """Check notification of a simple error code"""

        # Run actual duplicity command (will fail because bad dirs passed)
        basepython = f"python{sys.version_info.major}.{sys.version_info.minor}"
        cmd = (
            f"{basepython} {_top_dir}/duplicity/__main__.py --log-file={self.logfile} "
            f"full testing baddir >/dev/null 2>&1"
        )
        os.system(cmd)

        # The format of the file should be:
        # """ERROR 23 CommandLineError
        # . Blah blah blah.
        # . Blah blah blah.
        #
        # """
        f = open(self.logfile, "r")
        linecount = 0
        lastline = False
        for line in f:
            assert not lastline
            linecount += 1
            if linecount == 1:
                assert line == "ERROR 23 CommandLineError\n"
            elif line[0] != "\n":
                assert line.startswith(r". ")
            else:
                lastline = True
        assert lastline


if __name__ == "__main__":
    unittest.main()
