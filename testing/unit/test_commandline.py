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

import os
import sys

from duplicity import log
from duplicity import commandline
from duplicity import config
from . import UnitTestCase


class CommandlineTest(UnitTestCase):
    u"""Test the ParsedUrl class"""
    def test_basic(self):
        u"""test backup and restore with explicit commands"""
        commandline.parse_cmdline_options("full foo/bar file://duptest".split())
        assert config.full
        assert config.source_dir.endswith(u"foo/bar")
        assert config.target_url == u"file://duptest"

if __name__ == u"__main__":
    unittest.main()
