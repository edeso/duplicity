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


import glob
import os
import platform
import subprocess
import unittest

import pytest

from testing.functional import _runtest_dir
from testing.functional import FunctionalTestCase


class RestartTest(FunctionalTestCase):
    """
    Test checkpoint/restart using duplicity binary
    """

    def test_basic_checkpoint_restart(self):
        """
        Test basic Checkpoint/Restart
        """
        self.make_largefiles()
        self.backup("full", f"{_runtest_dir}/testfiles/largefiles", fail=1)
        self.backup("full", f"{_runtest_dir}/testfiles/largefiles")
        self.verify(f"{_runtest_dir}/testfiles/largefiles")

    @pytest.mark.slow
    def test_multiple_checkpoint_restart(self):
        """
        Test multiple Checkpoint/Restart
        """
        self.make_largefiles()
        self.backup("full", f"{_runtest_dir}/testfiles/largefiles", fail=1)
        self.backup("full", f"{_runtest_dir}/testfiles/largefiles", fail=2)
        self.backup("full", f"{_runtest_dir}/testfiles/largefiles", fail=3)
        self.backup("full", f"{_runtest_dir}/testfiles/largefiles")
        self.verify(f"{_runtest_dir}/testfiles/largefiles")

    def test_first_volume_failure(self):
        """
        Test restart when no volumes are available on the remote.
        Caused when duplicity fails before the first transfer.
        """
        self.make_largefiles()
        self.backup("full", f"{_runtest_dir}/testfiles/largefiles", fail=1)
        assert not os.system(f"rm {_runtest_dir}/testfiles/output/duplicity-full*difftar*")
        self.backup("full", f"{_runtest_dir}/testfiles/largefiles")
        self.verify(f"{_runtest_dir}/testfiles/largefiles")

    def test_multi_volume_failure(self):
        """
        Test restart when fewer volumes are available on the remote
        than the local manifest has on record.  Caused when duplicity
        fails the last queued transfer(s).
        """
        self.make_largefiles()
        self.backup("full", f"{_runtest_dir}/testfiles/largefiles", fail=3)
        assert not os.system(f"rm {_runtest_dir}/testfiles/output/duplicity-full*vol[23].difftar*")
        self.backup("full", f"{_runtest_dir}/testfiles/largefiles")
        self.verify(f"{_runtest_dir}/testfiles/largefiles")

    def test_restart_encrypt_without_password(self):
        """
        Test that we can successfully restart a encrypt-key-only backup without
        providing a password for it. (Normally, we'd need to decrypt the first
        volume, but there is special code to skip that with an encrypt key.)
        """
        self.set_environ("PASSPHRASE", None)
        self.set_environ("SIGN_PASSPHRASE", None)
        self.make_largefiles()
        enc_opts = ["--encrypt-key", self.encrypt_key1]
        self.backup("full", f"{_runtest_dir}/testfiles/largefiles", options=enc_opts, fail=2)
        self.backup("full", f"{_runtest_dir}/testfiles/largefiles", options=enc_opts)

        self.set_environ("PASSPHRASE", self.sign_passphrase)
        self.verify(f"{_runtest_dir}/testfiles/largefiles")

    def test_restart_sign_and_encrypt(self):
        """
        Test restarting a backup using same key for sign and encrypt
        https://bugs.launchpad.net/duplicity/+bug/946988
        """
        self.make_largefiles()
        enc_opts = ["--sign-key", self.sign_key, "--encrypt-key", self.sign_key]
        self.backup("full", f"{_runtest_dir}/testfiles/largefiles", options=enc_opts, fail=2)
        self.backup("full", f"{_runtest_dir}/testfiles/largefiles", options=enc_opts)
        self.verify(f"{_runtest_dir}/testfiles/largefiles")

    def test_restart_sign_and_hidden_encrypt(self):
        """
        Test restarting a backup using same key for sign and encrypt (hidden key id)
        https://bugs.launchpad.net/duplicity/+bug/946988
        """
        self.make_largefiles()
        enc_opts = ["--sign-key", self.sign_key, "--hidden-encrypt-key", self.sign_key]
        self.backup("full", f"{_runtest_dir}/testfiles/largefiles", options=enc_opts, fail=2)
        self.backup("full", f"{_runtest_dir}/testfiles/largefiles", options=enc_opts)
        self.verify(f"{_runtest_dir}/testfiles/largefiles")

    def test_last_file_missing_in_middle(self):
        """
        Test restart when the last file being backed up is missing on restart.
        Caused when the user deletes a file after a failure.  This test puts
        the file in the middle of the backup, with files following.
        """
        self.make_largefiles()
        self.backup("full", f"{_runtest_dir}/testfiles/largefiles", fail=3)
        assert not os.system(f"rm {_runtest_dir}/testfiles/largefiles/file2")
        self.backup("full", f"{_runtest_dir}/testfiles/largefiles")
        self.verify(f"{_runtest_dir}/testfiles/largefiles")

    @unittest.skipIf(
        platform.machine() in ["ppc64el", "ppc64le"],
        "Skip on ppc64el and ppc64le machines",
    )
    def test_last_file_missing_at_end(self):
        """
        Test restart when the last file being backed up is missing on restart.
        Caused when the user deletes a file after a failure.  This test puts
        the file at the end of the backup, with no files following.
        """
        self.make_largefiles()
        self.backup("full", f"{_runtest_dir}/testfiles/largefiles", fail=6)
        assert not os.system(f"rm {_runtest_dir}/testfiles/largefiles/file3")
        self.backup("full", f"{_runtest_dir}/testfiles/largefiles")
        self.verify(f"{_runtest_dir}/testfiles/largefiles")

    @pytest.mark.slow
    def test_restart_incremental(self):
        """
        Test restarting an incremental backup
        """
        self.make_largefiles()
        self.backup(
            "full",
            f"{_runtest_dir}/testfiles/dir1",
            options=["--allow-source-mismatch"],
        )
        self.backup(
            "inc",
            f"{_runtest_dir}/testfiles/largefiles",
            fail=2,
            options=["--allow-source-mismatch"],
        )
        self.backup(
            "inc",
            f"{_runtest_dir}/testfiles/largefiles",
            options=["--allow-source-mismatch"],
        )
        self.verify(f"{_runtest_dir}/testfiles/largefiles")

    def make_fake_second_volume(self, name):
        """
        Takes a successful backup and pretend that we interrupted a backup
        after two-volumes.  (This is because we want to be able to model
        restarting the second volume and duplicity deletes the last volume
        found because it may have not finished uploading.)
        """
        # First, confirm that we have signs of a successful backup
        self.assertEqual(len(glob.glob(f"{_runtest_dir}/testfiles/output/*.manifest*")), 1)
        self.assertEqual(len(glob.glob(f"{_runtest_dir}/testfiles/output/*.sigtar*")), 1)
        self.assertEqual(len(glob.glob(f"{_runtest_dir}/testfiles/cache/{name}/*")), 2)
        self.assertEqual(len(glob.glob(f"{_runtest_dir}/testfiles/cache/{name}/*.manifest*")), 1)
        self.assertEqual(len(glob.glob(f"{_runtest_dir}/testfiles/cache/{name}/*.sigtar*")), 1)
        # Alright, everything is in order; fake a second interrupted volume
        assert not os.system(f"rm {_runtest_dir}/testfiles/output/*.manifest*")
        assert not os.system(f"rm {_runtest_dir}/testfiles/output/*.sigtar*")
        assert not os.system(f"rm -f {_runtest_dir}/testfiles/output/*.vol[23456789].*")
        assert not os.system(f"rm -f {_runtest_dir}/testfiles/output/*.vol1[^.]+.*")
        self.assertEqual(len(glob.glob(f"{_runtest_dir}/testfiles/output/*.difftar*")), 1)
        assert not os.system(f"rm {_runtest_dir}/testfiles/cache/{name}/*.sigtar*")
        assert not os.system(
            f"cp {_runtest_dir}/testfiles/output/*.difftar* "
            + f"`ls {_runtest_dir}/testfiles/output/*.difftar* | "
            + " sed 's|vol1|vol2|'`"
        )
        assert not os.system(
            f"head -n6 {_runtest_dir}/testfiles/cache/{name}/*.manifest > "
            + f"{_runtest_dir}/testfiles/cache/{name}/"
            + f"`basename {_runtest_dir}/testfiles/cache/{name}/*.manifest`"
            + ".part"
        )
        assert not os.system(f"rm {_runtest_dir}/testfiles/cache/{name}/*.manifest")
        assert not os.system(
            f"""echo 'Volume 2:
    StartingPath   foo
    EndingPath     bar
    Hash SHA1 sha1' >> {_runtest_dir}/testfiles/cache/{name}/*.manifest.part"""
        )

    def test_split_after_small(self):
        """
        If we restart right after a volume that ended with a small
        (one-block) file, make sure we restart in the right place.
        """
        source = f"{_runtest_dir}/testfiles/largefiles"
        assert not os.system(f"mkdir -p {source}")
        assert not os.system(f"echo hello > {source}/file1")
        self.backup("full", source, options=["--name=backup1"])
        # Fake an interruption
        self.make_fake_second_volume("backup1")
        # Add new file
        assert not os.system(f"cp {source}/file1 {source}/newfile")
        # 'restart' the backup
        self.backup("full", source, options=["--name=backup1"])
        # Confirm we actually resumed the previous backup
        self.assertEqual(len(os.listdir(f"{_runtest_dir}/testfiles/output")), 4)
        # Now make sure everything is byte-for-byte the same once restored
        self.restore()
        assert not os.system(f"diff -r {source} {_runtest_dir}/testfiles/restore_out")

    def test_split_after_large(self):
        """
        If we restart right after a volume that ended with a large
        (multi-block) file, make sure we restart in the right place.
        """
        source = f"{_runtest_dir}/testfiles/largefiles"
        self.make_largefiles(count=1, size=1)
        self.backup("full", source, options=["--volsize=5", "--name=backup1"])
        # Fake an interruption
        self.make_fake_second_volume("backup1")
        # Add new file
        assert not os.system(f"cp {source}/file1 {source}/newfile")
        # 'restart' the backup
        self.backup("full", source, options=["--volsize=5", "--name=backup1"])
        # Confirm we actually resumed the previous backup
        self.assertEqual(len(os.listdir(f"{_runtest_dir}/testfiles/output")), 4)
        # Now make sure everything is byte-for-byte the same once restored
        self.restore()
        assert not os.system(f"diff -r %s {_runtest_dir}/testfiles/restore_out" % source)

    def test_split_inside_large(self):
        """
        If we restart right after a volume that ended inside of a large
        (multi-block) file, make sure we restart in the right place.
        """
        source = f"{_runtest_dir}/testfiles/largefiles"
        self.make_largefiles(count=1, size=3)
        self.backup("full", source, options=["--name=backup1"])
        # Fake an interruption
        self.make_fake_second_volume("backup1")
        # 'restart' the backup
        self.backup("full", source, options=["--name=backup1"])
        # Now make sure everything is byte-for-byte the same once restored
        self.restore()
        assert not os.system(f"diff -r {source} {_runtest_dir}/testfiles/restore_out")

    def test_new_file(self):
        """
        If we restart right after a volume, but there are new files that would
        have been backed up earlier in the volume, make sure we don't wig out.
        (Expected result is to ignore new, ealier files, but pick up later
        ones.)
        """
        source = f"{_runtest_dir}/testfiles/largefiles"
        self.make_largefiles(count=1, size=1)
        self.backup("full", source, options=["--name=backup1"])
        # Fake an interruption
        self.make_fake_second_volume("backup1")
        # Add new files, earlier and later in filename sort order
        assert not os.system(f"echo hello > {source}/a")
        assert not os.system(f"echo hello > {source}/z")
        # 'restart' the backup
        self.backup("full", source, options=["--name=backup1"])
        # Now make sure everything is the same once restored, except 'a'
        self.restore()
        assert not os.system(f"test ! -e {_runtest_dir}/testfiles/restore_out/a")
        assert not os.system(f"diff {source}/file1 {_runtest_dir}/testfiles/restore_out/file1")
        assert not os.system(f"diff {source}/z {_runtest_dir}/testfiles/restore_out/z")

    def test_changed_source_dangling_manifest_volume(self):
        """
        If we restart but find remote volumes missing, we can easily end up
        with a manifest that lists "vol1, vol2, vol3, vol2", leaving a dangling
        vol3.  Make sure we can gracefully handle that.  This will only happen
        if the source data changes to be small enough to not create a vol3 on
        restart.
        """
        source = f"{_runtest_dir}/testfiles/largefiles"
        self.make_largefiles(count=5, size=1)
        self.backup("full", source, fail=3)
        # now delete the last volume on remote end and some source files
        assert not os.system(f"rm {_runtest_dir}/testfiles/output/duplicity-full*vol3.difftar*")
        assert not os.system(f"rm {source}/file[2345]")
        assert not os.system(f"echo hello > {source}/z")
        # finish backup
        self.backup("full", source)
        # and verify we can restore
        self.restore()

    def test_changed_source_file_disappears(self):
        """
        Make sure we correctly handle restarting a backup when a file
        disappears when we had been in the middle of backing it up.  It's
        possible that the first chunk of the next file will be skipped unless
        we're careful.
        """
        source = f"{_runtest_dir}/testfiles/largefiles"
        self.make_largefiles(count=1)
        self.backup("full", source, fail=2)
        # now remove starting source data and make sure we add something after
        assert not os.system(f"rm {source}/*")
        assert not os.system(f"echo hello > {source}/z")
        # finish backup
        self.backup("full", source)
        # and verify we can restore
        self.restore()
        assert not os.system(f"diff {source}/z {_runtest_dir}/testfiles/restore_out/z")


# Note that this class duplicates all the tests in RestartTest
class RestartTestWithoutEncryption(RestartTest):
    def setUp(self):
        super().setUp()
        self.class_args.extend(["--no-encryption"])

    def test_no_write_double_snapshot(self):
        """
        Test that restarting a full backup does not write duplicate entries
        into the sigtar, causing problems reading it back in older
        versions.
        https://launchpad.net/bugs/929067
        """
        self.make_largefiles()
        self.backup("full", f"{_runtest_dir}/testfiles/largefiles", fail=2)
        self.backup("full", f"{_runtest_dir}/testfiles/largefiles")
        # Now check sigtar
        sigtars = glob.glob(f"{_runtest_dir}/testfiles/output/duplicity-full*.sigtar.gz")
        self.assertEqual(1, len(sigtars))
        sigtar = sigtars[0]
        output = subprocess.Popen(["tar", "t", f"--file={sigtar}"], stdout=subprocess.PIPE).communicate()[0]
        self.assertEqual(1, output.split(b"\n").count(b"snapshot/"))

    def test_ignore_double_snapshot(self):
        """
        Test that we gracefully ignore double snapshot entries in a signature
        file.  This winds its way through duplicity as a deleted base dir,
        which doesn't make sense and should be ignored.  An older version of
        duplicity accidentally created such files as a result of a restart.
        https://launchpad.net/bugs/929067
        """

        if platform.system().startswith("Linux"):
            tarcmd = "tar"
        elif platform.system().startswith("Darwin"):
            tarcmd = "gtar"
        elif platform.system().endswith("BSD"):
            tarcmd = "gtar"
        else:
            raise Exception(f"Platform {platform.platform()} not supported by tar/gtar.")

        # Intial normal backup
        self.backup("full", f"{_runtest_dir}/testfiles/blocktartest")
        # Create an exact clone of the snapshot folder in the sigtar already.
        # Permissions and mtime must match.
        os.mkdir(f"{_runtest_dir}/testfiles/snapshot", 0o755)
        os.utime(f"{_runtest_dir}/testfiles/snapshot", (1030384548, 1030384548))
        # Adjust the sigtar.gz file to have a bogus second snapshot/ entry
        # at the beginning.
        sigtars = glob.glob(f"{_runtest_dir}/testfiles/output/duplicity-full*.sigtar.gz")
        self.assertEqual(1, len(sigtars))
        sigtar = sigtars[0]
        self.assertEqual(
            0,
            os.system(
                f"{tarcmd} c --file={_runtest_dir}/testfiles/snapshot.sigtar " f"-C {_runtest_dir}/testfiles snapshot"
            ),
        )
        self.assertEqual(0, os.system(f"gunzip -c {sigtar} > {_runtest_dir}/testfiles/full.sigtar"))
        self.assertEqual(
            0,
            os.system(
                f"{tarcmd} A --file={_runtest_dir}/testfiles/snapshot.sigtar " f"{_runtest_dir}/testfiles/full.sigtar"
            ),
        )
        self.assertEqual(0, os.system(f"gzip {_runtest_dir}/testfiles/snapshot.sigtar"))
        os.remove(sigtar)
        os.rename(f"{_runtest_dir}/testfiles/snapshot.sigtar.gz", sigtar)
        # Clear cache so our adjusted sigtar will be sync'd back into the cache
        self.assertEqual(0, os.system(f"rm -r {_runtest_dir}/testfiles/cache"))
        # Try a follow on incremental (which in buggy versions, would create
        # a deleted entry for the base dir)
        self.backup("inc", f"{_runtest_dir}/testfiles/blocktartest")
        self.assertEqual(
            1,
            len(glob.glob(f"{_runtest_dir}/testfiles/output/duplicity-new*.sigtar.gz")),
        )
        # Confirm we can restore it (which in buggy versions, would fail)
        self.restore()


if __name__ == "__main__":
    unittest.main()
