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

import errno

from duplicity import librsync
from duplicity import log

tmp_file_index = 1


def check_common_error(error_handler, function, args=()):
    """Apply function to args, if error, run error_handler on exception

    This only catches certain exceptions which seem innocent
    enough.

    """
    from duplicity import path  # TODO: avoid circ. dep. issue

    try:
        return function(*args)
    # except (EnvironmentError, SkipFileException, DSRPPermError,
    #        RPathException, Rdiff.RdiffException,
    #        librsync.librsyncError, C.UnknownFileTypeError), exc:
    #    TracebackArchive.add()
    except (
        IOError,
        EnvironmentError,
        librsync.librsyncError,
        path.PathException,
    ) as exc:
        if (
            not isinstance(exc, EnvironmentError)
            or hasattr(exc, "errno")
            and errno.errorcode.get(exc.errno)
            in [
                "EPERM",
                "ENOENT",
                "EACCES",
                "EBUSY",
                "EEXIST",
                "ENOTDIR",
                "ENAMETOOLONG",
                "EINTR",
                "ENOTEMPTY",
                "EIO",
                "ETXTBSY",
                "ESRCH",
                "EINVAL",
                "EOPNOTSUPP",
            ]
        ):
            # Log.exception()
            if error_handler:
                return error_handler(exc, *args)
        else:
            # Log.exception(1, 2)
            raise


def listpath(path):
    """Like path.listdir() but return [] if error, and sort results"""

    def error_handler(exc):  # pylint: disable=unused-argument
        log.Warn(_("Error listing directory %s") % path.uc_name)
        return []

    dir_listing = sorted(check_common_error(error_handler, path.listdir))
    return dir_listing
