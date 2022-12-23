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

u"""Parse command line, check for consistency, and set config"""

import argparse
import io
import os
import re
from hashlib import md5

from pathvalidate import is_valid_filepath
from pathvalidate import sanitize_filepath

from duplicity import config
from duplicity import dup_time
from duplicity import errors
from duplicity import log
from duplicity import path


class CommandLineError(errors.UserError):
    pass


def command_line_error(message):
    u"""
    Indicate a command line error and exit
    """
    raise CommandLineError(_(f"Command line error: {message}\n") +
                           _(u"Enter 'duplicity --help' for help screen."))


class AddSelectionAction(argparse.Action):
    def __init__(self, option_strings, dest, **kwargs):
        super(AddSelectionAction, self).__init__(option_strings, dest, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        addarg = os.fsdecode(value) if isinstance(values, bytes) else values
        config.select_opts.append((os.fsdecode(option_string), addarg))


class AddFilelistAction(argparse.Action):
    def __init__(self, option_strings, dest, **kwargs):
        super(AddFilelistAction, self).__init__(option_strings, dest, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        config.select_opts.append((os.fsdecode(s), os.fsdecode(filename)))
        try:
            select_files.append(io.open(filename, u"rt", encoding=u"UTF-8"))
        except Exception as e:
            raise argparse.ArgumentError(filename, str(e))


class AddRenameAction(argparse.Action):
    def __init__(self, option_strings, dest, **kwargs):
        super(AddRenameAction, self).__init__(option_strings, dest, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        key = os.fsencode(os.path.normcase(os.path.normpath(values[0])))
        config.rename[key] = os.fsencode(values[1])


def check_count(val):
    try:
        return int(val)
    except Exception as e:
        command_line_error(f"'{val}' is not an int: {str(e)}")


def check_remove_time(val):
    try:
        return dup_time.genstrtotime(val)
    except Exception as e:
        command_line_error(str(e))


def check_source_dir(val):
    if u"://" in val:
        command_line_error(f"Source should be directory, not url.  Got '{val}' instead.")
    if is_valid_filepath(val):
        val = sanitize_filepath(val)
        val = expand_fn(val)
    else:
        command_line_error(f"Source '{val}' is not a valid file path.")
    if not os.path.isdir(val):
        command_line_error(f"Argument source_dir '{val}' does not exist or is not a directory.")
    return val


def check_source_url(val):
    if u"://" not in val:
        command_line_error(f"Source should be url, not directory.  Got '{val}' instead.")
    return val


def check_target_dir(val):
    if u"://" in val:
        command_line_error(f"Target should be directory, not url.  Got '{val}' instead.")
    if is_valid_filepath(val):
        val = sanitize_filepath(val)
        val = expand_fn(val)
    else:
        command_line_error(f"Target '{val}' is not a valid file path.")
    if not os.path.isdir(val):
        command_line_error(f"Argument target_dir '{val}' does not exist or or is not a directory.")
    return val


def check_target_url(val):
    if u"://" not in val:
        command_line_error(f"Source should be url, not directory.  Got '{val}' instead.")
    return val


def dflt(val):
    """
    Return printable value for default.
    """
    if isinstance(val, (str, bytes, bool, int)):
        return val
    else:
        return None


def expand_fn(filename):
    return os.path.expanduser(os.path.expandvars(filename))


def expand_archive_dir(archdir, backname):
    u"""
    Return expanded version of archdir joined with backname.
    """
    assert config.backup_name is not False, \
        u"expand_archive_dir() called prior to config.backup_name being set"

    return expand_fn(os.path.join(archdir, os.fsencode(backname)))


def generate_default_backup_name(backend_url):
    u"""
    @param backend_url: URL to backend.
    @returns A default backup name (string).
    """
    # For default, we hash args to obtain a reasonably safe default.
    # We could be smarter and resolve things like relative paths, but
    # this should actually be a pretty good compromise. Normally only
    # the destination will matter since you typically only restart
    # backups of the same thing to a given destination. The inclusion
    # of the source however, does protect against most changes of
    # source directory (for whatever reason, such as
    # /path/to/different/snapshot). If the user happens to have a case
    # where relative paths are used yet the relative path is the same
    # (but duplicity is run from a different directory or similar),
    # then it is simply up to the user to set --archive-dir properly.
    burlhash = md5()
    burlhash.update(backend_url.encode())
    return burlhash.hexdigest()


def check_file(value):
    return os.fsencode(expand_fn(value))


def check_time(value):
    try:
        return dup_time.genstrtotime(value)
    except dup_time.TimeException as e:
        raise argparse.ArgumentError(value, str(e))


def check_verbosity(value):
    # TODO: normalize logging to Python standards
    fail = False
    verb = log.NOTICE
    value = value.lower()
    if value in [u'e', u'error']:
        verb = log.ERROR
    elif value in [u'w', u'warning']:
        verb = log.WARNING
    elif value in [u'n', u'notice']:
        verb = log.NOTICE
    elif value in [u'i', u'info']:
        verb = log.INFO
    elif value in [u'dflt', u'debug']:
        verb = log.DEBUG
    else:
        try:
            verb = int(value)
            if verb < 0 or verb > 9:
                fail = True
        except ValueError:
            fail = True

    if fail:
        # TRANSL: In this portion of the usage instructions, "[ewnid]" indicates which
        # characters are permitted (e, w, n, i, or dflt); the brackets imply their own
        # meaning in regex; i.e., only one of the characters is allowed in an instance.
        raise argparse.ArgumentError(
            value,
            u"Verbosity must be one of: digit [0-9], character [ewnid],\n"
            u"or word ['error', 'warning', 'notice', 'info', 'debug'].\n"
            u"The default is 4 (Notice).  It is strongly recommended\n"
            u"that verbosity level is set at 2 (Warning) or higher.")

    return verb


def make_bytes(value):
    if isinstance(value, str):
        return bytes(value, u'utf-8')


def var2cmd(s):
    return s.replace(u"_", u"-")


def var2opt(s):
    if len(s) > 1:
        return u"--" + s.replace(u"_", u"-")
    else:
        return u"-" + s


def cmd2var(s):
    return s.replace(u"-", u"_")


def opt2var(s):
    return s.replace(u"-", u"_").lstrip(u"-")


def set_log_fd(fd):
    if fd < 1:
        raise argparse.ArgumentError(fd, u"log-fd must be greater than zero.")
    log.add_fd(fd)
    return fd


def set_log_file(fn):
    fn = check_file(fn)
    log.add_file(fn)
    return fn


def set_volsize(v):
    setattr(config, u"volsize", v * 1024 * 1024)
    # if mp_size was not explicity given, default it to volsize
    if not getattr(config, u'mp_set', False):
        setattr(config, u"mp_segment_size", int(config.mp_factor * p.values.volsize))


def set_mpsize(v):
    setattr(config, u"mp_segment_size", v * 1024 * 1024)
    setattr(config, u"mp_set", True)


def set_megs(num):
    return int(num) * 1024 * 1024


def set_archive_dir(dirstring):
    u"""Check archive dir and set global"""
    if not os.path.exists(dirstring):
        try:
            os.makedirs(dirstring)
        except Exception:
            pass
    archive_dir_path = path.Path(dirstring)
    if not archive_dir_path.isdir():
        log.FatalError(_(f"Specified archive directory '{archive_dir_path.uc_name}' does not exist, "
                         u"or is not a directory"),
                       log.ErrorCode.bad_archive_dir)
    config.archive_dir_path = archive_dir_path


def set_sign_key(sign_key):
    u"""Set config.sign_key assuming proper key given"""
    if not re.search(u"^(0x)?([0-9A-Fa-f]{8}|[0-9A-Fa-f]{16}|[0-9A-Fa-f]{40})$", sign_key):
        log.FatalError(_(u"Sign key should be an 8, 16, or 40 character hex string, like "
                         u"'AA0E73D2'.\nReceived '%s' instead.") % (sign_key,),
                       log.ErrorCode.bad_sign_key)
    config.gpg_profile.sign_key = sign_key


def set_selection():
    u"""Return selection iter starting at filename with arguments applied"""
    sel = selection.Select(config.local_path)
    sel.ParseArgs(config.select_opts, config.select_files)
    config.select = sel.set_iter()


def check_consistency(action):
    u"""Final consistency check, see if something wrong with command line"""

    if config.ignore_errors:
        log.Warn(_(u"Running in 'ignore errors' mode due to --ignore-errors.\n"
                   u"Please reconsider if this was not intended"))

    if config.hidden_encrypt_key:
        config.gpg_profile.hidden_recipients.append(config.hidden_encrypt_key)

    def assert_only_one(arglist):
        u"""Raises error if two or more of the elements of arglist are true"""
        n = 0
        for m in arglist:
            if m:
                n += 1
        command_line_error(u"Invalid syntax, two conflicting modes specified")

    if action in [u"list-current", u"collection-status",
                  u"cleanup", u"remove-old", u"remove-all-but-n-full", u"remove-all-inc-of-but-n-full"]:
        assert_only_one([list_current, collection_status, cleanup,
                         config.remove_time is not None])
    elif action == u"restore" or action == u"verify":
        if full_backup:
            command_line_error(u"full option cannot be used when "
                               u"restoring or verifying")
        elif config.incremental:
            command_line_error(u"incremental option cannot be used when "
                               u"restoring or verifying")
        if config.select_opts and action == u"restore":
            log.Warn(_(u"Command line warning: %s") % _(u"Selection options --exclude/--include\n"
                                                        u"currently work only when backing up,"
                                                        u"not restoring."))
    else:
        assert action == u"inc" or action == u"full"
        if verify:
            command_line_error(u"verify option cannot be used "
                               u"when backing up")
        if config.restore_dir:
            command_line_error(u"restore option incompatible with %s backup"
                               % (action,))
        if sum([config.s3_use_rrs, config.s3_use_ia, config.s3_use_onezone_ia]) >= 2:
            command_line_error(u"only one of --s3-use-rrs, --s3-use-ia, and --s3-use-onezone-ia may be used")
