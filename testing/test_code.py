# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4; encoding:utf-8 -*-
#
# Copyright 2014 Michael Terry <michael.terry@canonical.com>
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

from __future__ import print_function

import glob
import os
import sys
import subprocess
import pytest
import fnmatch
import os

if os.getenv('RUN_CODE_TESTS', None) == '1':
    # Make conditional so that we do not have to import in environments that
    # do not run the tests (e.g. the build servers)
    import pycodestyle

from . import _top_dir, DuplicityTestCase

skipCodeTest = pytest.mark.skipif(not os.getenv('RUN_CODE_TESTS', None) == '1',
                                  reason='Must set environment var RUN_CODE_TESTS=1')

files_to_test = [
    os.path.join(_top_dir, 'bin/duplicity'),
    os.path.join(_top_dir, 'bin/rdiffdir'),
    os.path.join(_top_dir, 'duplicity'),
    os.path.join(_top_dir, 'testing/functional'),
    os.path.join(_top_dir, 'testing/unit'),
] + glob.glob(os.path.join(_top_dir, 'testing/*.py'))


class CodeTest(DuplicityTestCase):

    def run_checker(self, cmd, returncodes=[0]):
        process = subprocess.Popen(cmd,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   universal_newlines=True)
        output = process.communicate()[0]
        if len(output):
            for line in output.split('\n'):
                print(line, file=sys.stderr)
            output = ""
        self.assertTrue(process.returncode in returncodes,
                        f"Test failed: returncode = {process.returncode}")

    @skipCodeTest
    def test_2to3(self):
        # As we modernize the source code, we can remove more and more nofixes
        self.run_checker([
            "2to3",
            "--nofix=next",
            "--nofix=types",
            "--nofix=unicode",
            # The following fixes we don't want to remove, since they are false
            # positives, things we don't care about, or real incompatibilities
            # but which 2to3 can fix for us better automatically.
            "--nofix=callable",
            "--nofix=dict",
            "--nofix=future",
            "--nofix=imports",
            "--nofix=print",
            "--nofix=raw_input",
            "--nofix=urllib",
            "--nofix=xrange",
            "--nofix=map",
        ] + files_to_test
        )

    @skipCodeTest
    def test_pylint(self):
        """Pylint test (requires pylint to be installed to pass)"""
        self.run_checker([
            "pylint",
            "--rcfile=" + os.path.join(_top_dir, "pylintrc"),
        ] + files_to_test
        )

    @skipCodeTest
    def test_pep8(self):
        """Test that we conform to PEP-8 using pycodestyle."""
        # Note that the settings, ignores etc for pycodestyle are set in tox.ini, not here
        style = pycodestyle.StyleGuide(config_file=os.path.join(_top_dir, 'tox.ini'))
        result = style.check_files(files_to_test)
        self.assertEqual(result.total_errors, 0,
                         "Found %s code style errors (and warnings)." % result.total_errors)


if __name__ == "__main__":
    unittest.main()
