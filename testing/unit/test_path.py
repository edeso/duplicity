# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4; encoding:utf-8 -*-
#
# Copyright 2002 Ben Escoto <ben@emerose.org>
# Copyright 2007 Kenneth Loafman <kenneth@loafman.com>
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

import unittest

from duplicity.path import *  # pylint: disable=unused-wildcard-import,redefined-builtin
from testing import _runtest_dir
from . import UnitTestCase


class PathTest(UnitTestCase):
    """Test basic path functions"""
    def setUp(self):
        super(PathTest, self).setUp()
        self.unpack_testfiles()

    def test_deltree(self):
        """Test deleting a tree"""
        assert not os.system("cp -pR {0}/testfiles/deltree {0}/testfiles/output".format(_runtest_dir).format(_runtest_dir))  # noqa
        p = Path("{0}/testfiles/output".format(_runtest_dir))
        assert p.isdir()
        p.deltree()
        assert not p.type, p.type

#      def test_compare(self):
#         """Test directory comparisons"""
#         assert not os.system("cp -pR /tmp/testfiles/dir1 /tmp/testfiles/output")
#         assert Path("/tmp/testfiles/dir1").compare_recursive(Path("/tmp/testfiles/output"), 1)
#         assert not Path("/tmp/testfiles/dir1").compare_recursive(Path("/tmp/testfiles/dir2"), 1)

    def test_quote(self):
        """Test path quoting"""
        p = Path("hello")
        assert p.quote() == '"hello"'
        assert p.quote("\\") == '"\\\\"', p.quote("\\")
        assert p.quote("$HELLO") == '"\\$HELLO"'

    def test_unquote(self):
        """Test path unquoting"""
        p = Path("foo")  # just to provide unquote function

        def t(s):
            """Run test on string s"""
            quoted_version = p.quote(s)
            unquoted = p.unquote(quoted_version)
            assert unquoted == s, (unquoted, s)

        t("\\")
        t("$HELLO")
        t(" aoe aoe \\ \n`")

    def test_canonical(self):
        """Test getting canonical version of path"""
        c = Path(".").get_canonical()
        assert c == b".", c

        c = Path("//foo/bar/./").get_canonical()
        assert c == b"/foo/bar", c

    def test_compare_verbose(self):
        """Run compare_verbose on a few files"""
        vft = Path("{0}/testfiles/various_file_types".format(_runtest_dir))
        assert vft.compare_verbose(vft)
        reg_file = vft.append("regular_file")
        assert not vft.compare_verbose(reg_file)
        assert reg_file.compare_verbose(reg_file)
        file2 = vft.append("executable")
        assert not file2.compare_verbose(reg_file)
        assert file2.compare_verbose(file2)


if __name__ == "__main__":
    unittest.main()
