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


import pexpect
import pytest
import os
from duplicity import log

from duplicity.backends._testbackend import BackendErrors as BE

from testing import _runtest_dir
from . import CmdError, FunctionalTestCase, EnvController

# os.environ['PYDEVD'] = "vscode"


class ConcurrencyFullLivecycleTest(FunctionalTestCase):
    def test_verify_compare_data(self):
        """Test that verify works in the basic case when the --compare-data option is used"""
        self.make_largefiles()
        self.backup("full", f"{_runtest_dir}/testfiles/largefiles", options=["--concurrency=3"])

        # Test verify for the file with --compare-data
        self.verify(
            f"{_runtest_dir}/testfiles/largefiles",
            options=["--compare-data"],
        )


class ConcurrencyFailTest(FunctionalTestCase):
    def setUp(self):
        super().setUp()
        self.backend_url = self.backend_url.replace("file", "fortestsonly")  # use _testbackend

    @pytest.mark.slow
    def test_put_fail_volume(self):
        """
        _testbackend won't put a certain volume
        """
        self.make_largefiles()
        options = [
            "--num-ret=2",
            "--backend-ret=3",
            "--concurrency=3",
        ]
        self.backup_with_failure(
            "full",
            f"{_runtest_dir}/testfiles/largefiles",
            BE.FAIL_WITH_EXCEPTION,
            "vol2.difftar",
            log.ErrorCode.backend_error,
            options=options,
            # PYDEVD="vscode",
            timeout=60,
        )

    @pytest.mark.slow
    def test_put_fail_sys_exit(self):
        """
        _testbackend exit on volume
        """
        self.make_largefiles()
        options = [
            "--num-ret=2",
            "--backend-ret=3",
            "--concurrency=3",
        ]
        self.backup_with_failure(
            "full",
            f"{_runtest_dir}/testfiles/largefiles",
            BE.FAIL_SYSTEM_EXIT,
            "vol2.difftar",
            log.ErrorCode.exception,
            options=options,
            # PYDEVD="vscode",
            timeout=60,
        )

    @pytest.mark.slow
    def test_out_of_order_volume(self):
        self.make_largefiles()
        options = [
            "--num-ret=2",
            "--backend-ret=3",
            "--concurrency=3",
            "--log-timestamp",
            "--verbosity",
            "i",
        ]
        with EnvController(**{BE.WAIT_FOR_OTHER_VOLUME: '["vol2.difftar", "vol7.difftar"]'}):
            try:
                transferred_files = self.backup("full", f"{_runtest_dir}/testfiles/largefiles", options, timeout=60)
            except pexpect.exceptions.TIMEOUT:
                self.fail(
                    "Concurrent backup was not able to terminate itself. (Mostlikely caused by a hanging thread.)"
                )
            except CmdError as e:  # Backup muse fail with an exit code != 0
                self.assertEqual(e.exit_status, 0, f"Backup must not fail, because out of order execution. {e}")

    @pytest.mark.slow
    def test_wrong_size(self):
        self.make_largefiles()
        options = [
            "--num-ret=2",
            "--backend-ret=3",
            "--concurrency=3",
            "--log-timestamp",
            "--verbosity",
            "i",
        ]
        with EnvController(**{BE.LAST_BYTE_MISSING: "vol3.difftar"}):
            try:
                transferred_files = self.backup("full", f"{_runtest_dir}/testfiles/largefiles", options, timeout=60)
            except pexpect.exceptions.TIMEOUT:
                self.fail(
                    "Concurrent backup was not able to terminate itself. (Mostlikely caused by a hanging thread.)"
                )
            except CmdError as e:  # Backup muse fail with an exit code != 0
                self.assertEqual(
                    e.exit_status,
                    log.ErrorCode.backend_validation_failed,
                    f"Backup must not fail, because out of order execution. {e}",
                )

    @pytest.mark.slow
    def test_continue_after_missing_volume(self):
        """
        test recovery after a volume in the sequence is missing.
        vol1, vol3-vol7 should be successful trasferred but val2 fails late.
        """
        # os.environ['PYDEVD'] = ""
        self.make_largefiles()
        options = [
            "--num-ret=2",
            "--backend-ret=3",
            "--concurrency=3",
            "--log-timestamp",
            "--verbosity",
            "i",
        ]
        with EnvController(
            **{BE.WAIT_FOR_OTHER_VOLUME: '["vol2.difftar", "vol5.difftar"]', BE.SKIP_PUT_SILENT: "vol2.difftar"}
        ):
            try:
                transferred_files = self.backup("full", f"{_runtest_dir}/testfiles/largefiles", options, timeout=60)
            except pexpect.exceptions.TIMEOUT:
                self.fail(
                    "Concurrent backup was not able to terminate itself. (Mostlikely caused by a hanging thread.)"
                )
            except CmdError as e:  # Backup muse fail with an exit code != 0
                self.assertNotEqual(e.exit_status, 0, f"Backup is expected to fail as a volume is missing. {e}")

        try:
            transferred_files = self.backup("full", f"{_runtest_dir}/testfiles/largefiles", options, timeout=60)
        except pexpect.exceptions.TIMEOUT:
            self.fail("Concurrent backup was not able to terminate itself. (Mostlikely caused by a hanging thread.)")
        except CmdError as e:  # Backup muse fail with an exit code != 0
            self.assertEqual(e.exit_status, 0, f"Backup must not fail, because out of order execution. {e}")

        # Test verify for the file with --compare-data
        self.verify(
            f"{_runtest_dir}/testfiles/largefiles",
            options=["--compare-data"],
        )
