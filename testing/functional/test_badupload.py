# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4; encoding:utf-8 -*-
#
# Copyright 2002 Ben Escoto <ben@emerose.org>
# Copyright 2007 Kenneth Loafman <kenneth@loafman.com>
# Copyright 2011 Canonical Ltd
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


import unittest
from duplicity import log

from duplicity.backends._testbackend import BackendErrors as BE

import pytest

from testing import _runtest_dir
from testing.functional import CmdError
from testing.functional import FunctionalTestCase


class BadUploadTest(FunctionalTestCase):
    """
    Test missing volume upload using duplicity binary
    """

    @pytest.mark.slow
    def test_missing_file(self):
        """
        Test basic lost file
        """
        try:
            self.backup("full", f"{_runtest_dir}/testfiles/dir1", options=["--skip-volume=1"])
            self.fail()
        except CmdError as e:
            self.assertEqual(e.exit_status, 56, str(e))
        else:
            self.fail("Expected CmdError not thrown")


class BadUploadTestBackend(FunctionalTestCase):
    """
    Test missing volume upload using duplicity binary
    """

    def _put_fail_volume(self, failure, condition, cmderror):
        """
        _testbackend throw exception on put of certain volume
        """
        self.make_largefiles()
        self.backup_with_failure("full", f"{_runtest_dir}/testfiles/largefiles", failure, condition, cmderror)

    @pytest.mark.slow
    def test_skip_volume_silent(self):
        """
        _testbackend won't put a certain volume
        """
        self.backup_with_failure(
            "full",
            f"{_runtest_dir}/testfiles/dir1",
            BE.SKIP_PUT_SILENT,
            "vol1.difftar",
            log.ErrorCode.backend_verification_failed,
            # PYDEVD="vscode"
        )

    @pytest.mark.slow
    def test_put_fail_volume1(self):
        """
        _testbackend throw exception on put of singel volume
        """
        self.backup_with_failure(
            "full",
            f"{_runtest_dir}/testfiles/dir1",
            BE.FAIL_WITH_EXCEPTION,
            "vol1.difftar",
            log.ErrorCode.backend_error,
        )

    @pytest.mark.slow
    def test_put_fail_volume2(self):
        """
        _testbackend throw exception on put of volume2 of serverals
        """
        self.make_largefiles()
        self.backup_with_failure(
            "full",
            f"{_runtest_dir}/testfiles/largefiles",
            BE.FAIL_WITH_EXCEPTION,
            "vol2.difftar",
            log.ErrorCode.backend_error,
        )


if __name__ == "__main__":
    unittest.main()
