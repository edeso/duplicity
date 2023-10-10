# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4; encoding:utf-8 -*-
#
# Copyright 2014 Canonical Ltd
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


import io
import os
import unittest

import duplicity.backend
from duplicity import log
from duplicity import path
from duplicity import util
from duplicity.errors import BackendException
from testing import _runtest_dir
from . import UnitTestCase


class BackendInstanceBase(UnitTestCase):
    def setUp(self):
        UnitTestCase.setUp(self)
        assert not os.system(f"rm -rf {_runtest_dir}/testfiles")
        os.makedirs(f"{_runtest_dir}/testfiles")
        self.backend = None
        self.local = path.Path(f"{_runtest_dir}/testfiles/local")
        self.local.writefileobj(io.BytesIO(b"hello"))

    def tearDown(self):
        assert not os.system(f"rm -rf {_runtest_dir}/testfiles")
        if self.backend is None:
            return
        if hasattr(self.backend, "_close"):
            self.backend._close()

    def test_get(self):
        if self.backend is None:
            return
        self.backend._put(self.local, b"file-a")
        getfile = path.Path(f"{_runtest_dir}/testfiles/getfile")
        self.backend._get(b"file-a", getfile)
        self.assertTrue(self.local.compare_data(getfile))

    def test_list(self):
        if self.backend is None:
            return
        self.backend._put(self.local, b"file-a")
        self.backend._put(self.local, b"file-b")
        # It's OK for backends to create files as a side effect of put (e.g.
        # the par2 backend does), so only check that at least a and b exist.
        self.assertTrue(b"file-a" in self.backend._list())
        self.assertTrue(b"file-b" in self.backend._list())

    def test_delete(self):
        if self.backend is None:
            return
        if not hasattr(self.backend, "_delete"):
            self.assertTrue(hasattr(self.backend, "_delete_list"))
            return
        self.backend._put(self.local, b"file-a")
        self.backend._put(self.local, b"file-b")
        self.backend._delete(b"file-a")
        self.assertFalse(b"file-a" in self.backend._list())
        self.assertTrue(b"file-b" in self.backend._list())

    def test_delete_clean(self):
        if self.backend is None:
            return
        if not hasattr(self.backend, "_delete"):
            self.assertTrue(hasattr(self.backend, "_delete_list"))
            return
        self.backend._put(self.local, b"file-a")
        self.backend._delete(b"file-a")
        self.assertFalse(b"file-a" in self.backend._list())

    def test_delete_missing(self):
        if self.backend is None:
            return
        if not hasattr(self.backend, "_delete"):
            self.assertTrue(hasattr(self.backend, "_delete_list"))
            return
        # Backends can either silently ignore this, or throw an error
        # that gives log.ErrorCode.backend_not_found.
        try:
            self.backend._delete(b"file-a")
        except BackendException as e:
            pass  # Something went wrong, but it was an 'expected' something
        except Exception as e:
            code = duplicity.backend._get_code_from_exception(self.backend, "delete", e)
            self.assertEqual(code, log.ErrorCode.backend_not_found)

    def test_delete_list(self):
        if self.backend is None:
            return
        if not hasattr(self.backend, "_delete_list"):
            self.assertTrue(hasattr(self.backend, "_delete"))
            return
        self.backend._put(self.local, b"file-a")
        self.backend._put(self.local, b"file-b")
        self.backend._put(self.local, b"file-c")
        self.backend._delete_list([b"file-a", b"d", b"file-c"])
        files = self.backend._list()
        self.assertFalse(b"file-a" in files, files)
        self.assertTrue(b"file-b" in files, files)
        self.assertFalse(b"file-c" in files, files)

    def test_move(self):
        if self.backend is None:
            return
        if not hasattr(self.backend, "_move"):
            return

        copy = path.Path(f"{_runtest_dir}/testfiles/copy")
        self.local.copy(copy)

        self.backend._move(self.local, b"file-a")
        self.assertTrue(b"file-a" in self.backend._list())
        self.assertFalse(self.local.exists())

        getfile = path.Path(f"{_runtest_dir}/testfiles/getfile")
        self.backend._get(b"file-a", getfile)
        self.assertTrue(copy.compare_data(getfile))

    def test_query_exists(self):
        if self.backend is None:
            return
        if not hasattr(self.backend, "_query"):
            return
        self.backend._put(self.local, b"file-a")
        info = self.backend._query(b"file-a")
        self.assertEqual(info["size"], self.local.getsize())

    def test_query_missing(self):
        if self.backend is None:
            return
        if not hasattr(self.backend, "_query"):
            return
        # Backends can either return -1 themselves, or throw an error
        # that gives log.ErrorCode.backend_not_found.
        try:
            info = self.backend._query(b"file-a")
        except BackendException as e:  # pylint:
            pass  # Something went wrong, but it was an 'expected' something
        except Exception as e:
            code = duplicity.backend._get_code_from_exception(self.backend, "query", e)
            self.assertEqual(code, log.ErrorCode.backend_not_found)
        else:
            self.assertEqual(info["size"], -1)

    def test_query_list(self):
        if self.backend is None:
            return
        if not hasattr(self.backend, "_query_list"):
            return
        self.backend._put(self.local, b"file-a")
        self.backend._put(self.local, b"file-c")
        info = self.backend._query_list([b"file-a", b"file-b"])
        self.assertEqual(info[b"file-a"]["size"], self.local.getsize())
        self.assertEqual(info[b"file-b"]["size"], -1)
        self.assertFalse(b"file-c" in info)


class LocalBackendTest(BackendInstanceBase):
    def setUp(self):
        super().setUp()
        url = f"file://{_runtest_dir}/testfiles/output"
        self.backend = duplicity.backend.get_backend_object(url)
        self.assertEqual(self.backend.__class__.__name__, "LocalBackend")


# TODO: Add par2-specific tests here, to confirm that we can recover
@unittest.skipIf(not util.which("par2"), "par2 not installed")
class Par2BackendTest(BackendInstanceBase):
    def setUp(self):
        super().setUp()
        url = f"par2+file://{_runtest_dir}/testfiles/output"
        self.backend = duplicity.backend.get_backend_object(url)
        self.assertEqual(self.backend.__class__.__name__, "Par2Backend")


# TODO: Fix so localhost is not required.  Fails on LP and GitLab
# class RsyncBackendTest(BackendInstanceBase):
#     def setUp(self):
#         super().setUp()
#         os.makedirs('{0}/testfiles/output')  # rsync needs it to exist first
#         url = 'rsync://localhost:2222//%s/{0}/testfiles/output' % os.getcwd()
#         self.backend = duplicity.backend.get_backend_object(url)
#         self.assertEqual(self.backend.__class__.__name__, 'RsyncBackend')


class TahoeBackendTest(BackendInstanceBase):
    def setUp(self):
        super().setUp()
        os.makedirs(f"{_runtest_dir}/testfiles/output")
        url = f"tahoe://{_runtest_dir}/testfiles/output"
        self.backend = duplicity.backend.get_backend_object(url)
        self.assertEqual(self.backend.__class__.__name__, "TAHOEBackend")


# TODO: Modernize hsi backend stub
#  class HSIBackendTest(BackendInstanceBase):
#      def setUp(self):
#          super().setUp()
#          os.makedirs('{0}/testfiles/output')
#          # hostname is ignored...  Seemingly on purpose
#          url = 'hsi://hostname%s/{0}/testfiles/output' % os.getcwd()
#          self.backend = duplicity.backend.get_backend_object(url)
#          self.assertEqual(self.backend.__class__.__name__, 'HSIBackend')


@unittest.skipIf(not util.which("lftp"), "lftp not installed")
class FTPBackendTest(BackendInstanceBase):
    def setUp(self):
        super().setUp()
        os.makedirs(f"{_runtest_dir}/testfiles/output")
        url = f"ftp://user:pass@hostname/{_runtest_dir}/testfiles/output"
        self.backend = duplicity.backend.get_backend_object(url)
        self.assertEqual(self.backend.__class__.__name__, "LFTPBackend")


@unittest.skipIf(not util.which("lftp"), "lftp not installed")
class FTPSBackendTest(BackendInstanceBase):
    def setUp(self):
        super().setUp()
        os.makedirs(f"{_runtest_dir}/testfiles/output")
        url = f"ftps://user:pass@hostname/{_runtest_dir}/testfiles/output"
        self.backend = duplicity.backend.get_backend_object(url)
        self.assertEqual(self.backend.__class__.__name__, "LFTPBackend")


@unittest.skipIf(not util.which("rclone"), "rclone not installed")
class RCloneBackendTest(BackendInstanceBase):
    def setUp(self):
        super().setUp()
        # make sure rclone config exists
        assert not os.system("rclone config touch")
        # add a duptest local config
        try:
            assert not os.system("rclone config create duptest local local=true --non-interactive")
            self.delete_config = True
        except Exception as e:
            self.delete_config = False
        os.makedirs(f"{_runtest_dir}/testfiles/output")
        url = f"rclone://duptest:/%s/{_runtest_dir}/testfiles/output"
        self.backend = duplicity.backend.get_backend_object(url)
        self.assertEqual(self.backend.__class__.__name__, "RcloneBackend")

    def tearDown(self):
        super().tearDown()
        if self.delete_config:
            assert not os.system("rclone config delete duptest")
