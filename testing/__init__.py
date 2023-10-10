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


import gettext
import os
import platform
import subprocess
import sys
import time
import unittest

from duplicity import backend
from duplicity import config
from duplicity import log
from duplicity import util

gettext.install("duplicity", names=["ngettext"])

log.setup()
util.start_debugger()

_testing_dir = os.path.dirname(os.path.abspath(__file__))
_top_dir = os.path.dirname(_testing_dir)
_overrides_dir = os.path.join(_testing_dir, "overrides")
_bin_dir = os.path.join(_testing_dir, "overrides", "bin")

if platform.system().startswith("Darwin"):
    # Use temp space TMPDIR or from getconf, never /tmp
    _runtest_dir = os.environ.get("TMPDIR", None) or subprocess.check_output(["getconf", "DARWIN_USER_TEMP_DIR"])
    _runtest_dir = os.fsdecode(_runtest_dir).rstrip().rstrip("/")
    if not os.path.exists(_runtest_dir):
        os.makedirs(_runtest_dir)
else:
    # be a little more flexible
    _runtest_dir = os.getenv("TMPDIR", False) or os.getenv("TEMP", False) or "/tmp"

if not os.path.exists(_runtest_dir):
    os.makedirs(_runtest_dir)

# Adjust python path for duplicity and override modules
sys.path = [_overrides_dir, _top_dir, _bin_dir] + sys.path

# Also set PYTHONPATH for any subprocesses
os.environ["PYTHONPATH"] = f"{_overrides_dir}:{_top_dir}:{os.environ.get('PYTHONPATH', '')}"

# And PATH for any subprocesses
os.environ["PATH"] = f"{_bin_dir}:{os.environ.get('PATH', '')}"

# Now set some variables that help standardize test behavior
os.environ["LANG"] = ""
os.environ["GNUPGHOME"] = os.path.join(_testing_dir, "gnupg")

# bzr does not honor perms so fix the perms and avoid annoying error
os.system(f"chmod 700 {os.path.join(_testing_dir, 'gnupg')}")

# Standardize time
os.environ["TZ"] = "US/Central"
time.tzset()


class DuplicityTestCase(unittest.TestCase):
    sign_key = "839E6A2856538CCF"
    sign_passphrase = "test"
    encrypt_key1 = "839E6A2856538CCF"
    encrypt_key2 = "453005CE9B736B2A"

    def setUp(self):
        super().setUp()
        self.savedEnviron = {}
        self.savedConfig = {}

        log.setup()
        log.setverbosity(log.WARNING)
        self.set_config("print_statistics", 0)
        backend.import_backends()

        self.remove_testfiles()
        self.unpack_testfiles()

        self.set_environ("TZ", "UTC")
        time.tzset()
        assert time.tzname[0] == "UTC", f"{time.tzname[0]} should be 'UTC'"

        # Have all file references in tests relative to our runtest dir
        os.chdir(_runtest_dir)

    def tearDown(self):
        for key in self.savedEnviron:
            self._update_env(key, self.savedEnviron[key])

        for key in self.savedConfig:
            setattr(config, key, self.savedConfig[key])

        time.tzset()

        self.remove_testfiles()

        os.chdir(_testing_dir)
        super().tearDown()

    def unpack_testfiles(self):
        assert not os.system(f"rm -rf {_runtest_dir}/testfiles")
        assert not os.system(f"tar xzf {_testing_dir}/testfiles.tar.gz -C {_runtest_dir} > /dev/null 2>&1")
        assert not os.system(f"mkdir {_runtest_dir}/testfiles/output {_runtest_dir}/testfiles/cache")

    def remove_testfiles(self):
        assert not os.system(f"rm -rf {_runtest_dir}/testfiles")

    def _update_env(self, key, value):
        if value is not None:
            os.environ[key] = value
        elif key in os.environ:
            del os.environ[key]

    def set_environ(self, key, value):
        if key not in self.savedEnviron:
            self.savedEnviron[key] = os.environ.get(key)
        self._update_env(key, value)

    def set_config(self, key, value):
        assert hasattr(config, key)
        if key not in self.savedConfig:
            self.savedConfig[key] = getattr(config, key)
        setattr(config, key, value)
