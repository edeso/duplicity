# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
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

"""
Miscellaneous utilities.
"""

import errno
import sys
import string
import traceback
import tarfile

import duplicity.globals as globals
import duplicity.log as log

def exception_traceback(limit = 50):
    """
    @return A string representation in typical Python format of the
            currently active/raised exception.
    """
    type, value, tb = sys.exc_info()

    lines = traceback.format_tb(tb, limit)
    lines.extend(traceback.format_exception_only(type, value))

    str = "Traceback (innermost last):\n"
    str = str + "%-20s %s" % (string.join(lines[:-1], ""),
                                lines[-1])

    return str

def escape(string):
    return "'%s'" % string.encode("string-escape")

def maybe_ignore_errors(fn):
    """
    Execute fn. If the global configuration setting ignore_errors is
    set to True, catch errors and log them but do continue (and return
    None).

    @param fn: A callable.
    @return Whatever fn returns when called, or None if it failed and ignore_errors is true.
    """
    try:
        return fn()
    except Exception, e:
        if globals.ignore_errors:
            log.Warn(_("IGNORED_ERROR: Warning: ignoring error as requested: %s: %s")
                     % (e.__class__.__name__, str(e)))
            return None
        else:
            raise

def make_tarfile(mode, fp):
    # We often use 'empty' tarfiles for signatures that haven't been filled out
    # yet.  So we want to 'ignore_zeros' which means, "don't raise errors when
    # tarfile is empty".  This is a simple object flag, but in python2.6 and
    # beyond, a block is read in the constructor too, so it needs to be passed
    # in there.
    if sys.version_info < (2, 6):
        tf = tarfile.TarFile("arbitrary", mode, fp)
        tf.ignore_zeros = True
        return tf
    else:
        return tarfile.TarFile("arbitrary", mode, fp, ignore_zeros=True)

def ignore_missing(fn, filename):
    """
    Execute fn on filename.  Ignore ENOENT errors, otherwise raise exception.

    @param fn: callable
    @param filename: string
    """
    try:
        fn(filename)
    except Exception:
        type, value, tb = sys.exc_info() #@UnusedVariable
        if isinstance(type, OSError) and value[0] == errno.ENOENT:
            pass
        raise

