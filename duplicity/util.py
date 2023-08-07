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

"""
Miscellaneous utilities.
"""

import atexit
import csv
import errno
import json
import os
import sys
import traceback
from io import StringIO

import duplicity.config as config
import duplicity.log as log
from duplicity import tarfile


def exception_traceback(limit=50):
    """
    @return A string representation in typical Python format of the
            currently active/raised exception.
    """
    type, value, tb = sys.exc_info()  # pylint: disable=redefined-builtin

    lines = traceback.format_tb(tb, limit)
    lines.extend(traceback.format_exception_only(type, value))

    msg = "Traceback (innermost last):\n"
    msg = msg + "%-20s %s" % (str.join("", lines[:-1]), lines[-1])

    return msg


def escape(string):
    """Convert a (bytes) filename to a format suitable for logging (quoted utf8)"""
    string = os.fsdecode(string).encode('unicode-escape', 'replace')
    return "'%s'" % string.decode('utf8', 'replace').replace("'", '\\x27')


def uindex(index):
    """Convert an index (a tuple of path parts) to unicode for printing"""
    if index:
        return os.path.join(*list(map(os.fsdecode, index)))
    else:
        return '.'


def uexc(e):
    """Returns the exception message in Unicode"""
    # Exceptions in duplicity often have path names in them, which if they are
    # non-ascii will cause a UnicodeDecodeError when implicitly decoding to
    # unicode.  So we decode manually, using the filesystem encoding.
    # 99.99% of the time, this will be a fine encoding to use.
    if e and e.args:
        # Find arg that is a string
        for m in e.args:
            if isinstance(m, str):
                # Already unicode
                return m
            elif isinstance(m, bytes):
                # Encoded, likely in filesystem encoding
                return os.fsdecode(m)
        # If the function did not return yet, we did not
        # succeed in finding a string; return the whole message.
        return str(e)
    else:
        return ''


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
    except Exception as e:
        if config.ignore_errors:
            log.Warn(_("IGNORED_ERROR: Warning: ignoring error as requested: %s: %s")
                     % (e.__class__.__name__, uexc(e)))
            return None
        else:
            raise


class BlackHoleList(list):

    def append(self, x):
        pass


class FakeTarFile(object):
    debug = 0

    def __iter__(self):
        return iter([])

    def close(self):
        pass


def make_tarfile(mode, fp):
    # We often use 'empty' tarfiles for signatures that haven't been filled out
    # yet.  So we want to ignore ReadError exceptions, which are used to signal
    # this.
    try:
        tf = tarfile.TarFile("arbitrary", mode, fp)
        # Now we cause TarFile to not cache TarInfo objects.  It would end up
        # consuming a lot of memory over the lifetime of our long-lasting
        # signature files otherwise.
        tf.members = BlackHoleList()
        return tf
    except tarfile.ReadError:
        return FakeTarFile()


def get_tarinfo_name(ti):
    # Python versions before 2.6 ensure that directories end with /, but 2.6
    # and later ensure they they *don't* have /.  ::shrug::  Internally, we
    # continue to use pre-2.6 method.
    if ti.isdir() and not ti.name.endswith(r"/"):
        return f"{ti.name}/"
    else:
        return ti.name


def ignore_missing(fn, filename):
    """
    Execute fn on filename.  Ignore ENOENT errors, otherwise raise exception.

    @param fn: callable
    @param filename: string
    """
    try:
        fn(filename)
    except OSError as ex:
        if ex.errno == errno.ENOENT:
            pass
        else:
            raise


@atexit.register
def release_lockfile():
    if config.lockfile and os.path.exists(config.lockpath):
        log.Debug(_("Releasing lockfile %s") % os.fsdecode(config.lockpath))
        try:
            config.lockfile.release()
            os.remove(config.lockpath)
            config.lockfile = None
            config.lockpath = ""
        except Exception as e:
            log.Error(f"Could not release lockfile: {str(e)}")
            pass


def copyfileobj(infp, outfp, byte_count=-1):
    """Copy byte_count bytes from infp to outfp, or all if byte_count < 0

    Returns the number of bytes actually written (may be less than
    byte_count if find eof.  Does not close either fileobj.

    """
    blocksize = 64 * 1024
    bytes_written = 0
    if byte_count < 0:
        while True:
            buf = infp.read(blocksize)
            if not buf:
                break
            bytes_written += len(buf)
            outfp.write(buf)
    else:
        while bytes_written + blocksize <= byte_count:
            buf = infp.read(blocksize)
            if not buf:
                break
            bytes_written += len(buf)
            outfp.write(buf)
        buf = infp.read(byte_count - bytes_written)
        bytes_written += len(buf)
        outfp.write(buf)
    return bytes_written


def which(program):
    """
    Return absolute path for program name.
    Returns None if program not found.
    """

    def is_exe(fpath):
        return os.path.isfile(fpath) and os.path.isabs(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.getenv("PATH").split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.abspath(os.path.join(path, program))
            if is_exe(exe_file):
                return exe_file

    return None


def start_debugger():
    if '--pydevd' in sys.argv or os.environ.get("PYDEVD", None):
        try:
            import pydevd_pycharm  # pylint: disable=import-error
        except ImportError:
            log.FatalError("Module pydevd_pycharm must be available for debugging.\n"
                           "Remove '--pydevd' from command line and unset 'PYDEVD'\n"
                           "from the environment to avoid starting the debugger.")

        # NOTE: this needs to be customized for your system
        debug_host = 'dione.local'
        debug_port = 6700

        # get previous pid:port if any
        # return if pid the same as ours
        prev_port = None
        debug_running = os.environ.get("DEBUG_RUNNING", False)
        if debug_running:
            prev_pid, prev_port = list(map(int, debug_running.split(":")))
            if prev_pid == os.getpid():
                return

        # new pid, next port, start a new debugger
        if prev_port:
            debug_port = int(prev_port) + 1

        # ignition
        try:
            pydevd_pycharm.settrace(debug_host,
                                    port=debug_port,
                                    suspend=False,
                                    stdoutToServer=True,
                                    stderrToServer=True,
                                    # patch_multiprocessing=True,
                                    )
            log.Info(f"Connection {debug_host}:{debug_port} accepted for debug.")
        except ConnectionRefusedError as e:
            log.Info(f"Connection {debug_host}:{debug_port} refused for debug: {str(e)}")

        # in a dev environment the path is screwed so fix it.
        base = sys.path.pop(0)
        base = base.split(os.path.sep)[:-1]
        base = os.path.sep.join(base)
        sys.path.insert(0, base)

        # save last debug pid:port used
        os.environ['DEBUG_RUNNING'] = f"{os.getpid()}:{debug_port}"


def merge_dicts(*dict_args):
    """
    Given any number of dictionaries, shallow copy and merge into a new dict,
    precedence goes to key-value pairs in latter dictionaries.
    """
    result = {}
    for dictionary in dict_args:
        result.update(dictionary)
    return result


def csv_args_to_dict(arg):
    """
    Given the string arg in single line csv format, split into pairs (key, val)
    and produce a dictionary from those key:val pairs.
    """
    mydict = {}
    with StringIO(arg) as infile:
        rows = csv.reader(infile)
        for row in rows:
            for i in range(0, len(row), 2):
                mydict[row[i]] = row[i + 1]
    return mydict


# TODO: just use util.fsdecode().casefold() directly when python27 is gone
def casefold_compat(s):
    """
    Compatability function for casefolding which provides an acceptable for
    older pythons. Can likely be removed once python2 support is no longer o
    any interest.
    """
    if sys.version_info.major >= 3 and sys.version_info.minor >= 3:
        return s.casefold()
    else:
        return s.lower()
