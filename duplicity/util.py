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

u"""
Miscellaneous utilities.
"""

from builtins import str
from builtins import map
from builtins import object
import errno
import os
import string
import sys
import traceback
import atexit

from duplicity import tarfile
import duplicity.globals as globals
import duplicity.log as log

try:
    # For paths, just use path.name/uname rather than converting with these
    from os import fsencode, fsdecode
except ImportError:
    # Most likely Python version < 3.2, so define our own fsencode/fsdecode.
    # These are functions that encode/decode unicode paths to filesystem encoding,
    # but the cleverness is that they handle non-unicode characters on Linux
    # There is a *partial* backport to Python2 available here:
    # https://github.com/pjdelport/backports.os/blob/master/src/backports/os.py
    # but if it cannot be trusted for full-circle translation, then we may as well
    # just read and store the bytes version of the path as path.name before
    # creating the unicode version (for path matching etc) and ensure that in
    # real-world usage (as opposed to testing) we create the path objects from a
    # bytes string.
    # ToDo: Revisit this once we drop Python 2 support/the backport is complete

    def fsencode(unicode_filename):
        u"""Convert a unicode filename to a filename encoded in the system encoding"""
        # For paths, just use path.name rather than converting with this
        # If we are not doing any cleverness with non-unicode filename bytes,
        # encoding to system encoding is good enough
        return unicode_filename.encode(sys.getfilesystemencoding(), u"replace")

    def fsdecode(bytes_filename):
        u"""Convert a filename encoded in the system encoding to unicode"""
        # For paths, just use path.uc_name rather than converting with this
        # If we are not doing any cleverness with non-unicode filename bytes,
        # decoding using system encoding is good enough. Use "ignore" as
        # Linux paths can contain non-Unicode characters
        return bytes_filename.decode(globals.fsencoding, u"replace")


def exception_traceback(limit=50):
    u"""
    @return A string representation in typical Python format of the
            currently active/raised exception.
    """
    type, value, tb = sys.exc_info()

    lines = traceback.format_tb(tb, limit)
    lines.extend(traceback.format_exception_only(type, value))

    msg = u"Traceback (innermost last):\n"
    if sys.version_info.major >= 3:
        msg = msg + u"%-20s %s" % (str.join(u"", lines[:-1]), lines[-1])
    else:
        msg = msg + u"%-20s %s" % (string.join(lines[:-1], u""), lines[-1])

    if sys.version_info.major < 3:
        return msg.decode(u'unicode-escape', u'replace')
    return msg


def escape(string):
    u"Convert a (bytes) filename to a format suitable for logging (quoted utf8)"
    string = fsdecode(string).encode(u'unicode-escape', u'replace')
    return u"'%s'" % string.decode(u'utf8', u'replace')


def uindex(index):
    u"Convert an index (a tuple of path parts) to unicode for printing"
    if index:
        return os.path.join(*list(map(fsdecode, index)))
    else:
        return u'.'


def uexc(e):
    # Exceptions in duplicity often have path names in them, which if they are
    # non-ascii will cause a UnicodeDecodeError when implicitly decoding to
    # unicode.  So we decode manually, using the filesystem encoding.
    # 99.99% of the time, this will be a fine encoding to use.
    m = e.message
    if isinstance(m, unicode):
        m = m.encode('utf-8')
    return fsdecode(m)


def maybe_ignore_errors(fn):
    u"""
    Execute fn. If the global configuration setting ignore_errors is
    set to True, catch errors and log them but do continue (and return
    None).

    @param fn: A callable.
    @return Whatever fn returns when called, or None if it failed and ignore_errors is true.
    """
    try:
        return fn()
    except Exception as e:
        if globals.ignore_errors:
            log.Warn(_(u"IGNORED_ERROR: Warning: ignoring error as requested: %s: %s")
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
        tf = tarfile.TarFile(u"arbitrary", mode, fp)
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
        return ti.name + r"/"
    else:
        return ti.name


def ignore_missing(fn, filename):
    u"""
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
    if globals.lockfile:
        log.Debug(_(u"Releasing lockfile %s") % globals.lockpath)
        try:
            globals.lockfile.release()
        except Exception:
            pass


def copyfileobj(infp, outfp, byte_count=-1):
    u"""Copy byte_count bytes from infp to outfp, or all if byte_count < 0

    Returns the number of bytes actually written (may be less than
    byte_count if find eof.  Does not close either fileobj.

    """
    blocksize = 64 * 1024
    bytes_written = 0
    if byte_count < 0:
        while 1:
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
    u"""
    Return absolute path for program name.
    Returns None if program not found.
    """

    def is_exe(fpath):
        return os.path.isfile(fpath) and os.path.isabs(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)  # @UnusedVariable
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.getenv(u"PATH").split(os.pathsep):
            path = path.strip(u'"')
            exe_file = os.path.abspath(os.path.join(path, program))
            if is_exe(exe_file):
                return exe_file

    return None
