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
import unittest

import pytest

from duplicity import path
from testing.functional import (
    _runtest_dir,
    CmdError,
    FunctionalTestCase,
)


class FinalTest(FunctionalTestCase):
    """
    Test backup/restore using duplicity binary
    """

    def runtest(self, dirlist, backup_options=None, restore_options=None):
        """Run backup/restore test on directories in dirlist"""
        if backup_options is None:
            backup_options = []
        if restore_options is None:
            restore_options = []

        assert len(dirlist) >= 1

        backup_options += ["--allow-source-mismatch"]

        # Back up directories to local backend
        current_time = 100000
        self.backup("full", dirlist[0], current_time=current_time, options=backup_options)
        for new_dir in dirlist[1:]:
            current_time += 100000
            self.backup("inc", new_dir, current_time=current_time, options=backup_options)

        # Restore each and compare them
        for i in range(len(dirlist)):
            dirname = dirlist[i]
            current_time = 100000 * (i + 1)
            self.restore(time=current_time, options=restore_options)
            self.check_same(dirname, f"{_runtest_dir}/testfiles/restore_out")
            self.verify(dirname, time=current_time, options=restore_options)

    def check_same(self, filename1, filename2):
        """Verify two filenames are the same"""
        path1, path2 = path.Path(filename1), path.Path(filename2)
        assert path1.compare_recursive(path2, verbose=1)

    @pytest.mark.slow
    def test_basic_cycle(self, backup_options=None, restore_options=None, dirlist=None, testfiles=None):
        """Run backup/restore test on basic directories"""
        if backup_options is None:
            backup_options = ["--no-encrypt", "--no-compress"]
        if restore_options is None:
            restore_options = ["--no-encrypt", "--no-compress"]
        if dirlist is None:
            dirlist = [
                f"{_runtest_dir}/testfiles/dir1",
                f"{_runtest_dir}/testfiles/dir2",
                f"{_runtest_dir}/testfiles/dir3",
            ]
        self.runtest(dirlist, backup_options=backup_options, restore_options=restore_options)

        if testfiles is None:
            testfiles = [
                ("symbolic_link", 99999, "dir1"),
                ("directory_to_file", 100100, "dir1"),
                ("directory_to_file", 200100, "dir2"),
                ("largefile", 300000, "dir3"),
            ]
        # Test restoring various sub files
        for filename, time, tfdir in testfiles:
            self.restore(filename, time, options=restore_options)
            self.check_same(f"{_runtest_dir}/testfiles/{tfdir}/{filename}", f"{_runtest_dir}/testfiles/restore_out")
            self.verify(
                f"{_runtest_dir}/testfiles/{tfdir}/{filename}",
                file_to_verify=filename,
                time=time,
                options=restore_options,
            )

    @pytest.mark.slow
    def test_asym_cycle(self):
        """Like test_basic_cycle but use asymmetric encryption and signing"""
        backup_options = ["--encrypt-key", self.encrypt_key1, "--sign-key", self.sign_key]
        restore_options = ["--encrypt-key", self.encrypt_key1, "--sign-key", self.sign_key]
        self.test_basic_cycle(backup_options=backup_options, restore_options=restore_options)

    @pytest.mark.slow
    def test_asym_with_hidden_recipient_cycle(self):
        """Like test_basic_cycle but use asymmetric encryption (hiding key id) and signing"""
        backup_options = ["--hidden-encrypt-key", self.encrypt_key1, "--sign-key", self.sign_key]
        restore_options = ["--hidden-encrypt-key", self.encrypt_key1, "--sign-key", self.sign_key]
        self.test_basic_cycle(backup_options=backup_options, restore_options=restore_options)

    def test_single_regfile(self):
        """Test backing and restoring up a single regular file"""
        self.runtest([f"{_runtest_dir}/testfiles/various_file_types/regular_file"])

    def test_empty_backup(self):
        """Make sure backup works when no files change"""
        self.backup("full", f"{_runtest_dir}/testfiles/empty_dir")
        self.backup("inc", f"{_runtest_dir}/testfiles/empty_dir")

    @pytest.mark.slow
    def test_long_filenames(self):
        """Test backing up a directory with long filenames in it"""
        # Note that some versions of ecryptfs (at least through Ubuntu 11.10)
        # have a bug where they treat the max path segment length as 143
        # instead of 255.  So make sure that these segments don't break that.
        lf_dir = path.Path(f"{_runtest_dir}/testfiles/long_filenames")
        if lf_dir.exists():
            lf_dir.deltree()
        lf_dir.mkdir()
        lf1 = lf_dir.append(
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"  # noqa
        )
        lf1.mkdir()
        lf2 = lf1.append(
            "BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB"  # noqa
        )
        lf2.mkdir()
        lf3 = lf2.append(
            "CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC"  # noqa
        )
        lf3.mkdir()
        lf4 = lf3.append(
            "DDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD"  # noqa
        )
        lf4.touch()
        lf4_1 = lf3.append(
            "SYMLINK--------------------------------------------------------------------------------------------"  # noqa
        )
        os.symlink(
            "SYMLINK-DESTINATION-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------",  # noqa
            lf4_1.name,
        )
        lf4_1.setdata()
        assert lf4_1.issym()
        lf4_2 = lf3.append(
            "DDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD"  # noqa
        )
        fp = lf4_2.open("wb")
        fp.write(b"hello" * 1000)
        assert not fp.close()

        self.runtest(
            [
                f"{_runtest_dir}/testfiles/empty_dir",
                lf_dir.uc_name,
                f"{_runtest_dir}/testfiles/empty_dir",
                lf_dir.uc_name,
            ]
        )

    def test_empty_restore(self):
        """Make sure error raised when restore doesn't match anything"""
        self.backup("full", f"{_runtest_dir}/testfiles/dir1", options=["--allow-source-mismatch"])
        self.assertRaises(CmdError, self.restore, "this_file_does_not_exist")
        self.backup("inc", f"{_runtest_dir}/testfiles/empty_dir", options=["--allow-source-mismatch"])
        self.assertRaises(CmdError, self.restore, "this_file_does_not_exist")

    @pytest.mark.slow
    def test_remove_older_than(self):
        """Test removing old backup chains"""
        first_chain = self.backup(
            "full", f"{_runtest_dir}/testfiles/dir1", current_time=10000, options=["--allow-source-mismatch"]
        )
        first_chain |= self.backup(
            "inc", f"{_runtest_dir}/testfiles/dir2", current_time=20000, options=["--allow-source-mismatch"]
        )
        second_chain = self.backup(
            "full", f"{_runtest_dir}/testfiles/dir1", current_time=30000, options=["--allow-source-mismatch"]
        )
        second_chain |= self.backup(
            "inc", f"{_runtest_dir}/testfiles/dir3", current_time=40000, options=["--allow-source-mismatch"]
        )

        self.assertEqual(self.get_backend_files(), first_chain | second_chain)

        self.run_duplicity(options=["remove-older-than", "35000", "--force", self.backend_url])
        self.assertEqual(self.get_backend_files(), second_chain)

        # Now check to make sure we can't delete only chain
        self.run_duplicity(options=["remove-older-than", "50000", "--force", self.backend_url])
        self.assertEqual(self.get_backend_files(), second_chain)

    def test_piped_password(self):
        """Make sure that prompting for a password works"""
        self.set_environ("PASSPHRASE", None)
        self.backup(
            "full", f"{_runtest_dir}/testfiles/empty_dir", passphrase_input=[self.sign_passphrase, self.sign_passphrase]
        )
        self.restore(passphrase_input=[self.sign_passphrase])

    @pytest.mark.slow
    def test_jsonstat(self):
        """Test cycle with json stats enabled"""
        backup_options = ["--jsonstat"]
        restore_options = ["--jsonstat"]
        self.test_basic_cycle(backup_options=backup_options, restore_options=restore_options)

    def test_jsonstat_missing(self):
        """Make sure collection_status works if one set misses jsonstat"""
        self.backup("full", f"{_runtest_dir}/testfiles/dir1", options=["--jsonstat", "--allow-source-mismatch"])
        self.backup("inc", f"{_runtest_dir}/testfiles/empty_dir", options=["--jsonstat", "--allow-source-mismatch"])
        self.backup("inc", f"{_runtest_dir}/testfiles/dir2", options=["--allow-source-mismatch"])
        self.collection_status(options=["--show-changes-in-set", "-1", "--jsonstat"])

    @pytest.mark.slow
    def test_skip_if_no_change(self):
        """Like test_basic_cycle but use asymmetric encryption and signing"""
        backup_options = ["--skip-if-no-change"]
        restore_options = []
        testfiles = [
            ("symbolic_link", 99999, "dir1"),
            ("directory_to_file", 100100, "dir1"),
            ("directory_to_file", 300100, "dir2"),
            ("largefile", 400000, "dir3"),
        ]
        self.test_basic_cycle(
            backup_options=backup_options,
            restore_options=restore_options,
            dirlist=[
                f"{_runtest_dir}/testfiles/dir1",
                f"{_runtest_dir}/testfiles/dir1",
                f"{_runtest_dir}/testfiles/dir2",
                f"{_runtest_dir}/testfiles/dir3",
            ],
            testfiles=testfiles,
        )


if __name__ == "__main__":
    unittest.main()
