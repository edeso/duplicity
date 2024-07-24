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
Utility functions for logging messages.
"""

import datetime
import sys

from duplicity.log import (
    Log,
    INFO,
    InfoCode,
    NOTICE,
    ErrorCode,
    ERROR,
    shutdown,
)


def PrintCollectionStatus(col_stats, force_print=False):
    """
    Prints a collection status to the log.
    """
    Log(
        str(col_stats),
        8,
        InfoCode.collection_status,
        "\n" + "\n".join(col_stats.to_log_info()),
        force_print,
    )


def PrintCollectionFileChangedStatus(col_stats, filepath, force_print=False):
    """
    Prints a collection status to the log.
    """
    Log(
        str(col_stats.get_file_changed_record(filepath)),
        8,
        InfoCode.collection_status,
        None,
        force_print,
    )


def PrintCollectionChangesInSet(col_stats, set_index, force_print=False):
    """
    Prints changes in the specified set to the log.
    """
    Log(
        str(col_stats.get_all_file_changed_records(set_index)),
        8,
        InfoCode.collection_status,
        None,
        force_print,
    )


def Progress(s, current, total=None):
    """
    Shortcut used for progress messages (verbosity INFO).
    """
    if total:
        controlLine = f"{int(current)} {int(total)}"
    else:
        controlLine = f"{int(current)}"
    Log(s, INFO, InfoCode.progress, controlLine)


def TransferProgress(progress, eta, changed_bytes, elapsed, speed, stalled):
    """
    Shortcut used for upload progress messages (verbosity NOTICE).
    """

    def _ElapsedSecs2Str(secs):
        tdelta = datetime.timedelta(seconds=secs)
        hours, rem = divmod(tdelta.seconds, 3600)
        minutes, seconds = divmod(rem, 60)
        fmt = ""
        if tdelta.days > 0:
            fmt = f"{int(tdelta.days)}d,"
        fmt = f"{fmt}{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
        return fmt

    def _RemainingSecs2Str(secs):
        tdelta = datetime.timedelta(seconds=secs)
        hours, rem = divmod(tdelta.seconds, 3600)
        minutes, seconds = divmod(rem, 60)
        fmt = ""
        if tdelta.days > 0:
            fmt = f"{int(tdelta.days)}d"
            if hours > 0:
                fmt = f"{fmt} {int(hours)}h"
            if minutes > 0:
                fmt = f"{fmt} {int(minutes)}min"
        elif hours > 0:
            fmt = f"{int(hours)}h"
            if minutes > 0:
                fmt = f"{fmt} {int(minutes)}min"
        elif minutes > 5:
            fmt = f"{int(minutes)}min"
        elif minutes > 0:
            fmt = f"{int(minutes)}min"
            if seconds >= 30:
                fmt = f"{fmt} 30sec"
        elif seconds > 45:
            fmt = "< 1min"
        elif seconds > 30:
            fmt = "< 45sec"
        elif seconds > 15:
            fmt = "< 30sec"
        else:
            fmt = f"{int(seconds)}sec"
        return fmt

    dots = int(0.4 * progress)  # int(40.0 * progress / 100.0) -- for 40 chars
    data_amount = float(changed_bytes) / 1024.0
    data_scale = "KB"
    if data_amount > 1000.0:
        data_amount /= 1024.0
        data_scale = "MB"
    if data_amount > 1000.0:
        data_amount /= 1024.0
        data_scale = "GB"
    if stalled:
        eta_str = "Stalled!"
        speed_amount = 0
        speed_scale = "B"
    else:
        eta_str = _RemainingSecs2Str(eta)
        speed_amount = float(speed) / 1024.0
        speed_scale = "KB"
        if speed_amount > 1000.0:
            speed_amount /= 1024.0
            speed_scale = "MB"
        if speed_amount > 1000.0:
            speed_amount /= 1024.0
            speed_scale = "GB"
    s = (
        f"{data_amount:.1f}{data_scale} {_ElapsedSecs2Str(elapsed)} [{speed_amount:.1f}{speed_scale}/s] "
        f"[{'=' * dots}>{' ' * (40 - dots)}] {int(progress)}% ETA {eta_str}"
    )

    controlLine = f"{int(changed_bytes)} {int(elapsed)} {int(progress)} {int(eta)} {int(speed)} {int(stalled)}"
    Log(s, NOTICE, InfoCode.upload_progress, controlLine, transfer_progress=True)


def FatalError(s, code=ErrorCode.generic, extra=None):
    """
    Write fatal error message and exit.
    """
    Log(s, ERROR, code, extra)
    shutdown()
    sys.exit(code)
