# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4; encoding:utf-8 -*-
#
# Copyright 2002 Ben Escoto <ben@emerose.org>
# Copyright 2007 Kenneth Loafman <kenneth@loafman.com>
# Copyright 2008 Michael Terry <mike@mterry.name>
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

"""
Log various messages depending on verbosity level.
"""

import logging
import os
import sys

# Logging levels are translated in cli_util:check_verbosity().
# Alphabetic levels are translated directly to logging levels.
# Numeric levels are reverse translated to logging levels.
# NOTICE is added between INFO and WARNONG.
# CRITICAL is currently unused.

from logging import (
    DEBUG,
    INFO,
    WARNING,
    ERROR,
    CRITICAL,
)

NOTICE = INFO + 5
MIN = CRITICAL  # min logging
MAX = DEBUG  # max logging

PREFIX = ""  # process log prefix

_logger = None
_log_timestamp = False


def Log(s, verb_level, code=1, extra=None, force_print=False, transfer_progress=False):
    """
    Write s to stderr if verbosity level low enough
    """
    global _logger
    if extra:
        controlLine = f"{int(code)} {extra}"
    else:
        controlLine = f"{int(code)}"
    if not s:
        s = ""  # If None is passed, standard logging would render it as 'None'

    if force_print:
        initial_level = _logger.getEffectiveLevel()
        _logger.setLevel(MAX)

    # If all the backends kindly gave us unicode, we could enable this next
    # assert line.  As it is, we'll attempt to convert s to unicode if we
    # are handed bytes.  One day we should update the backends.
    # assert isinstance(s, unicode)
    if not isinstance(s, str):
        s = s.decode("utf8", "replace")

    s = PREFIX + s

    _logger.log(
        verb_level,
        s,
        extra={
            "levelName": logging.getLevelName(verb_level),
            "controlLine": controlLine,
            "transferProgress": transfer_progress,
        },
    )

    if force_print:
        _logger.setLevel(initial_level)


def Debug(s):
    """
    Shortcut used for debug message (verbosity 9).
    """
    Log(s, DEBUG)


class InfoCode(object):
    """
    Enumeration class to hold info code values.
    These values should never change, as frontends rely upon them.
    Don't use 0 or negative numbers.
    """

    generic = 1
    progress = 2
    collection_status = 3
    diff_file_new = 4
    diff_file_changed = 5
    diff_file_deleted = 6
    patch_file_writing = 7
    patch_file_patching = 8
    # file_list = 9 # 9 isn't used anymore.  It corresponds to an older syntax for listing files
    file_list = 10
    synchronous_upload_begin = 11
    asynchronous_upload_begin = 12
    synchronous_upload_done = 13
    asynchronous_upload_done = 14
    skipping_socket = 15
    upload_progress = 16


def Info(s, code=InfoCode.generic, extra=None):
    """
    Shortcut used for info messages (verbosity INFO).
    """
    Log(s, INFO, code, extra)


def Notice(s):
    """
    Shortcut used for notice messages (verbosity 3, the default).
    """
    Log(s, NOTICE)


class WarningCode(object):
    """
    Enumeration class to hold warning code values.
    These values should never change, as frontends rely upon them.
    Don't use 0 or negative numbers.
    """

    generic = 1
    orphaned_sig = 2
    unnecessary_sig = 3
    unmatched_sig = 4
    incomplete_backup = 5
    orphaned_backup = 6
    ftp_ncftp_v320 = 7  # moved from error
    cannot_iterate = 8
    cannot_stat = 9
    cannot_read = 10
    no_sig_for_time = 11
    cannot_process = 12
    process_skipped = 13


def Warn(s, code=WarningCode.generic, extra=None):
    """
    Shortcut used for warning messages (verbosity 2)
    """
    Log(s, WARNING, code, extra)


class ErrorCode(object):
    """
    Enumeration class to hold error code values.
    These values should never change, as frontends rely upon them.
    Don't use 0 or negative numbers.  This code is returned by duplicity
    to indicate which error occurred via both exit code and log.
    """

    generic = 1  # Don't use if possible, please create a new code and use it
    command_line = 2
    hostname_mismatch = 3
    no_manifests = 4
    mismatched_manifests = 5
    unreadable_manifests = 6
    cant_open_filelist = 7
    bad_url = 8
    bad_archive_dir = 9
    deprecated_option = 10
    restore_path_exists = 11
    verify_dir_doesnt_exist = 12
    backup_dir_doesnt_exist = 13
    file_prefix_error = 14
    globbing_error = 15
    redundant_inclusion = 16
    inc_without_sigs = 17
    no_sigs = 18
    restore_path_not_found = 19
    no_restore_files = 20
    mismatched_hash = 21
    unsigned_volume = 22
    user_error = 23
    # boto_old_style = 24 # deprecated
    # boto_lib_too_old = 25 # deprecated
    # boto_calling_format = 26 # deprecated
    ftp_ncftp_missing = 27
    ftp_ncftp_too_old = 28
    # ftp_ncftp_v320 = 29 # moved to warning
    exception = 30
    gpg_failed = 31
    # s3_bucket_not_style = 32 # deprecated
    not_implemented = 33
    get_freespace_failed = 34
    not_enough_freespace = 35
    get_ulimit_failed = 36
    maxopen_too_low = 37
    connection_failed = 38
    restart_file_not_found = 39
    gio_not_available = 40
    source_path_mismatch = 42  # 41 is reserved for par2
    ftps_lftp_missing = 43
    volume_wrong_size = 44
    enryption_mismatch = 45
    pythonoptimize_set = 46

    dpbx_nologin = 47

    bad_request = 48
    s3_kms_no_id = 49

    # 50-> 69 reserved for backend errors
    backend_error = 50
    backend_permission_denied = 51
    backend_not_found = 52
    backend_no_space = 53
    backend_command_error = 54
    backend_code_error = 55
    backend_validation_failed = 56

    # file selection filter mode errors
    redundant_filter = 70
    trailing_filter = 71
    absolute_files_from = 72
    empty_files_from = 73

    # gpg key errors
    bad_sign_key = 80
    bad_encrypt_key = 81
    bad_hidden_encrypt_key = 82

    # Reserve 126 because it is used as an error code for pkexec
    # Reserve 127 because it is used as an error code for pkexec
    # Reserve 255 because it is used as an error code for gksu


def Error(s, code=ErrorCode.generic, extra=None):
    """
    Write error message.
    """
    Log(s, ERROR, code, extra)


class OutFilter(logging.Filter):
    """
    Filter that only allows warning or less important messages.
    """

    def filter(self, record):
        return record.msg and record.levelno <= WARNING


class ErrFilter(logging.Filter):
    """
    Filter that only allows messages more important than warnings.
    """

    def filter(self, record):
        return record.msg and record.levelno > WARNING


class DetailFormatter(logging.Formatter):
    """
    Formatter that creates messages in a syntax somewhat like syslog.
    """

    def __init__(self):
        # 'message' will be appended by format()
        # Note that we use our own, custom-created 'levelName' instead of the
        # standard 'levelname'.  This is because the standard 'levelname' can
        # be adjusted by any library anywhere in our stack without us knowing.
        # But we control 'levelName'.
        logging.Formatter.__init__(self, "%(asctime)s %(levelName)s %(message)s")

    def format(self, record):
        s = logging.Formatter.format(self, record)
        return s


class MachineFormatter(logging.Formatter):
    """
    Formatter that creates messages in a syntax easily consumable by other processes.
    """

    def __init__(self):
        # 'message' will be appended by format()
        # Note that we use our own, custom-created 'levelName' instead of the
        # standard 'levelname'.  This is because the standard 'levelname' can
        # be adjusted by any library anywhere in our stack without us knowing.
        # But we control 'levelName'.
        logging.Formatter.__init__(self, "%(levelName)s %(controlLine)s")

    def format(self, record):
        s = logging.Formatter.format(self, record)

        # Add user-text hint of 'message' back in, with each line prefixed by a
        # dot, so consumers know it's not part of 'controlLine'
        if record.message:
            s += ("\n" + record.message).replace("\n", "\n. ")

        # Add a newline so consumers know the message is over.
        return s + "\n"


class MachineFilter(logging.Filter):
    """
    Filter that only allows levels that are consumable by other processes.
    """

    def filter(self, record):
        # We only want to allow records that have our custom level names
        return hasattr(record, "levelName")


class PrettyProgressFormatter(logging.Formatter):
    """
    Formatter that overwrites previous progress lines on ANSI terminals.
    """

    last_record_was_progress = False

    def __init__(self):
        # 'message' will be appended by format()
        # Note that we use our own, custom-created 'levelName' instead of the
        # standard 'levelname'.  This is because the standard 'levelname' can
        # be adjusted by any library anywhere in our stack without us knowing.
        # But we control 'levelName'.
        logging.Formatter.__init__(self, "%(message)s")

    def format(self, record):
        s = logging.Formatter.format(self, record)

        # So we don't overwrite actual log lines
        if self.last_record_was_progress and record.transferProgress:
            # Go up one line, then erase it
            s = "\033[F\033[2K" + s

        self.last_record_was_progress = record.transferProgress

        return s


def add_fd(fd):
    """
    Add stream to which to write machine-readable logging.
    """
    global _logger
    handler = logging.StreamHandler(os.fdopen(fd, "w"))
    handler.setFormatter(MachineFormatter())
    handler.addFilter(MachineFilter())
    _logger.addHandler(handler)


def add_file(filename):
    """
    Add file to which to write machine-readable logging
    """
    global _logger
    handler = logging.FileHandler(filename, encoding="utf8")
    handler.setFormatter(MachineFormatter())
    handler.addFilter(MachineFilter())
    _logger.addHandler(handler)


def setverbosity(verb):
    """
    Set the verbosity level.
    """
    global _logger
    _logger.setLevel(verb)


def getverbosity():
    """
    Get the verbosity level.
    """
    global _logger
    return _logger.getEffectiveLevel()


def setup():
    """
    Initialize logging
    """
    global _logger
    global _log_timestamp
    if _logger:
        return

    # for backwards compatibility
    logging.addLevelName(NOTICE, "NOTICE")

    # OK, now we can start setup
    _logger = logging.getLogger("duplicity")

    # Default verbosity allows notices and above
    setverbosity(NOTICE)

    # stdout and stderr are for different logging levels
    outHandler = logging.StreamHandler(sys.stdout)
    if _log_timestamp:
        outHandler.setFormatter(DetailFormatter())
    else:
        outHandler.setFormatter(PrettyProgressFormatter())
    outHandler.addFilter(OutFilter())
    _logger.addHandler(outHandler)

    errHandler = logging.StreamHandler(sys.stderr)
    if _log_timestamp:
        errHandler.setFormatter(DetailFormatter())
    else:
        errHandler.setFormatter(PrettyProgressFormatter())
    errHandler.addFilter(ErrFilter())
    _logger.addHandler(errHandler)


def shutdown():
    """
    Cleanup and flush loggers
    """
    logging.shutdown()
