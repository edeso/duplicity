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
from typing import cast

from testing.functional import EnvController

try:
    import unittest.mock as mock
except ImportError:
    import mock
import unittest

import duplicity.backend
import duplicity.backends
import duplicity.backends._testbackend
import duplicity.path
from duplicity.errors import *  # pylint: disable=unused-wildcard-import
from duplicity.backends._testbackend import BackendErrors as BE
from duplicity import config
from . import UnitTestCase


@unittest.skipIf(sys.version_info[:2] < (3, 6), "Skip on bad urllib.parse handling")
class ParsedUrlTest(UnitTestCase):
    """Test the ParsedUrl class"""

    def test_basic(self):
        """Test various url strings"""
        pu = duplicity.backend.ParsedUrl("scp://ben@foo.bar:1234/a/b")
        assert pu.scheme == "scp", pu.scheme
        assert pu.netloc == "ben@foo.bar:1234", pu.netloc
        assert pu.path == "/a/b", pu.path
        assert pu.username == "ben", pu.username
        assert pu.port == 1234, pu.port
        assert pu.hostname == "foo.bar", pu.hostname

        pu = duplicity.backend.ParsedUrl("ftp://foo.bar:1234/")
        assert pu.scheme == "ftp", pu.scheme
        assert pu.netloc == "foo.bar:1234", pu.netloc
        assert pu.path == "/", pu.path
        assert pu.username is None, pu.username
        assert pu.port == 1234, pu.port
        assert pu.hostname == "foo.bar", pu.hostname

        pu = duplicity.backend.ParsedUrl("file:///home")
        assert pu.scheme == "file", pu.scheme
        assert pu.netloc == "", pu.netloc
        assert pu.path == "///home", pu.path
        assert pu.username is None, pu.username
        assert pu.port is None, pu.port

        pu = duplicity.backend.ParsedUrl("file://home")
        assert pu.scheme == "file", pu.scheme
        assert pu.netloc == "", pu.netloc
        assert pu.path == "//home", pu.path
        assert pu.username is None, pu.username
        assert pu.port is None, pu.port

        pu = duplicity.backend.ParsedUrl("ftp://foo@bar:pass@example.com:123/home")
        assert pu.scheme == "ftp", pu.scheme
        assert pu.netloc == "foo@bar:pass@example.com:123", pu.netloc
        assert pu.hostname == "example.com", pu.hostname
        assert pu.path == "/home", pu.path
        assert pu.username == "foo@bar", pu.username
        assert pu.password == "pass", pu.password
        assert pu.port == 123, pu.port

        pu = duplicity.backend.ParsedUrl("ftp://foo%40bar:pass@example.com:123/home")
        assert pu.scheme == "ftp", pu.scheme
        assert pu.netloc == "foo%40bar:pass@example.com:123", pu.netloc
        assert pu.hostname == "example.com", pu.hostname
        assert pu.path == "/home", pu.path
        assert pu.username == "foo@bar", pu.username
        assert pu.password == "pass", pu.password
        assert pu.port == 123, pu.port

        pu = duplicity.backend.ParsedUrl("imap://foo@bar:pass@example.com:123/home")
        assert pu.scheme == "imap", pu.scheme
        assert pu.netloc == "foo@bar:pass@example.com:123", pu.netloc
        assert pu.hostname == "example.com", pu.hostname
        assert pu.path == "/home", pu.path
        assert pu.username == "foo@bar", pu.username
        assert pu.password == "pass", pu.password
        assert pu.port == 123, pu.port

        pu = duplicity.backend.ParsedUrl("imap://foo@bar@example.com:123/home")
        assert pu.scheme == "imap", pu.scheme
        assert pu.netloc == "foo@bar@example.com:123", pu.netloc
        assert pu.hostname == "example.com", pu.hostname
        assert pu.path == "/home", pu.path
        assert pu.username == "foo@bar", pu.username
        assert pu.password is None, pu.password
        assert pu.port == 123, pu.port

        pu = duplicity.backend.ParsedUrl("imap://foo@bar@example.com/home")
        assert pu.scheme == "imap", pu.scheme
        assert pu.netloc == "foo@bar@example.com", pu.netloc
        assert pu.hostname == "example.com", pu.hostname
        assert pu.path == "/home", pu.path
        assert pu.username == "foo@bar", pu.username
        assert pu.password is None, pu.password
        assert pu.port is None, pu.port

        pu = duplicity.backend.ParsedUrl("imap://foo@bar.com@example.com/home")
        assert pu.scheme == "imap", pu.scheme
        assert pu.netloc == "foo@bar.com@example.com", pu.netloc
        assert pu.hostname == "example.com", pu.hostname
        assert pu.path == "/home", pu.path
        assert pu.username == "foo@bar.com", pu.username
        assert pu.password is None, pu.password
        assert pu.port is None, pu.port

        pu = duplicity.backend.ParsedUrl("imap://foo%40bar.com@example.com/home")
        assert pu.scheme == "imap", pu.scheme
        assert pu.netloc == "foo%40bar.com@example.com", pu.netloc
        assert pu.hostname == "example.com", pu.hostname
        assert pu.path == "/home", pu.path
        assert pu.username == "foo@bar.com", pu.username
        assert pu.password is None, pu.password
        assert pu.port is None, pu.port

        pu = duplicity.backend.ParsedUrl("scheme://username:passwor@127.0.0.1:22/path/path")
        assert pu.strip_auth() == "scheme://127.0.0.1:22/path/path"

        pu = duplicity.backend.ParsedUrl("xorriso:///dev/sr0")
        assert pu.scheme == "xorriso", pu.scheme
        assert pu.path == "///dev/sr0", pu.path

        pu = duplicity.backend.ParsedUrl("xorriso:///dev/sr0:/path/on/iso")
        assert pu.scheme == "xorriso", pu.scheme
        assert pu.path == "///dev/sr0:/path/on/iso", pu.path

    def test_errors(self):
        """Test various url errors"""
        self.assertRaises(
            InvalidBackendURL, duplicity.backend.ParsedUrl, "file:path"
        )  # no relative paths for non-netloc schemes
        self.assertRaises(
            UnsupportedBackendScheme,
            duplicity.backend.get_backend,
            "ssh://foo@bar:pass@example.com/home",
        )


class BackendWrapperTest(UnitTestCase):
    def setUp(self):
        super().setUp()
        self.mock = mock.MagicMock(spec=duplicity.backends._testbackend._TestBackend)
        self.backend = duplicity.backend.BackendWrapper(self.mock)
        self.local = mock.MagicMock()
        self.remote = "remote"

    @mock.patch("sys.exit")
    def test_default_error_exit(self, exit_mock):
        self.set_config("num_retries", 1)
        try:
            del self.mock._error_code
        except Exception as e:
            return
        self.mock._put.side_effect = Exception
        self.backend.put(self.local, self.remote)
        exit_mock.assert_called_once_with(50)

    @mock.patch("sys.exit")
    def test_translates_code(self, exit_mock):
        self.set_config("num_retries", 1)
        self.mock._error_code.return_value = 12345
        self.mock._put.side_effect = Exception
        self.backend.put(self.local, self.remote)
        exit_mock.assert_called_once_with(12345)

    @mock.patch("sys.exit")
    def test_uses_exception_code(self, exit_mock):
        self.set_config("num_retries", 1)
        self.mock._error_code.return_value = 12345
        self.mock._put.side_effect = BackendException("error", code=54321)
        self.backend.put(self.local, self.remote)
        exit_mock.assert_called_once_with(54321)

    @mock.patch("sys.exit")
    @mock.patch("time.sleep")  # so no waiting
    def test_cleans_up(self, exit_mock, time_mock):  # pylint: disable=unused-argument
        self.set_config("num_retries", 2)
        self.mock._retry_cleanup.return_value = None
        self.mock._put.side_effect = Exception
        self.backend.put(self.local, self.remote)
        self.mock._retry_cleanup.assert_called_once_with()

    def test_prefer_lists(self):
        self.mock._delete.return_value = None
        self.mock._delete_list.return_value = None
        self.backend.delete([self.remote])
        self.assertEqual(self.mock._delete.call_count, 0)
        self.assertEqual(self.mock._delete_list.call_count, 1)
        try:
            del self.mock._delete_list
        except Exception as e:
            return
        self.backend.delete([self.remote])
        self.assertEqual(self.mock._delete.call_count, 1)

        self.mock._query.return_value = None
        self.mock._query_list.return_value = None
        self.backend.query_info([self.remote])
        self.assertEqual(self.mock._query.call_count, 0)
        self.assertEqual(self.mock._query_list.call_count, 1)
        try:
            del self.mock._query_list
        except Exception as e:
            return
        self.backend.query_info([self.remote])
        self.assertEqual(self.mock._query.call_count, 1)

    @mock.patch("sys.exit")
    @mock.patch("time.sleep")  # so no waiting
    def test_retries(self, exit_mock, time_mock):  # pylint: disable=unused-argument
        self.set_config("num_retries", 2)

        self.mock._get.side_effect = Exception
        self.backend.get(self.remote, self.local)
        self.assertEqual(self.mock._get.call_count, config.num_retries)

        self.mock._put.side_effect = Exception
        self.backend.put(self.local, self.remote)
        self.assertEqual(self.mock._put.call_count, config.num_retries)

        self.mock._list.side_effect = Exception
        self.backend.list()
        self.assertEqual(self.mock._list.call_count, config.num_retries)

        self.mock._delete_list.side_effect = Exception
        self.backend.delete([self.remote])
        self.assertEqual(self.mock._delete_list.call_count, config.num_retries)

        self.mock._query_list.side_effect = Exception
        self.backend.query_info([self.remote])
        self.assertEqual(self.mock._query_list.call_count, config.num_retries)

        try:
            del self.mock._delete_list
        except Exception as e:
            return
        self.mock._delete.side_effect = Exception
        self.backend.delete([self.remote])
        self.assertEqual(self.mock._delete.call_count, config.num_retries)

        try:
            del self.mock._query_list
        except Exception as e:
            return
        self.mock._query.side_effect = Exception
        self.backend.query_info([self.remote])
        self.assertEqual(self.mock._query.call_count, config.num_retries)

        self.mock._move.side_effect = Exception
        self.backend.move(self.local, self.remote)
        self.assertEqual(self.mock._move.call_count, config.num_retries)

    def test_move(self):
        self.mock._move.return_value = True
        self.backend.move(self.local, self.remote)
        self.mock._move.assert_called_once_with(self.local, self.remote)
        self.assertEqual(self.mock._put.call_count, 0)

    def test_move_fallback_false(self):
        self.mock._move.return_value = False
        self.backend.move(self.local, self.remote)
        self.mock._move.assert_called_once_with(self.local, self.remote)
        self.mock._put.assert_called_once_with(self.local, self.remote)
        self.local.delete.assert_called_once_with()

    def test_move_fallback_undefined(self):
        try:
            del self.mock._move
        except Exception as e:
            return
        self.backend.move(self.local, self.remote)
        self.mock._put.assert_called_once_with(self.local, self.remote)
        self.local.delete.assert_called_once_with()

    def test_verify(self):
        self.mock._validate.return_value = True
        assert self.backend.validate(self.remote, 2345) is True

    def test_verify_fallback(self):
        self.mock._validate.return_value = False
        self.mock._query = {self.remote: {"size": 2345}}
        assert self.backend.validate(self.remote, 2345) is False

    def test_verify_generic(self):
        try:
            del self.mock._validate
        except Exception as e:
            return
        ql_resp = mock.MagicMock()
        ql_resp.return_value = {self.remote: {"size": 2345}}
        self.mock._query_list = ql_resp
        assert self.backend.validate(self.remote, 2345)[0] is True

    @mock.patch("time.sleep")
    def test_verify_generic_fail(self, time_mock):  # pylint: disable=unused-argument
        try:
            del self.mock._validate
        except Exception as e:
            pass
        ql_resp = mock.MagicMock()
        ql_resp.return_value = {self.remote: {"size": 111}}
        self.mock._query_list = ql_resp
        assert self.backend.validate(self.remote, 2345)[0] is False

    @mock.patch("time.sleep")
    def test_verify_generic_fail_1(self, time_mock):  # pylint: disable=unused-argument
        try:
            del self.mock._validate
        except Exception as e:
            pass
        ql_resp = mock.MagicMock()
        ql_resp.return_value = {self.remote: {"size": -1}}
        self.mock._query_list = ql_resp
        assert self.backend.validate(self.remote, 2345)[0] is False

    @mock.patch("time.sleep")
    def test_verify_generic_fail_2(self, time_mock):  # pylint: disable=unused-argument
        """
        simulate backend which can't get file size, because of missing functionality
        """
        try:
            del self.mock._validate
        except Exception as e:
            pass
        ql_resp = mock.MagicMock()
        ql_resp.return_value = {self.remote: {"size": None}}
        self.mock._query_list = ql_resp
        assert self.backend.validate(self.remote, 2345)[0] is True

    def test_verify_testbackend(self):
        file = duplicity.path.Path("testfiles/dir1/regular_file")
        test_backend = cast(
            duplicity.backend.BackendWrapper,
            duplicity.backend.get_backend("fortestsonly://testfiles/output"),
        )
        test_backend.put(file)
        assert test_backend.validate(os.fsdecode(file.get_filename()), 75650, file)[0] is True

    def test_verify_testbackend_fail(self):
        file = duplicity.path.Path("testfiles/dir1/regular_file")
        test_backend = cast(
            duplicity.backend.BackendWrapper,
            duplicity.backend.get_backend("fortestsonly://testfiles/output"),
        )
        test_backend.put(file)
        with EnvController(**{BE.LAST_BYTE_MISSING: "regular_file"}):
            assert test_backend.validate(os.fsdecode(file.get_filename()), 75650, file)[0] is False

    def test_close(self):
        self.mock._close.return_value = None
        self.backend.close()
        self.mock._close.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
