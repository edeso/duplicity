# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4; encoding:utf-8 -*-
#
# Copyright 2012 Canonical Ltd
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
import platform
import sys
import time

import pexpect

from duplicity import backend
from duplicity import config
from duplicity import util
from testing import DuplicityTestCase
from testing import _runtest_dir
from testing import _top_dir


class CmdError(Exception):
    """Indicates an error running an external command"""

    def __init__(self, code):
        Exception.__init__(self, code)
        self.exit_status = code


class FunctionalTestCase(DuplicityTestCase):
    _setsid_w = None

    @classmethod
    def _check_setsid(cls):
        if cls._setsid_w is not None:
            return
        if platform.platform().startswith("Linux"):
            # setsid behavior differs between distributions.
            # If setsid supports -w ("wait"), use it.
            import subprocess

            try:
                with open("/dev/null", "w") as sink:
                    subprocess.check_call(["setsid", "-w", "ls"], stdout=sink, stderr=sink)
            except subprocess.CalledProcessError:
                cls._setsid_w = False
            else:
                cls._setsid_w = True

    def setUp(self):
        super().setUp()

        self.unpack_testfiles()

        self.class_args = []
        self.backend_url = f"file://{_runtest_dir}/testfiles/output"
        self.last_backup = None
        self.set_environ("PASSPHRASE", self.sign_passphrase)
        self.set_environ("SIGN_PASSPHRASE", self.sign_passphrase)

        backend_inst = backend.get_backend(self.backend_url)
        bl = backend_inst.list()
        if bl:
            backend_inst.delete(backend_inst.list())
        backend_inst.close()
        self._check_setsid()

    def run_duplicity(self, options=None, current_time=None, fail=None, passphrase_input=None, timeout=None):
        """
        Run duplicity binary with given arguments and options
        """

        if options is None:
            options = []
        if passphrase_input is None:
            passphrase_input = []

        # Check all string inputs are unicode -- we will convert to system encoding before running the command
        for item in passphrase_input:
            assert isinstance(item, str), f"item {os.fsdecode(item)} in passphrase_input is not unicode"

        # set python path to be dev directory
        os.environ["PYTHONPATH"] = _top_dir

        cmd_list = []

        # We run under setsid and take input from /dev/null (below) because
        # this way we force a failure if duplicity tries to read from the
        # console unexpectedly (like for gpg password or such).
        if platform.platform().startswith("Linux"):
            cmd_list.extend(["setsid"])
            if self._setsid_w:
                cmd_list.extend(["-w"])

        cmd_list.extend([f"python{sys.version_info.major}.{sys.version_info.minor}"])

        if os.environ.get("RUN_COVERAGE", None):
            cmd_list.extend(["-m", "coverage", "run", "--source=duplicity", "-p"])

        cmd_list.extend([os.path.join(_top_dir, "duplicity", "__main__.py")])
        cmd_list.extend(options)

        if os.environ.get("PYDEVD", None):
            cmd_list.extend(["--pydevd"])

        cmd_list.extend(["-v0"])
        cmd_list.extend(["--no-print-statistics"])
        cmd_list.extend([f"--archive-dir={_runtest_dir}/testfiles/cache"])

        if current_time:
            cmd_list.extend(["--current-time", current_time])

        cmd_list.extend(self.class_args)

        if fail:
            cmd_list.extend(["--fail", fail])

        # convert to string and single quote to avoid shell expansion
        cmdline = " ".join([f"'{x}'" for x in cmd_list])

        if not passphrase_input:
            cmdline += " < /dev/null"

        # Set encoding to filesystem encoding and send to spawn.
        # option -f to shell avoids globbing which breaks selection tests.
        # shell used instead of cmdline to allow setsid to be prepended.
        child = pexpect.spawn(
            "/bin/sh",
            ["-f", "-c", cmdline],
            timeout=None,
            encoding=config.fsencoding,
        )

        for passphrase in passphrase_input:
            child.expect("passphrase.*:")
            child.sendline(passphrase)

        # if the command fails, we need to clear its output
        # so it will terminate cleanly.
        child.expect_exact(pexpect.EOF)
        lines = child.before.splitlines()
        child.wait()
        child.ptyproc.delayafterclose = 0.0
        return_val = child.exitstatus

        if fail:
            self.assertEqual(30, return_val)
        elif return_val:
            print("\n...command:", cmdline, file=sys.stderr)
            print("...cwd:", os.getcwd(), file=sys.stderr)
            print("...output:", file=sys.stderr)
            for line in lines:
                line = line.rstrip()
                if line:
                    print(os.fsdecode(line), file=sys.stderr)
            print("...return_val:", return_val, file=sys.stderr)
            raise CmdError(return_val)
        else:
            for line in lines:
                line = line.rstrip()
                if line:
                    print(os.fsdecode(line), file=sys.stderr)

    def backup(self, type, input_dir, options=None, **kwargs):  # pylint: disable=redefined-builtin
        """Run duplicity backup to default directory"""
        if options is None:
            options = []
        options = [type, input_dir, self.backend_url, "--volsize=1"] + options
        before_files = self.get_backend_files()

        # If a chain ends with time X and the next full chain begins at time X,
        # we may trigger an assert in dup_collections.py.  If needed, sleep to
        # avoid such problems
        now = time.time()
        if self.last_backup == int(now):
            time.sleep(1)

        self.run_duplicity(options=options, **kwargs)
        self.last_backup = int(time.time())

        after_files = self.get_backend_files()
        return after_files - before_files

    def backup_with_failure(
        self, type, input_dir, failure_type, failure_condition, error_code, options=None, PYDEVD=None, **kwargs
    ):
        """
        using _testbackent to trigger certain failure conditions. See backends/_testbackend.py for possible trigger
        """
        self.backend_url = self.backend_url.replace("file", "fortestsonly")  # use _testbackend
        if not options:
            options = [  # lower the retry count to fail faster.
                "--num-ret=2",
                "--backend-ret=3",
            ]

        try:
            env = {failure_type: failure_condition}
            if PYDEVD:  # start debugger in forked duplicity execution. Use for troubleshooting only.
                env["PYDEVD"] = PYDEVD
            with EnvController(**env):
                self.backup(type, input_dir, options, **kwargs)
        except CmdError as e:  # Backup must fail with an exit code != 0
            self.assertEqual(e.exit_status, error_code, str(e))
        else:
            self.fail("Expected CmdError not thrown")

    def restore(self, file_to_restore=None, time=None, options=None, **kwargs):
        if options is None:
            options = []
        assert not os.system(f"rm -rf {_runtest_dir}/testfiles/restore_out")
        options = [
            "restore",
            self.backend_url,
            f"{_runtest_dir}/testfiles/restore_out",
        ] + options
        if file_to_restore:
            options.extend(["--path-to-restore", file_to_restore])
        if time:
            options.extend(["--restore-time", str(time)])
        self.run_duplicity(options=options, **kwargs)

    def verify(self, dirname, file_to_verify=None, time=None, options=None, **kwargs):
        if options is None:
            options = []
        options = ["verify", self.backend_url, dirname] + options
        if file_to_verify:
            options.extend(["--path-to-restore", file_to_verify])
        if time:
            options.extend(["--restore-time", str(time)])
        self.run_duplicity(options=options, **kwargs)

    def cleanup(self, options=None):
        """
        Run duplicity cleanup to default directory
        """
        if options is None:
            options = []
        options = ["cleanup", self.backend_url, "--force"] + options
        self.run_duplicity(options=options)

    def collection_status(self, options=None):
        """
        Run duplicity collection-status to default directory
        """
        if options is None:
            options = []
        options = ["collection-status", self.backend_url] + options
        self.run_duplicity(options=options)

    def get_backend_files(self):
        backend_inst = backend.get_backend(self.backend_url)
        bl = backend_inst.list()
        backend_inst.close()
        return set(bl)

    def make_largefiles(self, count=3, size=2):
        """
        Makes a number of large files in /tmp/testfiles/largefiles that each are
        the specified number of megabytes.
        """
        assert not os.system(f"mkdir {_runtest_dir}/testfiles/largefiles")
        for n in range(count):
            assert not os.system(
                f"dd if=/dev/urandom of={_runtest_dir}/testfiles/largefiles/file{n + 1} "
                f"bs=1024 count={size * 1024} > /dev/null 2>&1"
            )


class EnvController:
    def __init__(self, **kwargs):
        self.env = kwargs

    def __enter__(self):
        for k, v in self.env.items():
            os.environ[k] = v

    def __exit__(self, exc_type, exc_val, exc_tb):
        for k, _ in self.env.items():
            os.unsetenv(k)
            del os.environ[k]
