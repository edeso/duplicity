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


import glob
import os
import sys
from subprocess import (
    Popen,
    PIPE,
    STDOUT,
)

import pytest

if os.getenv("RUN_CODE_TESTS", None) == "1":
    # Make conditional so that we do not have to import in environments that
    # do not run the tests (e.g. the build servers)
    import pycodestyle

from . import _top_dir, DuplicityTestCase

files_to_test = [os.path.join(_top_dir, "bin/duplicity")]
files_to_test.extend(glob.glob(os.path.join(_top_dir, "duplicity/**/*.py"), recursive=True))
files_to_test.extend(glob.glob(os.path.join(_top_dir, "testing/functional/*.py")))
files_to_test.extend(glob.glob(os.path.join(_top_dir, "testing/unit/*.py")))
files_to_test.extend(glob.glob(os.path.join(_top_dir, "testing/*.py")))

# don't test argparse311.py.  not really ours.
files_to_test.remove(os.path.join(_top_dir, "duplicity/argparse311.py"))


@pytest.mark.skipif(
    not os.getenv("RUN_CODE_TESTS", None) == "1",
    reason="Must set environment var RUN_CODE_TESTS=1",
)
class CodeTest(DuplicityTestCase):
    def run_checker(self, cmd, returncodes=None):
        if returncodes is None:
            returncodes = [0]
        process = Popen(cmd, stdout=PIPE, stderr=STDOUT, universal_newlines=True)
        output = process.communicate()[0]
        if len(output):
            for line in output.split("\n"):
                print(line, file=sys.stderr)
            output = ""
        self.assertTrue(
            process.returncode in returncodes,
            f"Test failed: returncode = {process.returncode}",
        )

    def test_black(self):
        """Black check for out of format files"""
        print()
        self.run_checker(
            [
                "black",
                "--check",
            ]
            + files_to_test,
        )

    def test_pep8(self):
        """Test that we conform to PEP-8 using pycodestyle."""
        # Note that the settings, ignores etc for pycodestyle are set in tox.ini, not here
        print()
        style = pycodestyle.StyleGuide(config_file=os.path.join(_top_dir, "tox.ini"))
        result = style.check_files(files_to_test)
        self.assertEqual(
            result.total_errors,
            0,
            f"Found {result.total_errors} code style errors (and warnings).",
        )

    def test_pylint(self):
        """Pylint test (requires pylint to be installed to pass)"""
        print()
        self.run_checker(
            [
                "pylint",
                f"--rcfile={os.path.join(_top_dir, '.pylintrc')}",
            ]
            + files_to_test
        )


if __name__ == "__main__":
    unittest.main()
