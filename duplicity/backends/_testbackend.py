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
import hashlib
import inspect
import json
import logging
import os
from random import random
import re
import sys
import time

import duplicity.backend
from duplicity import (
    log,
    path,
    progress,
)
from duplicity.errors import BackendException


class BackendErrors:
    # FAIL_WITH_EXCEPTION: set to substring matched by the filename.
    FAIL_WITH_EXCEPTION = "DUP_FAIL_WITH_EXCEPTION"
    # SYSTEM_EXIT: set to substring matched by the filename.
    FAIL_SYSTEM_EXIT = "DUP_FAIL_BY_SYSTEM_EXIT"
    # WAIT_FOR_OTHER_VOLUME: set to json string: ["file_to_delay", "file_wait_for"] (substring match)
    WAIT_FOR_OTHER_VOLUME = "DUP_FAIL_WAIT_FOR_VOLUME"
    # LAST_BYTE_MISSING: set to substring matched by the filename.
    LAST_BYTE_MISSING = "DUP_FAIL_LAST_BYTE_MISSING"
    # SKIP_PUT_SILENT: Don't put file if name contains string
    SKIP_PUT_SILENT = "DUP_FAIL_SKIP_PUT_SILENT"
    # RANDOM_DELAY: max random delay in ms added to command
    DELAY_RANDOM_MS = "DUP_FAIL_DELAY_RANDOM_MS"
    # FIX_DELAY: fix delay in ms added to command
    DELAY_FIX_MS = "DUP_FAIL_DELAY_FIX_MS"


class _TestBackend(duplicity.backend.Backend):
    """Use this backend to test/create certain error situations

    errors get triggered via ENV Vars, see class BackendErrors

    """

    def __init__(self, parsed_url):
        super().__init__(parsed_url)
        log._logger.addHandler(logging.FileHandler("/tmp/testbackend.log"))
        log.Warn("TestBackend is not made for production use!")
        # The URL form "file:MyFile" is not a valid duplicity target.
        if not parsed_url.path.startswith("//"):
            raise BackendException("Bad file:// path syntax.")
        self.remote_pathdir = path.Path(parsed_url.path[2:])
        try:
            os.makedirs(self.remote_pathdir.base)
        except Exception:
            pass

    @staticmethod
    def _fail_with_exception(filename):
        filename = os.fsdecode(filename)
        log.Debug(f"DUB_FAIL: Check if fail on exception for {filename}. Called by {inspect.stack()[2][3]}.")
        if os.getenv(BackendErrors.FAIL_WITH_EXCEPTION) and os.getenv(BackendErrors.FAIL_WITH_EXCEPTION) in filename:
            log.Error(f"DUB_FAIL: Force exception on file {filename}.")
            raise FileNotFoundError(f"TEST: raised exception on {filename} by intention")

    @staticmethod
    def _fail_by_sys_exit(filename):
        filename = os.fsdecode(filename)
        log.Debug(f"DUB_FAIL: Check if do sys.exit(30) for {filename}. Called by {inspect.stack()[2][3]}.")
        if os.getenv(BackendErrors.FAIL_SYSTEM_EXIT) and os.getenv(BackendErrors.FAIL_SYSTEM_EXIT) in filename:
            log.Error(f"DUB_FAIL: Force sys.exit(30) on file {filename}.")
            time.sleep(1)  # otherwise log message doesn't get printed.
            sys.exit(30)

    def _wait_for_other_volume(self, filename):
        filename = os.fsdecode(filename)
        log.Debug(f"DUB_FAIL: Check if action on {filename} shoud be delayed. Called by {inspect.stack()[2][3]}.")
        env = os.getenv(BackendErrors.WAIT_FOR_OTHER_VOLUME)
        if not env:
            return  # skip if env not set
        file_stop, file_waitfor = json.loads(env)
        timestamp = re.match(r".*\.(\d{8}T\d{6}[-+0-9:Z]*)\..*", filename).group(1)
        file_waitfor_glob = f"{os.fsdecode(self.remote_pathdir.get_canonical())}/*{timestamp}*{file_waitfor}*"
        if file_stop in filename:
            while not glob.glob(file_waitfor_glob):
                log.Error(f"DUB_FAIL: Waiting for file matiching {file_waitfor_glob}.")
                time.sleep(1)
            log.Warn(f"DUB_FAIL: {filename} written after {glob.glob(file_waitfor_glob)}")

    def _remove_last_byte(self, filename):
        filename = os.fsdecode(filename)
        log.Debug(f"DUB_FAIL: Check if {filename} shoud be truncated. Called by {inspect.stack()[2][3]}.")
        if os.getenv(BackendErrors.LAST_BYTE_MISSING) and os.getenv(BackendErrors.LAST_BYTE_MISSING) in filename:
            log.Error(f"DUB_FAIL: removing last byte from {filename}")
            with open(self.remote_pathdir.append(filename).get_canonical(), "ab") as remote_file:
                remote_file.seek(-1, os.SEEK_END)
                remote_file.truncate()

    @staticmethod
    def _skip_put_silent(filename):
        """
        retrun true if file should be skipped silently
        """
        filename = os.fsdecode(filename)
        log.Debug(f"DUB_FAIL: Check if {filename} should be skipped. Called by {inspect.stack()[2][3]}.")
        if os.getenv(BackendErrors.SKIP_PUT_SILENT) and os.getenv(BackendErrors.SKIP_PUT_SILENT) in filename:
            log.Error(f"DUB_FAIL: {filename} skipped silent.")
            return True
        return False

    @staticmethod
    def _delay():
        """
        sleep a random amount of milliseconds if ENV set
        """
        log.Debug("DUB_FAIL: Check if action should be delayed.")
        wait = 0
        if os.getenv(BackendErrors.DELAY_RANDOM_MS):
            wait += random() * float(os.getenv(BackendErrors.DELAY_RANDOM_MS)) / 1000  # type: ignore
        if os.getenv(BackendErrors.DELAY_FIX_MS):
            wait += float(os.getenv(BackendErrors.DELAY_FIX_MS)) / 1000  # type: ignore
        if wait > 0:
            log.Warn(f"DUB_FAIL: wait for {wait} sec.")
            time.sleep(wait)

    def _move(self, source_path, remote_filename):
        self._fail_with_exception(remote_filename)
        self._fail_by_sys_exit(remote_filename)
        self._wait_for_other_volume(remote_filename)
        self._delay()
        target_path = self.remote_pathdir.append(remote_filename)
        try:
            source_path.rename(target_path)
            return True
        except OSError:
            return False

    def _put(self, source_path, remote_filename):
        self._fail_with_exception(remote_filename)
        self._wait_for_other_volume(remote_filename)
        self._delay()
        if self._skip_put_silent(remote_filename):
            return
        target_path = self.remote_pathdir.append(remote_filename)
        source_path.setdata()
        source_size = source_path.getsize()
        progress.report_transfer(0, source_size)
        target_path.writefileobj(source_path.open("rb"))

        self._fail_by_sys_exit(remote_filename)  # fail after file is transferred
        self._remove_last_byte(remote_filename)

        progress.report_transfer(source_size, source_size)

    def _get(self, filename, local_path):
        self._fail_with_exception(filename)
        self._fail_by_sys_exit(filename)
        self._delay()
        source_path = self.remote_pathdir.append(filename)
        local_path.writefileobj(source_path.open("rb"))

    def _list(self):
        return self.remote_pathdir.listdir()

    def _validate(self, remote_filename, size, source_path=None, **kwargs):
        # poc to show that validate can do additional things.
        self._delay()

        self._remove_last_byte(remote_filename)

        results_str = []
        results_bool = []
        try:
            if source_path:
                target_path = self.remote_pathdir.append(remote_filename)
                target_hash = self.__hash_fileobj(target_path.open())
                source_hash = self.__hash_fileobj(source_path.open())
                if target_hash == source_hash:
                    results_str.append(f"file hash {target_hash} matches")
                    results_bool.append(True)
                else:
                    results_str.append(f"expected hash {source_hash} doesn't match file hash {target_hash}")
                    results_bool.append(False)
            if size == self._query(remote_filename)["size"]:
                results_str.append(f"file size {size}")
                results_bool.append(True)
            else:
                results_str.append(
                    f'expected size {size} and file size {self._query(remote_filename)["size"]} don\'t match'
                )
                results_bool.append(False)
        except FileNotFoundError as e:
            results_bool.append(False)
            results_str.append(f"FileNotFoundError: {e}")
        except Exception as e:
            log.FatalError(
                _("Unexpected exception while validate %s.") % os.fsdecode(remote_filename),
                log.ErrorCode.backend_validation_failed,
                extra=f"Exception: {e}",
            )
        return (all(results_bool), ", ".join(results_str))

    def _delete(self, filename):
        self._fail_with_exception(filename)
        self._fail_by_sys_exit(filename)
        self._delay()
        self.remote_pathdir.append(filename).delete()

    def _delete_list(self, filenames):
        for filename in filenames:
            self._fail_with_exception(filename)
            self._fail_by_sys_exit(filename)
            self._delay()
            self.remote_pathdir.append(filename).delete()

    def _query(self, filename):
        self._fail_with_exception(filename)
        self._delay()
        self._fail_by_sys_exit(filename)
        target_file = self.remote_pathdir.append(filename)
        target_file.setdata()
        size = target_file.getsize() if target_file.exists() else -1
        return {"size": size}

    def _query_list(self, filename_list):
        return {x: self._query(x) for x in filename_list}

    def _retry_cleanup(self):
        pass

    def _close(self):
        pass

    def _error_code(self, operation, e):  # pylint: disable=unused-argument
        return log.ErrorCode.backend_error

    def __hash_file(self, filename):
        self.__hash_fileobj(open(filename, "rb"))

    def __hash_fileobj(self, fileobj):
        # TODO: Remove when py38 goes EOL
        if sys.version_info[:2] == (3, 8):
            h = hashlib.sha1()
        else:
            h = hashlib.sha1(usedforsecurity=False)
        # loop till the end of the file
        chunk = 0
        while chunk != b"":
            # read only 1024 bytes at a time
            chunk = fileobj.read(1024)
            h.update(chunk)
        fileobj.close()
        # return the hex representation of digest
        return h.hexdigest()


duplicity.backend.register_backend("fortestsonly", _TestBackend)
