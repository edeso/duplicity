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
import subprocess
import sys

import pytest

if os.getenv(u'RUN_CODE_TESTS', None) == u'1':
    # Make conditional so that we do not have to import in environments that
    # do not run the tests (e.g. the build servers)
    import pycodestyle

from . import _top_dir, DuplicityTestCase
from tools import find_unadorned_strings

skipCodeTest = pytest.mark.skipif(not os.getenv(u'RUN_CODE_TESTS', None) == u'1',
                                  reason=u'Must set environment var RUN_CODE_TESTS=1')

files_to_test = [
    os.path.join(_top_dir, u'bin/duplicity'),
    os.path.join(_top_dir, u'bin/rdiffdir'),
]
files_to_test.extend(glob.glob(os.path.join(_top_dir, u'duplicity/**/*.py'), recursive=True))
files_to_test.extend(glob.glob(os.path.join(_top_dir, u'testing/functional/*.py')))
files_to_test.extend(glob.glob(os.path.join(_top_dir, u'testing/unit/*.py')))
files_to_test.extend(glob.glob(os.path.join(_top_dir, u'testing/*.py')))


class CodeTest(DuplicityTestCase):

    def run_checker(self, cmd, returncodes=None):
        if returncodes is None:
            returncodes = [0]
        process = subprocess.Popen(cmd,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   universal_newlines=True)
        output = process.communicate()[0]
        if len(output):
            for line in output.split(u'\n'):
                print(line, file=sys.stderr)
            output = u""
        self.assertTrue(process.returncode in returncodes,
                        f"Test failed: returncode = {process.returncode}")

    @skipCodeTest
    def test_pylint(self):
        u"""Pylint test (requires pylint to be installed to pass)"""
        self.run_checker([
            u"pylint",
            u"--rcfile=" + os.path.join(_top_dir, u"pylintrc"),
        ] + files_to_test
        )

    @skipCodeTest
    def test_pep8(self):
        u"""Test that we conform to PEP-8 using pycodestyle."""
        # Note that the settings, ignores etc for pycodestyle are set in tox.ini, not here
        style = pycodestyle.StyleGuide(config_file=os.path.join(_top_dir, u'tox.ini'))
        result = style.check_files(files_to_test)
        self.assertEqual(result.total_errors, 0,
                         u"Found %s code style errors (and warnings)." % result.total_errors)

    @skipCodeTest
    def test_unadorned_string_literals(self):
        u"""For predictable results in python/3 all string literals need to be marked as unicode, bytes or raw"""

        do_assert = False
        for python_source_file in files_to_test:
            # Check each of the relevant python sources for unadorned string literals
            unadorned_string_list = find_unadorned_strings.check_file_for_unadorned(python_source_file)
            if unadorned_string_list:
                do_assert = True
                print(f"Found {len(unadorned_string_list):d} "
                      f"unadorned strings in {python_source_file:s}:",
                      file=sys.stderr)
                for unadorned_string in unadorned_string_list:
                    print(unadorned_string[1:], file=sys.stderr)

        self.assertEqual(do_assert, False, u"Found unadorned strings.")


if __name__ == u"__main__":
    unittest.main()
